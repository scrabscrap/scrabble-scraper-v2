import React, { Component } from 'react';

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
  o1: 'tabletw', o4: 'tabledl', o8: 'tabletw', o12: 'tabledl', o15: 'tabletw',
};

class Board extends Component {
  cell(coord) {
    const value = this.props.board?.[coord];
    if (value == null) return <div id={coord}></div>;
    return (
      <div id={coord} className="tile">
        {value === '_' ? '\u00A0' : value}
      </div>
    );
  }

  render() {
    return (
      <div className="justify-content-center">
        <table id="board" className="tableboard">
          <thead>
            <tr>
              <td className="tableborder"></td>
              {COLS.map((col) => (
                <td key={`col-${col}`} className="tableborder">{col}</td>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={`row-${row}`}>
                <td className="tableborder">{row.toUpperCase()}</td>
                {COLS.map((col) => {
                  const coord = `${row}${col}`;
                  const specialClass = SPECIAL_CLASSES[coord] || '';
                  return (
                    <td key={coord} className={specialClass}>
                      {this.cell(coord)}
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
}

export default Board;