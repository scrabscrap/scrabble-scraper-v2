import React, { Component } from 'react';

import './bootstrap.min.css';
import './App.css'

import Display from './display/Display'

const WS_URL = `${(window.location.protocol === 'https:') ? 'wss:' : 'ws:'}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}/ws_status`

// websocket impl see: https://morioh.com/p/606840219b21
class App extends Component {

  constructor(props) {
    super(props);
    this.state = {
      op: 'START',
      tournament: 'SCRABBLE SCRAPER',
      layout: null,
      clock1: 1800, clock2: 1800,
      time: Date(),
      move: null,
      name1: 'Name1', name2: 'Name2',
      score1: 0, score2: 0,
      time1: 1800, time2: 1800,
      onmove: '',
      bag: null,
      board: null,
      moves: null,
      image: null,
      settings: {
        obs: this.getCookie('OBS', false),
        obsbank: this.getCookie('OBSBANK', false),
        websocket: true,
        header_text: 'SCRABBLE SCRAPER',
        theme2020: this.getCookie('THEME2020', false)
      },
      unknown_move: false,
      ws: null,
      highlight_reload: false,
    }
  }

  getCookie = (name, def) => {
    const val = document.cookie.split('; ').filter(row => row.startsWith(name + '=')).map(c => c.split('=')[1])[0]
    if (typeof def === 'boolean') {
      return (val) ? (val === 'true') : def
    } else if (typeof def === 'number') {
      return (val) ? Number(val) : def
    }
    return (val) ? val : def
  }

  setCookie = (name, val) => {
    document.cookie = name + '=' + val + ';SameSite=Lax'
  }

  updateSettings = (val) => {
    // this function allows child components to update the settings
    const { settings } = this.state
    if (settings !== val) {
      console.log('update settings')
      console.log(val)
      this.setState({ settings: val })
      this.setCookie('OBS', val.obs)
      this.setCookie('OBSBANK', val.obsbank)
      this.setCookie('THEME2020', val.theme2020)
    }
  }

  componentDidMount() {
    if (navigator.userAgent.includes("OBS")) {
        const {settings} = this.state;
        settings.obs = true
      settings.obsbank = this.getCookie('OBSBANK', false) 
      this.setState({ settings: settings })
      this.setCookie('OBS', settings.obs)
      this.setCookie('OBSBANK', settings.obsbank)
      this.setCookie('THEME2020', settings.theme2020)
    }
    this.connect();
    this.fileconnect();
  }

  // componentDidUpdate(prevProps) { }

  componentWillUnmount() {
    if (this.intervalID) {                       // clear running ws timeout
      clearTimeout(this.intervalID);
      this.intervalID = null
    }
    if (this.ws_intervalID) {                    // clear running fileconnect timeout
      clearTimeout(this.ws_intervalID);
      this.ws_intervalID = null
    }
    if (this.state.ws) {                         // close websocket
      this.state.ws.close()
      this.setState({ ws: null })
    }
  }

  // ## websocket
  ws_firsttry = (new Date()).getTime()  // last websocket open 
  ws_intervalID;                        // var for timeout
  connect = () => {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {  // websocket onopen event listener
      console.log('ws: connected ' + WS_URL);
      this.setState({ ws: ws });
      clearTimeout(this.ws_intervalID);          // clear Interval on on open of websocket connection
      this.ws_intervalID = null;
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      console.debug('ws: setState (websocket) ' + data?.op)
      this.ws_firsttry = (new Date()).getTime()
      let img_str
      if (data.image != null) {
        if (data.op === 'START') {
          img_str = null
        } else if (data.image.startsWith('b\'')) {
          img_str = 'data:image/png;base64,' + data.image.substring(2, data.image.length - 1)
        } else {
          img_str = 'data:image/png;base64,' + data.image
        }
      } else {
        img_str = this.state.image
      }
      // check for (unknown) move
      let unknown_move = false
      if (data.move) {
        for (const [, value] of Array.from(data.moves.entries())) {
          if (value.includes('(unknown)')) { unknown_move = true }
        }
      }
      if (data.status?.tournament) {
        this.setState( {
          settings: { header_text: data.status.tournament}
        })

      } 
      if (data.status?.layout) {
        this.setState( {
          settings: { theme2020: data.status.layout.includes('2020')}
        })
      }

      this.setState({
        op: data.op, clock1: data.clock1, clock2: data.clock2,
        ...data.status,
        image: img_str,
        unknown_move: unknown_move,
        settings: {
          ...this.state.settings,
          websocket: true,
        }
      })
    }

    ws.onclose = e => {  // websocket onclose event listener
      console.log('ws: Socket is closed. Try to reconnect in 2 seconds. Code=', e.code);
      const { settings } = this.state
      if (settings.websocket) {
        settings.websocket = false
        this.setState({ settings: settings })
      }
      if (((new Date()).getTime() - this.ws_firsttry) < (30 * 1000)) { // 30 sec
        console.log('ws: start timer')
        this.ws_intervalID = setTimeout(this.check, 2000); //retry in 2s
      } else {
        console.log('ws: give up', ((new Date()).getTime() - this.ws_firsttry) / 1000, ' - try fileconnect')
        clearTimeout(this.ws_intervalID);
        this.ws_intervalID = null
        this.fileconnect()
      }
    };

    ws.onerror = err => { // websocket onerror event listener
      console.error('ws: encountered error: ', ws.code, 'Closing socket');
      ws.close();
    };
  };

  check = () => {
    console.log('ws: check')
    const { ws } = this.state;
    if (!ws || ws.readyState === WebSocket.CLOSED) {
      console.log('ws: try to connect')
      this.connect();
    }
  };

  // ## fileconnect
  intervalID;     // var for timeout
  last_timestamp; // timestamp of json data
  nodataCnt = 0;  // reload without data changes
  errorCnt = 0;   // error loading status.json
  fileconnect = () => {

    if (this.intervalID) {                                                 // clear timer
      clearTimeout(this.intervalID);
      this.intervalID = null
    }

    if (this.state.ws && (this.state.ws.readyState === WebSocket.OPEN)) {  // switch to websocket
      clearTimeout(this.intervalID);                                       // no more fileconnect reloads
      this.intervalID = null
      console.log('fileconnect: switch to websocket')
      const { settings } = this.state
      settings.websocket = true
      this.setState({ settings: settings })
      this.connect()
      return
    }

    fetch('web/status.json')
      .then(response => {
        if (response.ok) {
          this.errorCnt = 0
          return (response.headers.get('Content-Type').indexOf('application/json') > -1) ? response.json() : response;
        }
      })
      .then(data => {
        if (data.time !== this.last_timestamp) {
          console.debug('fileconnect: setState (status.json)')
          const op = (data.onmove === data.name1) ? 'S0' : 'S1'
          const img = 'web/image-' + data.move + '.jpg?' + data.time.substring(data.time.indexOf('.') + 1)
          // check for (unknown) move
          let unknown_move = false
          if (data.move) {
            for (const [, value] of Array.from(data.moves.entries())) {
              if (value.includes('(unknown)')) { unknown_move = true }
            }
          }
          if (data?.tournament) {
              this.setState( {
                settings: { header_text: data.tournament}
              })
            }
          if (data?.layout) {
            this.setState( {
              settings: { theme2020: data.layout.includes('2020')}
            })
          } 
    
          this.setState({                        // use image-url, op ist calculated, clock1/2 is not available
            op: op, clock1: data.time1, clock2: data.time2,
            ...data,
            image: img,
            unknown_move: unknown_move,
            settings: {
              ...this.state.settings,
              websocket: false,
            }
          });
          this.last_timestamp = data.time;
          this.nodataCnt = 0;
        } else {
          this.nodataCnt += 1
        }
      }).catch(error => {
        this.errorCnt += 1
        console.error('fileconnect: can not fetch web/status.json (errorCnt:', this.errorCnt, ')')
      });
    if ((this.nodataCnt > 360) || (this.errorCnt > 60)) {            // nodata for 30min or fetch error for 5min
      this.setState({ highlight_reload: true })
      console.warn('fileconnect: timeout - no further reload (nodata:', this.nodataCnt, ', errorCnt:', this.errorCnt, ')')
    } else {
      console.debug('fileconnect: start timer')
      this.intervalID = setTimeout(this.fileconnect.bind(this), 5000); // reload in 5s
    }
  }

  render() {
    return (<Display state={this.state} updateSettings={this.updateSettings} />);
  }
}

export default App;