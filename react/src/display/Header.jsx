import React, { Component } from 'react';

import Settings from './Settings'

class Header extends Component {

    render() {
        const items = [];
        const str = this.props.settings.header_text;

        for (let i in str) {
            if (str[i] !== ' ') {
                items.push(<span key={i} className='tile'>{str[i]}</span>)
            } else {
                items.push(<span key={i}>&nbsp;</span>)
            }
        }

        const buttonclass = (this.props.highlight_reload) ? 'btn btn-link text-danger p-1' :'btn btn-link text-muted p-1'
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
                                {this.props.time}&nbsp;{(this.props.settings.websocket) ? 'ws' : '  '}&nbsp;
                                v{import.meta.env.PACKAGE_VERSION}-{import.meta.env.VITE_APP_VERSION}
                            </span>
                            <span><button className={buttonclass} onClick={() => window.location.reload()} title='Reload'>&#x21BB;</button></span>
                            <Settings settings={this.props.settings} updateSettings={this.props.updateSettings} />
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default Header;