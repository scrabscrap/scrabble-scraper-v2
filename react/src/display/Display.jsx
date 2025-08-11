import { useGame } from '../GameContext';
import Bag from './Bag';
import Board from './Board';
import Header from './Header';
import Moves from './Moves';
import Picture from './Picture';
import Player from './Player';

function Display() {
    const { state, updateSettings } = useGame();

    let player_on_move = '';
    // fileconnect: data.op represents last move, therefore switch player_on_move
    if (state.op === 'S0') { player_on_move = (state.settings.websocket) ? '0' : '1'; }
    if (state.op === 'S1') { player_on_move = (state.settings.websocket) ? '1' : '0'; }

    let root_css = 'container-fluid ';
    if (state.settings.theme2020) {
        root_css += 'theme2020';
    } else {
        root_css += 'theme2012';
    }

    if (state.settings.obs) {
        return (
            <div className={root_css}>
                <div className='row py-1'>
                    <div className='col-4'>
                        <Player
                            counter={(player_on_move === '0') && state.settings.websocket}
                            obs={state.settings.obsbank}
                            unknown_move={state.unknown_move}
                            color={player_on_move === '0' ? 'bg-info' : state.op === 'P0' ? 'bg-warning' : ''}
                            name={state.name1}
                            score={state.score1}
                            time={state.clock1}
                            on_move={player_on_move === '0'}
                            player_color='text-success'
                        />
                    </div>
                    <div className='col'>
                        <Header
                            time={state.time}
                            highlight_reload={state.highlight_reload}
                            tournament={state.tournament}
                            settings={state.settings}
                            updateSettings={updateSettings}
                            commit={state.commit}
                        />
                    </div>
                    <div className='col-4'>
                        <Player
                            counter={(player_on_move === '1') && state.settings.websocket}
                            obs={state.settings.obsbank}
                            unknown_move={state.unknown_move}
                            color={player_on_move === '1' ? 'bg-info' : state.op === 'P1' ? 'bg-warning' : ''}
                            name={state.name2}
                            score={state.score2}
                            time={state.clock2}
                            on_move={player_on_move === '1'}
                            player_color='text-danger'
                        />
                    </div>
                </div>
                <div className='row py-1'>
                    <div className='col move-panel px-1'>
                        <div className='embed-responsive embed-responsive-16by9 obs-main-camera bg-transparent'></div>
                    </div>
                    <div className='col-3 move-panel px-1'>
                        <Bag bag={state.bag} />
                        <Moves moves={state.moves} />
                    </div>
                </div>
            </div>
        );
    } else {
        return (
            <div className={root_css}>
                <div className='row py-1'>
                    <div className='col-4'>
                        <Player
                            counter={(player_on_move === '0') && state.settings.websocket}
                            unknown_move={state.unknown_move}
                            color={player_on_move === '0' ? 'bg-info' : state.op === 'P0' ? 'bg-warning' : ''}
                            name={state.name1}
                            score={state.score1}
                            time={state.clock1}
                            on_move={player_on_move === '0'}
                            player_color='text-success'
                        />
                    </div>
                    <div className='col'>
                        <Header
                            time={state.time}
                            highlight_reload={state.highlight_reload}
                            tournament={state.tournament}
                            settings={state.settings}
                            updateSettings={updateSettings}
                            commit={state.commit}
                        />
                    </div>
                    <div className='col-4'>
                        <Player
                            counter={(player_on_move === '1') && state.settings.websocket}
                            unknown_move={state.unknown_move}
                            color={player_on_move === '1' ? 'bg-info' : state.op === 'P1' ? 'bg-warning' : ''}
                            name={state.name2}
                            score={state.score2}
                            time={state.clock2}
                            on_move={player_on_move === '1'}
                            player_color='text-danger'
                        />
                    </div>
                </div>
                <div className='row'>
                    <div className='col-sm-6 col-md-4'>
                        <div className='row py-1'>
                            <div className='col pr-3'>
                                <Picture image={state.image} />
                            </div>
                        </div>
                    </div>
                    <div className='col-auto'>
                        <div className='row py-1 justify-content-center'>
                            <div className='card'>
                                <div className='card-body'>
                                    <Board board={state.board} />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className='col move-panel'>
                        <Bag bag={state.bag} />
                        <Moves moves={state.moves} api={state.api} />
                    </div>
                </div>
            </div>
        );
    }
}

export default Display;