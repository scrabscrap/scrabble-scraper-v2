import React, { Component } from 'react';

import Settings from './Settings'

class Header extends Component {

    render() {
        var items = []
        var str = this.props.settings.header_text

        for (let i in str) {
            if (str[i] !== ' ') {
                items.push(<span key={i} className='tile'>{str[i]}</span>)
            } else {
                items.push(<span key={i}>&nbsp;</span>)
            }
        }

        const buttonclass = (this.props.highlight_reload) ?
            'btn btn-danger btn-sm float-right' :
            'btn btn-success btn-sm float-right bg-body'
        // new: 'btn btn-info btn-sm float-right bg-body'

        return (
            <div className='header bg-body'>
                <div className='card-body'>
                    <div className='row'>
                        <div className='col'></div>
                        <div className='col-auto'>
                            {items}
                        </div>
                        <div className='col'>
                            <button type='button' data-toggle='tooltip' data-placement='top' title='Refresh page'
                                className={buttonclass}
                                onClick={() => window.location.reload(true)}>
                                &#x21BB;
                            </button>
                            <Settings settings={this.props.settings} updateSettings={this.props.updateSettings} />
                        </div>
                    </div>
                    <div className='row'>
                        <div className='col'></div>
                        <div className='col-auto'>
                            <span className='text-muted'>https://github.com/scrabscrap/scrabble-scraper-v2
                                {(this.props.settings.websocket) ? ' (websocket)' : ''} - {this.props.time}</span>
                        </div>
                        <div className='col'></div>
                    </div>
                </div>
            </div>
        );
    }
}

export default Header;