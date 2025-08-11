import { createContext, useContext, useEffect, useRef, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}/ws_status`;

const GameContext = createContext();

export function useGame() {
    return useContext(GameContext);
}

function getCookie(name, def) {
    const val = document.cookie.split('; ').filter(row => row.startsWith(name + '=')).map(c => c.split('=')[1])[0];
    if (typeof def === 'boolean') {
        return (val) ? (val === 'true') : def;
    } else if (typeof def === 'number') {
        return (val) ? Number(val) : def;
    }
    return (val) ? val : def;
}

function setCookie(name, val) {
    document.cookie = name + '=' + val + ';SameSite=Lax';
}

export function GameProvider({ children }) {
    // State
    const [state, setState] = useState({
        op: 'START',
        tournament: 'SCRABBLE SCRAPER',
        commit: null,
        layout: null,
        clock1: 1800, clock2: 1800,
        time: Date(),
        move: null,
        name1: 'Name1', name2: 'Name2',
        score1: 0, score2: 0,
        time1: 1800, time2: 1800,
        onmove: '',
        bag: null,
        board: null,
        moves: null,
        image: null,
        settings: {
            obs: getCookie('OBS', false),
            obsbank: getCookie('OBSBANK', false),
            websocket: true,
            theme2020: getCookie('THEME2020', false)
        },
        unknown_move: false,
        highlight_reload: false,
    });

    // Refs für Timer und Polling
    const intervalID = useRef(null);
    const last_timestamp = useRef();
    const nodataCnt = useRef(0);
    const errorCnt = useRef(0);

    // --- Hilfsfunktionen ---
    const updateSettings = (val) => {
        setCookie('OBS', val.obs);
        setCookie('OBSBANK', val.obsbank);
        setCookie('THEME2020', val.theme2020);
        setState(prev => ({ ...prev, settings: { ...prev.settings, ...val } }));
    };

    const parseImage = (data) => {
        if (data.image == null) return null;
        if (data.op === 'START') return null;
        if (data.image.startsWith("b'")) {
            return 'data:image/png;base64,' + data.image.substring(2, data.image.length - 1);
        }
        return 'data:image/png;base64,' + data.image;
    };

    const hasUnknownMove = (data) => {
        if (!data.move) return false;
        if (!data.moves) return false;
        for (const [, value] of Array.from(data.moves.entries ? data.moves.entries() : Object.entries(data.moves))) {
            if (value.includes('(unknown)')) return true;
        }
        return false;
    };

    // --- WebSocket mit Hook ---
    const {
        lastMessage,
        readyState,
    } = useWebSocket(WS_URL, {
        shouldReconnect: () => true,
        reconnectAttempts: 10,
        reconnectInterval: 2000,
        onOpen: () => {
            setState(prev => ({
                ...prev,
                settings: { ...prev.settings, websocket: true }
            }));
        },
        onClose: () => {
            setState(prev => ({
                ...prev,
                settings: { ...prev.settings, websocket: false }
            }));
        },
        // onError handled by onClose
        share: true,
        retryOnError: true,
    });

    // WebSocket Nachricht empfangen
    useEffect(() => {
        if (lastMessage !== null && readyState === ReadyState.OPEN) {
            try {
                const data = JSON.parse(lastMessage.data);
                const img_str = parseImage(data);
                const unknown_move = hasUnknownMove(data);

                setState(prev => ({
                    ...prev,
                    ...(data.status || {}),
                    op: data.op,
                    clock1: data.clock1,
                    clock2: data.clock2,
                    image: img_str,
                    unknown_move,
                    settings: {
                        ...prev.settings,
                        websocket: true,
                        ...(data.status?.layout ? { theme2020: data.status.layout.includes('2020') } : {})
                    }
                }));
            } catch (e) {
                // ignore parse errors
            }
        }
        // eslint-disable-next-line
    }, [lastMessage, readyState]);

    // --- Fileconnect (Polling) ---
    const parseFileConnectImage = (data) => {
        return 'web/image-' + data.move + '.jpg?' + data.time.substring(data.time.indexOf('.') + 1);
    };

    const handleFileConnectData = (data) => {
        const op = (data.onmove === data.name1) ? 'S0' : 'S1';
        const img = parseFileConnectImage(data);
        const unknown_move = hasUnknownMove(data);

        setState(prev => ({
            ...prev,
            ...data,
            op,
            clock1: data.time1,
            clock2: data.time2,
            image: img,
            unknown_move,
            settings: {
                ...prev.settings,
                websocket: false,
                ...(data.layout ? { theme2020: data.layout.includes('2020') } : {})
            }
        }));
    };

    // --- Lifecycle: Fallback auf Polling wenn WebSocket nicht offen ---
    useEffect(() => {
        // OBS detection
        if (navigator.userAgent.includes("OBS")) {
            setState(prev => {
                const settings = {
                    ...prev.settings,
                    obs: true,
                    obsbank: getCookie('OBSBANK', false)
                };
                setCookie('OBS', settings.obs);
                setCookie('OBSBANK', settings.obsbank);
                setCookie('THEME2020', settings.theme2020);
                return { ...prev, settings };
            });
        }
    }, []);

    useEffect(() => {
        if (readyState === ReadyState.OPEN) {
            // Stoppe Polling, falls WebSocket offen
            if (intervalID.current) {
                clearTimeout(intervalID.current);
                intervalID.current = null;
            }
            return;
        }

        let cancelled = false; // <--- Hier hinzufügen

        // Starte Polling nur, wenn noch nicht aktiv
        function poll() {
            fetch('web/status.json')
                .then(response => {
                    if (response.ok) {
                        errorCnt.current = 0;
                        return (response.headers.get('Content-Type').indexOf('application/json') > -1) ? response.json() : response;
                    }
                })
                .then(data => {
                    const currentTimestamp = ('timestamp' in data) ? data.timestamp : data.time;
                    if (data && currentTimestamp != last_timestamp.current) {
                        last_timestamp.current = currentTimestamp;
                        nodataCnt.current = 0;
                        handleFileConnectData(data);
                    } else {
                        nodataCnt.current += 1;
                    }
                }).catch(() => {
                    errorCnt.current += 1;
                })
                .finally(() => {
                    if ((nodataCnt.current > 360) || (errorCnt.current > 60)) {
                        setState(prev => ({ ...prev, highlight_reload: true }));
                    }
                    if (!cancelled) {
                        intervalID.current = setTimeout(poll, 5000);
                    }
                });
        }

        poll();

        // Cleanup
        return () => {
            if (intervalID.current) {
                clearTimeout(intervalID.current);
                intervalID.current = null;
            }
        };
        // eslint-disable-next-line
    }, [readyState]);

    // --- Context Value ---
    const value = {
        state,
        updateSettings,
    };

    return (
        <GameContext.Provider value={value}>
            {children}
        </GameContext.Provider>
    );
}