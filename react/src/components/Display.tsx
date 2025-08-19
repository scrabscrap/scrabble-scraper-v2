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

import { Bag } from './Bag';
import { Board } from './Board';
import { Header } from './Header';
import { Moves } from './Moves';
import { Picture } from './Picture';
import { Player } from './Player';
import { useSettings } from '../context/SettingsContext';

export function Display() {
    const { settings } = useSettings();
    const rootCss = `container-fluid ${settings.THEME2020 ? 'theme2020' : 'theme2012'}`;

    return (
        <div className={rootCss}>
            <div className="row py-1">
                <div className="col-4">
                    <Player player={0} />
                </div>
                <div className="col">
                    <Header />
                </div>
                <div className="col-4">
                    <Player player={1} />
                </div>
            </div>

            {!settings.OBS && (
                <div className="row">
                    <div className="col-sm-6 col-md-4">
                        <div className="row py-1">
                            <div className="col pr-3">
                                <Picture />
                            </div>
                        </div>
                    </div>
                    <div className="col-auto">
                        <div className="row py-1 justify-content-center">
                            <div className="card">
                                <div className="card-body">
                                    <Board />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="col move-panel">
                        <Bag />
                        <Moves />
                    </div>
                </div>
            )}

            {settings.OBS && (
                <div className="row">
                    <div className="col move-panel px-1">
                        <div className="embed-responsive embed-responsive-16by9 obs-main-camera bg-transparent" />
                    </div>
                    <div className="col-3 move-panel px-1 mr-2">
                        <Bag />
                        <Moves />
                    </div>
                </div>
            )}
        </div>
    );
}
