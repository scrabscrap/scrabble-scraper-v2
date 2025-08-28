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

import React from 'react';
import { SettingsForm } from './SettingsForm';
import { useDataContext } from "../context/DataContext";

export function Header() {
    const { data, usingWebSocket, isStale } = useDataContext();

    function getLoadingIcon(usingWebSocket: boolean | null): string {
        if (usingWebSocket === null) return String.fromCodePoint(0x1F50E); // Lupe
        if (usingWebSocket) return String.fromCodePoint(0x26A1); // Blitz
        return String.fromCodePoint(0x1F4BE); // Diskette
    }

    const items = Array.from(data.tournament).map((char: string, i: number) => (
        <span key={i} className="tile">
            {char !== ' ' ? char.toUpperCase() : '\u00A0'}
        </span>
    ));

    const timeString = String(data.time).split('.')[0]; // cut off nano sec
    const commitString = import.meta.env.PACKAGE_VERSION + ' (' + import.meta.env.VITE_APP_VERSION + ')';

    const buttonClass = isStale ? 'btn btn-link text-danger p-1' : 'btn btn-link text-muted p-1';

    return (
        <div className='header bg-body'>
            <div className='card-body'>
                <div className='row'>
                    <div className='justify-content-center text-center m-auto'>
                        {items}
                    </div>
                </div>
                <div className='row'>
                    <div className='justify-content-center text-center m-auto'>
                        <span className='text-muted'>
                            {timeString}&nbsp;v{commitString}
                        </span>
                        <span>
                            &nbsp;{getLoadingIcon(usingWebSocket)}
                            <button className={buttonClass} title='Reload' aria-label="Reload"
                                onClick={() => window.location.reload()}>
                                &#x21BB;
                            </button>
                        </span>
                        <SettingsForm />
                    </div>
                </div>
            </div>
        </div>
    );
}
