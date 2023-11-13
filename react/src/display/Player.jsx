import React, { Component } from 'react';

class Player extends Component {
    timeoutID;

    constructor(props) {
        super(props);
        this.state = {
            next: props.time,
            startTime: Date.now()
        };
    }

    componentDidMount() {
        this.setState({ next: this.props.time, startTime: Date.now() })
        if (this.props.counter) { // clock countdown, if websocket access and player is active
            this.timeoutID = setTimeout(this.counter.bind(this), 1000);
        }
    }

    componentDidUpdate(prevProps) {
        if (prevProps.time !== this.props.time) { // got new time info
            this.setState({ next: this.props.time, startTime: Date.now() })
        }
    }

    componentWillUnmount() {
        if (this.timeoutID) { // clear running timeoutID
            clearTimeout(this.timeoutID);
        }
        this.timeoutID = null
    }

    counter = () => {
        clearTimeout(this.timeoutID);
        this.timeoutID = null
        if (this.props.counter) {
            const nowTime = Date.now()
            const nextTime = this.state.startTime + this.state.next
            this.timeoutID = setTimeout(this.counter.bind(this), 1000 - ((nowTime - nextTime) * 1000));
            this.setState({ next: this.state.next - 1 })
        }
    }

    formatSeconds(s) { // format <sign><M>:<SS>
        let sign = (s < 0) ? '-' : ''
        let minutes = Math.abs(~~(s / 60));
        let seconds = Math.abs(~~(s % 60));
        return sign + minutes + ':' + (seconds > 9 ? seconds : '0' + seconds);
    }

    render() {

        if (this.props.counter) { // clock countdown, if websocket access and player is active
            if (this.timeoutID) {
                clearTimeout(this.timeoutID);
                this.timeoutID = null
            }
            this.timeoutID = setTimeout(this.counter.bind(this), 1000);
        }
        const headerclass = 'card-header ' + this.props.color
        return (
            <div className='card player'>
                <div className={headerclass}>
                    <h2 className='card-title'>{this.props.name}</h2>
                    <p className='h4'>
                        <span ><b>{this.props.score} {this.props.unknown_move ? ' ?' : ''}</b></span>
                        <span className='float-right monospace' >
                            <b>{this.formatSeconds(this.props.counter ? this.state.next : this.props.time)} &#x1F551;</b>
                        </span>
                    </p>

                    <div className={this.props.obs ? 'obs-bank-camera pt-4' : 'hidden'} >
                        <center><div><h2>&#x1F4F9;</h2></div></center>
                    </div>
                </div>
            </div >
        );
    }
}

export default Player;