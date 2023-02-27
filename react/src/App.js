import React, { Component } from 'react';

import './bootstrap.min.css';
import './App.css'

import Display from './display/Display'

// websocket impl see: https://morioh.com/p/606840219b21
class App extends Component {

  constructor(props) {
    super(props);
    const ws_url = `${window.WS_URL}`
    const websocket = (ws_url !== "undefined")
    this.state = {
      op: 'START',
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
        websocket: websocket,
        ws_url: ws_url,
        header_text: this.getCookie('HEADER', 'SCRABBLE-SCRAPER')
      },
      unknown_move: false,
      ws: null,
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
      this.setCookie('HEADER', val.header_text)
      if (val.websocket === true) {
        if (this.intervalID) { clearTimeout(this.intervalID); }
        this.intervalID = null
        this.connect();
      } else {
        if (this.state.ws) { this.state.ws.close() }
        this.fileconnect();
      }
    }
  }

  componentDidMount() {
    if (this.state.settings.websocket === true) {
      this.connect();
    } else {
      if (this.state.ws) { this.state.ws.close() }
      this.fileconnect();
    }
  }

  // componentDidUpdate(prevProps) { }

  componentWillUnmount() {
    if (this.intervalID) {                       // clear running timeoutID
      clearTimeout(this.intervalID);
    }
    this.intervalID = null
    if (this.state.ws) {
      this.state.ws.close()
      this.setState({ ws: null })
    }
  }

  // ## websocket
  timeout = 250;
  connect = () => {
    var ws = new WebSocket(this.state.settings.ws_url);
    let that = this;                             // cache the this
    var connectInterval;

    ws.onopen = () => {                          // websocket onopen event listener
      console.log('connected websocket main component: ' + this.state.settings.ws_url);
      this.setState({ ws: ws });
      that.timeout = 250;                        // reset timer to 250 on open of websocket connection 
      clearTimeout(connectInterval);             // clear Interval on on open of websocket connection
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      console.debug('setState (websocket) ' + data?.op)
      let img_str = data.image
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

    ws.onclose = e => {                          // websocket onclose event listener
      console.log(
        `Socket is closed. Reconnect in ${Math.min(10000 / 1000, (that.timeout + that.timeout) / 1000)} second.`, e.reason);
      that.timeout = that.timeout + that.timeout; //increment retry interval
      if (this.state.settings.websocket) {
        const { settings } = this.state
        settings.websocket = false
        this.setState({ settings: settings })
        connectInterval = setTimeout(this.check, Math.min(10000, that.timeout)); //call check function after timeout
      } else {
        clearTimeout(connectInterval)
        this.fileconnect()
      }
    };

    ws.onerror = err => {                        // websocket onerror event listener
      console.error('Socket encountered error: ', err.message, 'Closing socket');
      ws.close();
    };
  };

  check = () => {
    if (this.state.settings.websocket) {
      const { ws } = this.state;                   //check if websocket instance is closed, if so call `connect` function.
      if (!ws || ws.readyState === WebSocket.CLOSED) this.connect();
    }
  };

  // ## fileconnect
  intervalID;
  last_timestamp;                                // timestamp of json data
  fileconnect = () => {
    let errorCnt = 0;
    let nodataCnt = 0;

    fetch('web/status.json')
      .then(response => {
        if (response.ok) {
          this.errorCnt = 0
          return (response.headers.get('Content-Type').indexOf('application/json') > -1) ? response.json() : response;
        }
      })
      .then(data => {
        if (data.time !== this.last_timestamp) {
          console.debug('setState (status.json)')
          const op = (data.onmove === data.name1) ? 'S0' : 'S1'
          const img = 'web/image-' + data.move + '.jpg?' + data.time.substring(data.time.indexOf('.') + 1)
          // check for (unknown) move
          let unknown_move = false
          if (data.move) {
            for (const [, value] of Array.from(data.moves.entries())) {
              if (value.includes('(unknown)')) { unknown_move = true }
            }
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
          this.nodataCnt = this.nodataCnt + 1
        }
      }).catch(error => {
        console.error('can not fetch web/status.json')
        errorCnt = errorCnt + 1
      });
    if (this.intervalID) {                       // clear timer
      clearTimeout(this.intervalID);
      this.intervalID = null
    }
    if ((nodataCnt < 360) && (errorCnt < 60)) {  // nodata for 30min or fetch error for 5min
      console.debug('start timer')
      if (this.state.settings.websocket === true) {                  // switch to websocket
        clearTimeout(this.intervalID);           // no more fileconnect reloads
        console.log('switch to websocket')
        const { settings } = this.state
        settings.websocket = true
        this.setState({ image: null, settings: settings })
        this.connect()
      } else {
        this.intervalID = setTimeout(this.fileconnect.bind(this), 5000); // reload in 5s
      }
    } else {
      console.warn('fileconnect: timeout - no further reload') //TODO: color reload-button
    }
  }

  render() {
    return (<Display state={this.state} updateSettings={this.updateSettings} />);
  }
}

export default App;