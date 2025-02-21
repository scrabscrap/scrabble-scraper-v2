import React, { Component } from 'react';

import Header from './Header'
import Bag from './Bag'
import Player from './Player'
import Moves from './Moves'
import Board from './Board'
import Picture from './Picture'

class Display extends Component {

    render() {
        const data = this.props.state
        console.debug(data)

        let player_on_move = '';
        // fileconnect: data.op represents last move, therefor switch player_on_move
        if (data.op === 'S0') { player_on_move = (data.settings.websocket) ? '0' : '1' }
        if (data.op === 'S1') { player_on_move = (data.settings.websocket) ? '1' : '0' }

        let root_css = 'container-fluid '
        if (data.settings.theme2020) {
            document.body.style.backgroundColor = '#00607d'
            root_css += 'theme2020'
        } else {
            document.body.style.backgroundColor = 'darkgreen'
            root_css += 'theme2012'
        }

        if (data.settings.obs) {
            return (
                <div className={root_css}>
                    <div className='row py-1'>
                        <div className='col-4'>
                            <Player counter={(player_on_move === '0') && data.settings.websocket} obs={data.settings.obsbank}
                                unknown_move={data.unknown_move}
                                color={player_on_move === '0' ? 'bg-info' : data.op === 'P0' ? 'bg-warning' : ''}
                                name={data.name1} score={data.score1} time={data.clock1} on_move={(player_on_move === '0')}
                                player_color='text-success' />
                        </div>
                        <div className='col'>
                            <Header time={this.props.state.time} highlight_reload={this.props.state.highlight_reload} tournament={this.props.state.tournament}
                                settings={this.props.state.settings} updateSettings={this.props.updateSettings} commit={data.commit} />
                        </div>
                        <div className='col-4'>
                            <Player counter={(player_on_move === '1') && data.settings.websocket} obs={data.settings.obsbank}
                                unknown_move={data.unknown_move}
                                color={player_on_move === '1' ? 'bg-info' : data.op === 'P1' ? 'bg-warning' : ''}
                                name={data.name2} score={data.score2} time={data.clock2} on_move={(player_on_move === '1')}
                                player_color='text-danger' />
                        </div>
                    </div>
                    <div className='row py-1'>
                        <div className='col move-panel px-1'>
                            <div className='embed-responsive embed-responsive-16by9 obs-main-camera bg-transparent'></div>
                        </div>

                        <div className='col-3 move-panel px-1'>
                            <Bag bag={data.bag} />
                            <Moves moves={data.moves} />
                        </div>
                    </div>
                </div >
            )
        } else {
            return (
                <div className={root_css}>
                    <div className='row py-1'>
                        <div className='col-4'>
                            <Player counter={(player_on_move === '0') && data.settings.websocket}
                                unknown_move={data.unknown_move}
                                color={player_on_move === '0' ? 'bg-info' : data.op === 'P0' ? 'bg-warning' : ''}
                                name={data.name1} score={data.score1} time={data.clock1} on_move={(player_on_move === '0')}
                                player_color='text-success' />
                        </div>
                        <div className='col'>
                            <Header time={this.props.state.time} highlight_reload={this.props.state.highlight_reload} tournament={this.props.state.tournament}
                                settings={this.props.state.settings} updateSettings={this.props.updateSettings} commit={data.commit} />
                        </div>
                        <div className='col-4'>
                            <Player counter={(player_on_move === '1') && data.settings.websocket}
                                unknown_move={data.unknown_move}
                                color={player_on_move === '1' ? 'bg-info' : data.op === 'P1' ? 'bg-warning' : ''}
                                name={data.name2} score={data.score2} time={data.clock2} on_move={(player_on_move === '1')}
                                player_color='text-danger' />
                        </div>
                    </div>

                    <div className='row'>

                        <div className='col-sm-6 col-md-4'>
                            <div className='row py-1'>
                                <div className='col pr-3'><Picture image={data.image} /></div>
                            </div>
                        </div>
                    
                        <div className='col-auto'>
                            <div className='row py-1 justify-content-center'>
                                <div className='card'>
                                    <div className='card-body'>
                                        <Board board={data.board} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className='col move-panel'>
                            <Bag bag={data.bag} />
                            <Moves moves={data.moves} />
                        </div>

                    </div>
                </div>
            );
        }
    }
}

export default Display;  