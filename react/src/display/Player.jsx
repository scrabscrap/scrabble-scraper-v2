import { useEffect, useRef, useState } from 'react';

function formatSeconds(s) {
    let sign = (s < 0) ? '-' : '';
    let minutes = Math.abs(Math.floor(s / 60));
    let seconds = Math.abs(Math.floor(s % 60));
    return sign + minutes + ':' + (seconds > 9 ? seconds : '0' + seconds);
}

function Player({
    counter,
    obs,
    unknown_move,
    color,
    name,
    score,
    time,
    on_move,
    player_color
}) {
    const [next, setNext] = useState(time);
    const [startTime, setStartTime] = useState(Date.now());
    const timeoutID = useRef(null);

    // Reset timer when time prop changes
    useEffect(() => {
        setNext(time);
        setStartTime(Date.now());
    }, [time]);

    // Timer effect
    useEffect(() => {
        if (!counter) return;
        function tick() {
            setNext(prev => prev - 1);
        }
        timeoutID.current = setInterval(tick, 1000);
        return () => {
            clearInterval(timeoutID.current);
        };
    }, [counter, startTime]);

    const headerclass = 'card-header ' + color;
    let symbol_clock = String.fromCodePoint(0x23F1); // ⏱
    if (on_move) {
        symbol_clock = String.fromCodePoint(0x23F3); // ⏳
    }

    return (
        <div className='card player'>
            <div className={headerclass}>
                <h2 className='card-title'>{name}</h2>
                <p className='h4'>
                    <span className={player_color}><b>&#x25C9;&nbsp;</b></span>
                    <span><b>{score}{unknown_move ? ' ?' : ''}</b></span>
                    <span className='float-right monospace'>
                        <b>
                            {formatSeconds(counter ? next : time)} {symbol_clock}
                        </b>
                    </span>
                </p>
                <div className={obs ? 'obs-bank-camera pt-4' : 'hidden'}>
                    <center><div><h2>&#x1F4F9;</h2></div></center>
                </div>
            </div>
        </div>
    );
}

export default Player;