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

const POLLING_TIMEOUT = 1 * 60 * 60 * 1000; // 1h
const POLLING_INTERVAL = 2000; // 2s
const WS_TIMEOUT = 30 * 60 * 1000; // 30min
const WS_RECONNECT = 2000; // 2s
const MAX_RETRIES = 100;

interface GameStatus {
  'api': string;    // api version
  'state': string; // current state
  'timestamp': number | null; // timestamp for creating the json data (float) - new in api 3.0
  'time': string;   // timestamp current move
  'commit': string; // git commit for app
  'layout': string; // custom2012, custom2020, custom2020light
  'tournament': string;
  'name1': string;
  'name2': string;
  'onmove': string; // player on move
  'move': number;   // int
  'score1': number; // int
  'score2': number; // int
  'clock1': number;  // int
  'clock2': number;  // int
  'time1': number;  // int
  'time2': number;  // int
  'image': string;  // current image URL or base64 encoded
  'bag': any;
  'board': any;
  'moves': any;
  'moves_data': any;
  'unknown_move': boolean; // true if moves contains MoveUnknown; the score calculation is invalid
}

interface LiveDataState {
  data: GameStatus | null;
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
  });
  const errorCountRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const pollTimer = useRef(null);
  const reconnectTimer = useRef(null);
  const startTime = useRef<number | null>(null);
  const etagRef = useRef<string | null>(null);

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
  const hasDataChanged = (prevData: GameStatus, newJson: GameStatus) => {
    if (!prevData) return true;

    return (
      prevData.time1 !== newJson.time1 ||
      prevData.time2 !== newJson.time2 ||
      prevData.move !== newJson.move ||
      prevData.onmove !== newJson.onmove ||
      prevData.time !== newJson.time ||
      prevData?.timestamp !== newJson?.timestamp
    );
  };

  const startPolling = () => {
    stopPolling();
    console.log("Start Polling...");
    setState((prev) => ({ ...prev, usingWebSocket: false }));
    if (!startTime.current) startTime.current = Date.now();

    const pollOnce = async () => {
      // first check for Timeout
      if (startTime.current && Date.now() - startTime.current > POLLING_TIMEOUT) {
        console.warn("Polling timeout reached (2h) ⏰");
        stopPolling();
        return;
      }

      try {
        const headers: Record<string, string> = {};
        if (etagRef.current) {
          headers["If-None-Match"] = etagRef.current;
        }
        const res = await fetch(pollUrl, { headers }); // set previous etag for request
        if (res.status === 304) { // check for changes
          console.log("No changes (304)");
          return;
        }
        if (!res.ok) return;

        const json = await res.json();
        const etag = res.headers.get("etag"); // get current etag
        if (etag) {
          etagRef.current = etag;
        }

        console.debug(json)

        setState((prev) => {
          const changed = hasDataChanged(prev.data, json);
          if (!changed) return prev; // no change -> no data update
          const now = Date.now();

          if (!('unknown_move' in json)) { // new field (api 3.1): status.unknown_move
            json.unknown_move = hasUnknownMove(json);
          }
          if (!('clock1' in json)) { // new field (api 3.1): status.clock1 / status.clock2
            json.clock1 = 1800 - json.time1;
            json.clock2 = 1800 - json.time2;
          }

          return {
            ...prev,
            data: json,
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

    };

    pollOnce();
    pollTimer.current = setInterval(pollOnce, POLLING_INTERVAL);
  };

  const stopPolling = () => {
    if (pollTimer.current) clearInterval(pollTimer.current);
    pollTimer.current = null;
    setState(prev => ({
      ...prev,
      isStale: true
    }));

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
        if (!('unknown_move' in json)) {
          json.unknown_move = hasUnknownMove(json);
          console.debug('add unknown_move')
        }
        console.debug(json)
        setState((prev) => ({
          ...prev,
          data: json,
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