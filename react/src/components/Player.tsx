// This file is part of the scrabble-scraper-v2 distribution
// Copyright (c) 2025 Rainer Rohloff.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

import React, { useEffect, useRef, useState } from 'react';
import { useSettings } from '../context/SettingsContext';
import { useDataContext } from "../context/DataContext";

type PlayerProps = {
    player: 0 | 1;
};

export function Player({ player }: PlayerProps) {
    const { settings } = useSettings();
    const { data, usingWebSocket } = useDataContext();

    const name = (player === 0) ? data.status.name1 : data.status.name2;
    const clock = (player === 0) ? data.clock1 : data.clock2;
    const score = (player === 0) ? data.status.score1 : data.status.score2;
    const playerColor = (player === 0) ? 'text-success' : 'text-danger';
    const [timeLeft, setTimeLeft] = useState(clock);
    const timeoutID = useRef(null);
    const onMove = (data.op === 'S0' && player === 0) || (data.op === 'S1' && player === 1);
    const isPaused = (data.op === 'P0' && player === 0) || (data.op === 'P1' && player === 1);
    const headerColor = onMove ? 'bg-info' : isPaused ? 'bg-warning' : '';

    // util to format time string
    function formatSeconds(s: number): string {
        const sign = s < 0 ? '-' : '';
        const minutes = Math.abs(Math.floor(s / 60));
        const seconds = Math.abs(s % 60);
        return `${sign}${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    // reset Timer on clock changes
    useEffect(() => { setTimeLeft(clock); }, [clock]);

    // Timer start/stop
    useEffect(() => {
        if (!usingWebSocket || !onMove) return;

        const tick = () => setTimeLeft(prev => prev - 1);

        timeoutID.current = setInterval(tick, 1000);
        return () => {
            if (timeoutID.current) clearInterval(timeoutID.current);
            timeoutID.current = null;
        };
    }, [usingWebSocket, onMove]);

    const clockSymbol = onMove ? '⏳' : '⏱'; // ⏳/⏱

    return (
        <div className="card player">
            <div className={`card-header ${headerColor}`}>
                <h2 className="card-title">{name}</h2>
                <p className="h4">
                    <span className={playerColor}>
                        <b>&#x25C9;&nbsp;</b>
                    </span>
                    <span>
                        <b>
                            {score}
                            {data.status.unknown_move ? ' ?' : ''}
                        </b>
                    </span>
                    <span className="float-right monospace">
                        <b>
                            {formatSeconds(usingWebSocket ? timeLeft : clock)} {clockSymbol}
                        </b>
                    </span>
                </p>
                {settings.OBS && settings.OBSBANK && (
                    <div className="obs-bank-camera pt-4 text-center">
                        <h2>&#x1F4F9;</h2>
                    </div>
                )}            </div>
        </div>
    );
}
