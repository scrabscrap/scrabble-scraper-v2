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

const ROWS = 'ABCDEFGHIJKLMNO'.toLowerCase().split('');
const COLS = Array.from({ length: 15 }, (_, i) => i + 1);
const SPECIAL_CLASSES = {
  a1: 'tabletw', a4: 'tabledl', a8: 'tabletw', a12: 'tabledl', a15: 'tabletw',
  b2: 'tabledw', b6: 'tabletl', b10: 'tabletl', b14: 'tabledw',
  c3: 'tabledw', c7: 'tabledl', c9: 'tabledl', c13: 'tabledw',
  d1: 'tabledl', d4: 'tabledw', d8: 'tabledl', d12: 'tabledw', d15: 'tabledl',
  e5: 'tabledw', e11: 'tabledw',
  f2: 'tabletl', f6: 'tabletl', f10: 'tabletl', f14: 'tabletl',
  g3: 'tabledl', g7: 'tabledl', g9: 'tabledl', g13: 'tabledl',
  h1: 'tabletw', h4: 'tabledl', h8: 'tabledw', h12: 'tabledl', h15: 'tabletw',
  i3: 'tabledl', i7: 'tabledl', i9: 'tabledl', i13: 'tabledl',
  j2: 'tabletl', j6: 'tabletl', j10: 'tabletl', j14: 'tabletl',
  k5: 'tabledw', k11: 'tabledw',
  l1: 'tabledl', l4: 'tabledw', l8: 'tabledl', l12: 'tabledw', l15: 'tabledl',
  m3: 'tabledw', m7: 'tabledl', m9: 'tabledl', m13: 'tabledw',
  n2: 'tabledw', n6: 'tabletl', n10: 'tabletl', n14: 'tabledw',
  o1: 'tabletw', o4: 'tabledl', o8: 'tabletw', o12: 'tabledl', o15: 'tabletw'
};

export function Board() {
  const { data } = useDataContext();
  const board = data.board;

  const cell = coord => {
    const value = board[coord];
    if (value == null) return <div id={coord} />;
    return (
      <div id={coord} className="tile">
        {value === '_' ? '\u00A0' : value}
      </div>
    );
  };

  return (
    <div className="justify-content-center">
      <table id="board" className="tableboard">
        <thead>
          <tr>
            <td className="tableborder" />
            {COLS.map(col => (
              <td key={`col-${col}`} className="tableborder">
                {col}
              </td>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map(row => (
            <tr key={`row-${row}`}>
              <td className="tableborder">{row.toUpperCase()}</td>
              {COLS.map(col => {
                const coord = `${row}${col}`;
                const specialClass = SPECIAL_CLASSES[coord] || '';
                return (
                  <td key={coord} className={specialClass}>
                    {cell(coord)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
