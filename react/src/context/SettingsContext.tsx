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

import React, { createContext, useContext, useState, useEffect } from "react";

interface SettingsType {
  OBS: boolean;
  THEME2020: boolean;
  OBSBANK: boolean;
  WS_AVAILABLE: boolean;
}

interface SettingsContextType {
  settings: SettingsType;
  setSettings: (newSettings: SettingsType) => void;
}

interface SettingsProviderProps {
  children: React.ReactNode;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

function setCookie(name: string, value: string, days = 365) {
  const d = new Date();
  d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
  const expires = "expires=" + d.toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)};${expires};path=/`;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState({
    OBS: getCookie("OBS") === "true",
    THEME2020: getCookie("THEME2020") === "true",
    OBSBANK: getCookie("OBSBANK") === "true",
    WS_AVAILABLE: false, // Default
  });

  // Fetch Header Info at first mount to check for X-WebSocket-Available
  useEffect(() => {
    async function checkWS() {
      try {
        const res = await fetch("index.html", { method: 'HEAD' });
        const ws = res.headers.get("X-WebSocket-Available") === "true";
        setSettings(prev => ({ ...prev, WS_AVAILABLE: ws }));
      } catch {
        setSettings(prev => ({ ...prev, WS_AVAILABLE: false }));
      }
    }
    checkWS();
  }, []);
  // Sync Settings -> Cookies
  useEffect(() => {
    Object.entries(settings).forEach(([key, value]) => {
      if (key !== "WS_AVAILABLE") setCookie(key, String(value));
    });
  }, [settings]);

  return (
    <SettingsContext.Provider value={{ settings, setSettings }} >
      {children}
    </SettingsContext.Provider>
  );
};

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) {
    throw new Error("useSettings must be used inside SettingsProvider");
  }
  return ctx;
}