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

interface LiveDataState {
  data: {
    op: string;
    clock1: number;
    clock2: number;
    image: string;
    status: any;
    unknown_move: boolean;
  } | null;
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

  const hasUnknownMove = (data) => {
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
  const hasDataChanged = (prevData: any, newJson: any) => {
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

        setState((prev) => {
          const changed = hasDataChanged(prev.data, json);
          if (!changed) return prev; // Keine Änderung -> keine Aktualisierung
          const now = Date.now();
          const op = (json.moves.length <= 0) ? (json.onmove === json.name1) ? "S0" : "S1" : (json.onmove === json.name1) ? "S1" : "S0";
          const clock1 = json.time1;
          const clock2 = json.time2;
          const image = json.moves.length > 0 ? `web/image-${json.move}.jpg?${clock1}${clock2}` : "";
          const unknown_move = hasUnknownMove(json);

          return {
            ...prev,
            data: {
              op,
              clock1,
              clock2,
              image,
              status: json,
              unknown_move,
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
        const unknown_move = hasUnknownMove(json.status);

        setState((prev) => ({
          ...prev,
          data: {
            ...json,
            unknown_move,
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