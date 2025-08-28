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
import { useDataContext } from "../context/DataContext";

function isScrabble(word: string): boolean {
    let skip = false;
    let chars = 0;
    for (let i = 0; i < word.length; i++) {
        switch (word[i]) {
            case '(':
                skip = true;
                break;
            case ')':
                skip = false;
                break;
            case '.':
                break;
            default:
                if (!skip) chars++;
        }
    }
    return chars >= 7;
}

export function Moves() {
    const { data } = useDataContext();
    const moves: Map<number, string> | null = data.moves as Map<number, string> | null;
    const api: string = data.api;


    function renderRow(key: number, imgLink: string, name: string, sp: string[], marker: string = '') {
        return (
            <tr className={marker} key={key + 1}>
                <td>
                    <a href={imgLink} target="_scrabscrap_board">
                        {key + 1}
                    </a>
                </td>
                <td className="td-truncate text-nowrap overflow-hidden">{name}</td>
                {sp.map((val, idx) => (
                    <td
                        key={idx}
                        className={`pr-1 monospace ${idx >= 2 ? 'text-right' : ''}`}
                        colSpan={sp.length === 3 && idx === 0 ? 2 : 1}
                    >
                        {val}
                    </td>
                ))}
                <td className="td-fill" />
            </tr>
        );
    }

    const items = moves
        ? Array.from(moves.entries()).map(([key, value]) => {
            let name = value.slice(1, value.indexOf(':') + 1);
            let rest = value.slice(value.indexOf(':') + 1).trim();
            let sp = rest.split(' ');
            let img_number = parseInt(api) < 3 ? key + 1 : key;
            let img_link = `./web/image-${img_number}.jpg`;
            let marker = sp.length > 3 && isScrabble(sp[1]) ? 'table-warning' : '';

            return renderRow(key, img_link, name, sp, marker);
        }) : [];
    return (
        <div className="card card-body my-1">
            <div className="d-flex flex-column-reverse overflow-auto">
                <table className="table table-sm table-striped">
                    <tbody>{items}</tbody>
                </table>
            </div>
        </div>
    );
}
