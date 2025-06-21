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
      commit: null,
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
      const { settings } = this.state;
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

  handleWebSocketOpen = (ws) => {
    console.log('ws: connected ' + WS_URL);
    this.setState({ ws });
    clearTimeout(this.ws_intervalID);
    this.ws_intervalID = null;
  };

  parseImage = (data) => {
    if (data.image == null) return this.state.image;
    if (data.op === 'START') return null;
    if (data.image.startsWith("b'")) {
      return 'data:image/png;base64,' + data.image.substring(2, data.image.length - 1);
    }
    return 'data:image/png;base64,' + data.image;
  };

  hasUnknownMove = (data) => {
    if (!data.move) return false;
    for (const [, value] of Array.from(data.moves.entries())) {
      if (value.includes('(unknown)')) return true;
    }
    return false;
  };

  handleWebSocketMessage = (msg) => {
    const data = JSON.parse(msg.data);
    console.debug('ws: setState (websocket) ' + data?.op);
    this.ws_firsttry = (new Date()).getTime();

    const img_str = this.parseImage(data);
    const unknown_move = this.hasUnknownMove(data);

    if (data.status?.layout) {
      this.setState({
        settings: { theme2020: data.status.layout.includes('2020') }
      });
    }

    this.setState({
      op: data.op,
      clock1: data.clock1,
      clock2: data.clock2,
      ...data.status,
      image: img_str,
      unknown_move,
      settings: {
        ...this.state.settings,
        websocket: true,
      }
    });
  };

  handleWebSocketClose = (e) => {
    console.log('ws: Socket is closed. Try to reconnect in 2 seconds. Code=', e.code);
    const { settings } = this.state;
    if (settings.websocket) {
      settings.websocket = false;
      this.setState({ settings });
    }
    if (((new Date()).getTime() - this.ws_firsttry) < (30 * 1000)) {
      console.log('ws: start timer');
      this.ws_intervalID = setTimeout(this.check, 2000);
    } else {
      console.log('ws: give up', ((new Date()).getTime() - this.ws_firsttry) / 1000, ' - try fileconnect');
      clearTimeout(this.ws_intervalID);
      this.ws_intervalID = null;
      this.fileconnect();
    }
  };

  handleWebSocketError = (ws) => {
    console.error('ws: encountered error: ', ws.code, 'Closing socket');
    ws.close();
  };

  connect = () => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => this.handleWebSocketOpen(ws);
    ws.onmessage = this.handleWebSocketMessage;
    ws.onclose = this.handleWebSocketClose;
    ws.onerror = () => this.handleWebSocketError(ws);
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

  parseFileConnectImage = (data) => {
    return 'web/image-' + data.move + '.jpg?' + data.time.substring(data.time.indexOf('.') + 1);
  };

  handleFileConnectData = (data) => {
    const op = (data.onmove === data.name1) ? 'S0' : 'S1';
    const img = this.parseFileConnectImage(data);
    const unknown_move = this.hasUnknownMove(data);

    if (data?.layout) {
      this.setState({
        settings: { theme2020: data.layout.includes('2020') }
      });
    }

    this.setState({
      op,
      clock1: data.time1,
      clock2: data.time2,
      ...data,
      image: img,
      unknown_move,
      settings: {
        ...this.state.settings,
        websocket: false,
      }
    });
    this.last_timestamp = data.time;
    this.nodataCnt = 0;
  };

  fileconnect = () => {
    if (this.intervalID) {
      clearTimeout(this.intervalID);
      this.intervalID = null;
    }

    if (this.state.ws && (this.state.ws.readyState === WebSocket.OPEN)) {
      clearTimeout(this.intervalID);
      this.intervalID = null;
      console.log('fileconnect: switch to websocket');
      const { settings } = this.state;
      settings.websocket = true;
      this.setState({ settings });
      this.connect();
      return;
    }

    fetch('web/status.json')
      .then(response => {
        if (response.ok) {
          this.errorCnt = 0;
          return (response.headers.get('Content-Type').indexOf('application/json') > -1) ? response.json() : response;
        }
      })
      .then(data => {
        if (data.time !== this.last_timestamp) {
          console.debug('fileconnect: setState (status.json)');
          this.handleFileConnectData(data);
        } else {
          this.nodataCnt += 1;
        }
      }).catch(error => {
        this.errorCnt += 1;
        console.error('fileconnect: can not fetch web/status.json (errorCnt:', this.errorCnt, ')');
      });

    if ((this.nodataCnt > 360) || (this.errorCnt > 60)) {
      this.setState({ highlight_reload: true });
      console.warn('fileconnect: timeout - no further reload (nodata:', this.nodataCnt, ', errorCnt:', this.errorCnt, ')');
    } else {
      console.debug('fileconnect: start timer');
      this.intervalID = setTimeout(this.fileconnect.bind(this), 5000);
    }
  };

  render() {
    return (<Display state={this.state} updateSettings={this.updateSettings} />);
  }
}

export default App;