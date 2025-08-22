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

import { useEffect, useState, useRef } from "react";
import { useSettings } from "../context/SettingsContext";

const POLLING_TIMEOUT = 2 * 60 * 60 * 1000; // 2h
const POLLING_INTERVAL = 3000; // 3s
const WS_TIMEOUT = 30 * 60 * 1000; // 30min
const WS_RECONNECT = 2000; // 2s
const MAX_RETRIES = 100;

interface GameStatus {
  'api': string;    // api version
  'timestamp': number | null; // timestamp for creating the json data (float) - new in api 3.0
  'commit': string; // git commit for app
  'layout': string; // custom2012, custom2020, custom2020light
  'tournament': string;
  'name1': string;
  'name2': string;
  'onmove': string; // player on move
  'time': string;   // timestamp current move
  'move': number;   // int
  'score1': number; // int
  'score2': number; // int
  'time1': number;  // int
  'time2': number;  // int
  'moves': any;
  'board': any;
  'bag': any;
  'unknown_move': boolean; // true if moves contains MoveUnknown; the score calculation is invalid
}

interface WSData {
  op: string;         // current Status of Game (START, S0, S1, P0, P1, EOG)
  clock1: number;     // current timer player1
  clock2: number;     // current timer player2
  image: string;      // image url or data image
  status: GameStatus;
}

interface LiveDataState {
  data: WSData | null;
  lastUpdate: number | null;
  isStale: boolean;
  usingWebSocket: boolean | null;
}

export function useLiveData(pollUrl: string, wsUrl: string) {
  const { settings } = useSettings();
  const [state, setState] = useState<LiveDataState>({
    data: null,
    lastUpdate: null,
    isStale: false,
    usingWebSocket: null,
  }); const errorCountRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const pollTimer = useRef(null);
  const reconnectTimer = useRef(null);
  const startTime = useRef<number | null>(null);

  const hasUnknownMove = (data: GameStatus) => {
    if (!data.move) return false;
    if (!data.moves) return false;
    const items: Array<string> = data.moves
    for (const [, value] of Array.from(items.entries())) {
      if (value.includes('(unknown)')) return true;
    }
    return false;
  };

  // --------------------------
  // Polling
  // --------------------------
  const hasDataChanged = (prevData: WSData, newJson: GameStatus) => {
    if (!prevData?.status) return true;

    return (
      prevData.status.time1 !== newJson.time1 ||
      prevData.status.time2 !== newJson.time2 ||
      prevData.status.move !== newJson.move ||
      prevData.status.onmove !== newJson.onmove
    );
  };

  const startPolling = () => {
    stopPolling();
    console.log("Start Polling...");
    setState((prev) => ({ ...prev, usingWebSocket: false }));
    if (!startTime.current) startTime.current = Date.now();

    const pollOnce = async () => {
      try {
        const res = await fetch(pollUrl);
        if (!res.ok) return;
        const json = await res.json();
        console.debug(json)

        setState((prev) => {
          const changed = hasDataChanged(prev.data, json);
          if (!changed) return prev; // Keine Änderung -> keine Aktualisierung
          const now = Date.now();
          const op = (json.moves.length <= 0) ? (json.onmove === json.name1) ? "S0" : "S1" : (json.onmove === json.name1) ? "S1" : "S0";
          const clock1 = json.time1;
          const clock2 = json.time2;
          const image = json.moves.length > 0 ? `web/image-${json.move}.jpg?${clock1}${clock2}` : "";
          // new field (api 3.1): status.unknown_move
          if (!('unknown_move' in json)) {
            json.unknown_move = hasUnknownMove(json);
          }
          return {
            ...prev,
            data: {
              op,
              clock1,
              clock2,
              image,
              status: json,
            },
            lastUpdate: changed ? now : prev.lastUpdate ?? now,
            isStale:
              prev.lastUpdate !== null &&
              now - prev.lastUpdate > POLLING_TIMEOUT,
          };
        });
      } catch (err) {
        console.error("Polling error:", err);
        errorCountRef.current += 1;
        if (errorCountRef.current >= MAX_RETRIES) {
          console.warn(`Max retries (${MAX_RETRIES}) reached, stopping polling`);
          setState(prev => ({
            ...prev,
            isStale: true
          }));
          stopPolling();
          return;
        }
      }

      // Stop after 2h
      if (startTime.current && Date.now() - startTime.current > POLLING_TIMEOUT) {
        console.warn("Polling timeout reached (2h) ⏰");
        stopPolling();
      }
    };

    pollOnce();
    pollTimer.current = setInterval(pollOnce, POLLING_INTERVAL);
  };

  const stopPolling = () => {
    if (pollTimer.current) clearInterval(pollTimer.current);
    pollTimer.current = null;
  };

  const resetPolling = () => {
    errorCountRef.current = 0;
    startTime.current = Date.now();
    setState(prev => ({
      ...prev,
      isStale: false
    }));
    startPolling();
  };

  useEffect(() => {
    window.addEventListener('load', resetPolling);
    return () => window.removeEventListener('load', resetPolling);
  }, []);

  // --------------------------
  // WebSocket
  // --------------------------
  const connectWebSocket = () => {
    if (wsRef.current) wsRef.current.close();
    if (!startTime.current) startTime.current = Date.now();

    console.log("Try WebSocket connect...");
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WS connected ✅");
      stopPolling();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      setState((prev) => ({ ...prev, usingWebSocket: true }));
    };

    ws.onmessage = (ev) => {
      try {
        const json = JSON.parse(ev.data);
        // new field (api 3.1): status.unknown_move
        if (!('unknown_move' in json.status)) {
          json.status.unknown_move = hasUnknownMove(json);
          console.debug('add unknown_move')
        }
        console.debug(json)
        setState((prev) => ({
          ...prev,
          data: {
            ...json,
          },
          lastUpdate: Date.now(),
          isStale: false,
        }));
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WS error:", err);
      ws.close(); // sorgt für onclose
    };

    ws.onclose = () => {
      console.warn("WS closed ❌");
      wsRef.current = null;
      setState((prev) => ({ ...prev, usingWebSocket: false }));

      // Reconnect every WS_RECONNECT s, max. WS_TIMEOUT
      if (startTime.current && Date.now() - startTime.current < WS_TIMEOUT) {
        reconnectTimer.current = setTimeout(connectWebSocket, WS_RECONNECT);
      } else {
        console.warn("WS reconnect timeout reached ⏰ → fallback Polling");
        startPolling();
      }
    };
  };

  // --------------------------
  // Lifecycle
  // --------------------------
  useEffect(() => {
    if (settings.WS_AVAILABLE) {
      connectWebSocket();
    } else {
      startPolling();
    }

    return () => {
      stopPolling();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [settings.WS_AVAILABLE, pollUrl, wsUrl]);

  return state;
}