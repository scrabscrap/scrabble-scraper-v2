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

import React, { useEffect, useState } from 'react';
import { useSettings } from '../context/SettingsContext';

export function SettingsForm() {
    const { settings, setSettings } = useSettings();
    const [isOpen, setIsOpen] = useState(false);
    const [localSettings, setLocalSettings] = useState(settings); // local state for form

    // Sync, on external cookie change
    useEffect(() => { setLocalSettings(settings); }, [settings]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, type, checked, value } = e.target;
        setLocalSettings(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    };

    const handleSave = () => {
        setSettings(localSettings);
        setIsOpen(prev => !prev);
    };

    const handleCancel = () => {
        setLocalSettings(settings);
        setIsOpen(prev => !prev);
    };

    const toggleShow = () => {
        if (isOpen) setLocalSettings(settings); // Reset Cookies
        setIsOpen(prev => !prev);
    };

    return (
        <span>
            <button className="btn btn-sm btn-link p-1" onClick={toggleShow} title="Settings" aria-label="Settings">
                &#x2699;
            </button>
            <div className={isOpen ? 'modal fade show d-block' : 'd-none'} tabIndex={-1}>
                <div className="modal-dialog modal-dialog-centered" style={{ minWidth: '300px' }}>
                    <div className="modal-content">
                        <div className="modal-header">
                            <h5 className="modal-title">Settings</h5>
                            <button type="button" className="close" data-dismiss="modal" onClick={handleCancel} aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div className="modal-body justify-content-left text-left m-auto">
                            <div className="form-check">
                                <input className="form-check-input" type="checkbox"
                                    id="obs" name="OBS" checked={localSettings.OBS} onChange={handleChange} />
                                <label className="form-check-label" htmlFor="obs">
                                    OBS Layout
                                </label>
                            </div>
                            <div className="form-check">
                                <input className="form-check-input" type="checkbox"
                                    id="obsbank" name="OBSBANK" checked={localSettings.OBSBANK} onChange={handleChange} />
                                <label className="form-check-label" htmlFor="obsbank">
                                    OBS Bank Camera
                                </label>
                            </div>
                            <div className="form-check">
                                <input className="form-check-input" type="checkbox"
                                    id="theme2020" name="THEME2020" checked={localSettings.THEME2020} onChange={handleChange} />
                                <label className="form-check-label" htmlFor="theme2020">
                                    2020 Theme
                                </label>
                            </div>
                            <div className="form-check">
                                <input className="form-check-input" type="checkbox"
                                    id="ws_available" name="WS_AVAILABLE" checked={localSettings.WS_AVAILABLE} disabled />
                                <label className="form-check-label text-muted" htmlFor="ws_available">
                                    WebSocket
                                </label>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-secondary" onClick={handleCancel}>
                                Close
                            </button>
                            <button type="button" className="btn btn-primary" onClick={handleSave}>
                                Save changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </span>
    );
}
