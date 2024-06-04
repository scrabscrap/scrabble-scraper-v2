import React, { Component } from 'react';

class Moves extends Component {

    is_scrabble(word) {
        let skip = false
        let chars = 0
        for (let i = 0; i < word.length; i++) {
            switch(word[i]) {
                case '(': skip = true; break;
                case ')': skip = false; break;
                case '.': break;
                default: if (! skip) { chars++ }
            }
        }
        return (chars >= 7)
    }

    render() {
        let items = []

        if (this.props.moves != null) {
            for (const [key, value] of Array.from(this.props.moves.entries())) {
                let name = value.slice(1, value.indexOf(':') + 1)
                let rest = value.slice(value.indexOf(':') + 1).trim()
                let sp = rest.split(' ')
                let img_link = './web/image-' + (key + 1) + '.jpg'
                if (sp.length === 3) { // move, name, [-|--|(challenge)|(unknown)], [], points, score 
                    items.push(<tr key={key + 1}>
                        <td><a href={img_link} target='_scrabscrap_board'>{key + 1}</a></td>
                        <td className='td-truncate text-nowrap overflow-hidden'>{name}</td>
                        <td className='pr-1 monospace' colSpan='2'>{sp[0]}</td>
                        <td className='pr-1 monospace text-right'>{sp[1]}</td>
                        <td className='pr-1 monospace text-right'>{sp[2]}</td>
                        <td className='td-fill'></td>
                    </tr>)
                } else { // move, name, coord, word, points, score
                    let marker = ''
                    if (this.is_scrabble(sp[1])) { marker = 'table-warning' }
                    items.push(<tr className={marker} key={key + 1}>
                        <td><a href={img_link} target='_scrabscrap_board'>{key + 1}</a></td>
                        <td className='td-truncate text-nowrap overflow-hidden'>{name}</td>
                        <td className='pr-1 monospace'>{sp[0]}</td>
                        <td className='pr-1 monospace'>{sp[1]}</td>
                        <td className='pr-1 monospace text-right'>{sp[2]}</td>
                        <td className='pr-1 monospace text-right'>{sp[3]}</td>
                        <td className='td-fill'></td>
                    </tr>)
                }
            }
        }
        return (
            <div className='card card-body my-1'>
                <div className='d-flex flex-column-reverse overflow-auto'>
                    <table className='table table-sm table-striped' >
                        <tbody>
                            {items}
                        </tbody>
                    </table>
                </div>
            </div >
        );
    }
}


export default Moves;