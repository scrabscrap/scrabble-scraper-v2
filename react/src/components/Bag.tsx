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

export function Bag() {
    const { data } = useDataContext();
    const bag = data.status.bag
    const cntTiles = bag?.length ?? 0;
    const cntBag = cntTiles > 14 ? cntTiles - 14 : 0;
    const panelClass = `card-body bag-body${cntTiles > 0 && cntTiles <= 14 ? ' bg-warning' : ''}`;

    const items = bag.map((value: string, index: number) => (
        <span key={index} className="tile">
            {value === '_' ? '\u00A0' : value}
        </span>
    ));

    return (
        <div className="card my-1">
            <div className={panelClass}>
                {items}<br />
                {cntTiles} tiles ({cntBag} in bag)
            </div>
        </div>
    );
}
