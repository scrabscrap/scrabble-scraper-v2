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

import React, { createContext, useContext } from "react";
import { useLiveData } from "../hooks/useLiveData";

type DataProviderProps = {
    children: React.ReactNode;
};

const WEBSOCKET_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}/ws_status`;
const STATUS_FILE = 'web/status.json';

const DataContext = createContext(null);

export const DataProvider: React.FC<DataProviderProps> = ({ children }) => {
    const liveData = useLiveData(STATUS_FILE, WEBSOCKET_URL);
    if (liveData.data === null) {
        return (
            <div className="container-fluid d-flex justify-content-center align-items-center" style={{ minHeight: "100vh" }}>
                <div className="spinner-border" role="status" />
            </div>
        );
    }
    return (
        <DataContext.Provider value={liveData}>
            {children}
        </DataContext.Provider>
    );
};

export const useDataContext = () => {
    const ctx = useContext(DataContext);
    if (!ctx) throw new Error("useDataContext must be used within a DataProvider");
    return ctx;
};