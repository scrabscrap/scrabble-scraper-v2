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

        if (data.settings.obs) {
            return (
                <div className='container-fluid'>
                    <div className='row py-1'>
                        <div className='col-3'>
                            <Player counter={(player_on_move === '0') && data.settings.websocket} obs={data.settings.obsbank}
                                unknown_move={data.unknown_move}
                                color={player_on_move === '0' ? 'bg-info' : data.op === 'P0' ? 'bg-warning' : ''}
                                name={data.name1} score={data.score1} time={data.clock1} />
                        </div>
                        <div className='col'>
                            <Header time={this.props.state.time} highlight_reload={this.props.state.highlight_reload}
                                settings={this.props.state.settings} updateSettings={this.props.updateSettings} />
                        </div>
                        <div className='col-3'>
                            <Player counter={(player_on_move === '1') && data.settings.websocket} obs={data.settings.obsbank}
                                unknown_move={data.unknown_move}
                                color={player_on_move === '1' ? 'bg-info' : data.op === 'P1' ? 'bg-warning' : ''}
                                name={data.name2} score={data.score2} time={data.clock2} />
                        </div>
                    </div>
                    <div className='row py-1'>
                        <div className='col move-panel px-1'>
                            <div className='card card-body my-1'>
                                <div className='embed-responsive embed-responsive-16by9 obs-main-camera'>
                                    <center><h2>&#x1F4F9;</h2></center>
                                </div>
                            </div>
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
                <div>
                    <div className='container-fluid'>
                        <div className='row py-1'>
                            <div className='col-md-12'>
                                <Header time={this.props.state.time} highlight_reload={this.props.state.highlight_reload}
                                    settings={this.props.state.settings} updateSettings={this.props.updateSettings} />
                            </div>
                        </div>
                        <div className='row'>
                            <div className='col-sm-6 col-md-3'>
                                <div className='row py-1'>
                                    <div className='col-md-12 pr-1'>
                                        <Player counter={(player_on_move === '0') && data.settings.websocket} obs={false}
                                            unknown_move={data.unknown_move}
                                            color={player_on_move === '0' ? 'bg-info' : data.op === 'P0' ? 'bg-warning' : ''}
                                            name={data.name1} score={data.score1} time={data.clock1} />
                                    </div>
                                </div>
                                <div className='row py-1'>
                                    <div className='col-md-12 pr-1'>
                                        <Player counter={(player_on_move === '1') && data.settings.websocket} obs={false}
                                            unknown_move={data.unknown_move}
                                            color={player_on_move === '1' ? 'bg-info' : data.op === 'P1' ? 'bg-warning' : ''}
                                            name={data.name2} score={data.score2} time={data.clock2} />
                                    </div>
                                </div>
                                <div className='row py-1'>
                                    <div className='col pr-1'><Picture image={data.image} /></div>
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
                </div >
            );
        }
    }
}

export default Display;  