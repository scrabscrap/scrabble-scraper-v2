const txt = document.createElement("textarea");
const log = (text) => {
    const logEntry = document.getElementById('logentry');
    txt.innerHTML = text;
    text = txt.value;
    logEntry.insertAdjacentText('beforeend', text);
};
function connectSocket() {
    const socket = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws_log');
    socket.addEventListener('message', ev => log(ev.data));
    socket.addEventListener('close', () => {
        setTimeout(connectSocket, 5000); // nach 5 Sekunden neu versuchen
    });
    socket.addEventListener('error', () => socket.close());
}
connectSocket();
