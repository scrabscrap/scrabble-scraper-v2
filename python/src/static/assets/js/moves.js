const OFFSET = 12.5; // 18.75;     // Rahmenbreite
const GRID_DIM = 15;
const GRID_SIZE = 25;

const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws_status');
const POST_URL = '/moves'

const boardImage = document.getElementById('boardImage');
const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const letterGrid = document.getElementById("letterGrid");

const table = document.getElementById("movesTable");
const blankoTableBody = document.getElementById("blankoTable");

let current_moves = []
let selectedMoveId = null;
let flash_message_count = 0;


// websocket data
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.debug(msg);
    // set status indicator
    status_field = document.getElementById("status");
    status_field.innerHTML = `
                <i class="${(msg.state == "S0") ? 'bi-circle-fill text-success' : (msg.state == "S1") ? 'bi-circle-fill text-danger' : (msg.state == "EOG") ? 'bi-circle-fill' : 'bi-circle-fill text-warning'}"></i>
            `;
    // set background image
    if (msg.image) { boardImage.src = msg.image; }
    else { boardImage.src = default_board_image; }
    // rebuild table
    fillTableWS(msg);
    // rebuild blanko table
    fillBlankoTableWS(msg)
    // draw grid and board table
    drawGrid();
    updateLetterGrid(msg.board);
    // clear flash messages
    if (document.getElementById("flash_messages").innerHTML.length > 0) {
        if (flash_message_count > 0) {
            document.getElementById("flash_messages").innerHTML = "";
            flash_message_count = 0;
        } else {
            flash_message_count += 1;
        }
    }
};

ws.onclose = () => setTimeout(() => location.reload(), 5000); // reload WebSocket

// ---------------- Table ----------------
function buildRow(move, index) {
    const row = document.createElement("tr");
    if (move.move_type === 'EXCHANGE') coord = '-'
    else if (move.move_type === 'CHALLENGE_BONUS') coord = '(c)'
    else if (move.move_type == 'WITHDRAW') coord = '--'
    else if (move.move_type == 'LAST_RACK_BONUS') coord = 'Rack='
    else if (move.move_type == 'LAST_RACK_MALUS') coord = 'Rack='
    else coord = move.start

    if ((move.move_type == 'LAST_RACK_BONUS') || (move.move_type == 'LAST_RACK_MALUS')) word = move.gcg_word
    else word = move.word
    row.dataset.id = index;
    row.innerHTML = `
                <td>${index}</td>
                <td><i class="${move.player == 0 ? 'bi-circle-fill text-success' : 'bi-circle-fill text-danger'}"></i></td>
                <td class="coords edit-text" contenteditable="plaintext-only">${coord}</td>
                <td class="letters edit-text" contenteditable="plaintext-only">${word}</td>
                <td>${move.points}</td>
                <td>${move.score[move.player]}</td>
                `;
    return row;
}

function fillTableWS(msg) {
    if (msg.moves_data) {
        current_moves = msg.moves_data
        const tbody = table.querySelector("tbody");
        const fragment = document.createDocumentFragment();
        msg.moves_data.forEach((m, index) => { fragment.appendChild(buildRow(m, index)); });
        tbody.innerHTML = "";
        tbody.appendChild(fragment);
    }
}
// ---------------- End Table ----------------

// ---------------- Picture Grid ----------------
function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "rgba(0,0,255,0.4)";
    for (let i = 0; i <= GRID_DIM; i++) {
        ctx.beginPath();
        ctx.moveTo(OFFSET + i * GRID_SIZE, OFFSET);
        ctx.lineTo(OFFSET + i * GRID_SIZE, OFFSET + GRID_DIM * GRID_SIZE);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(OFFSET, OFFSET + i * GRID_SIZE);
        ctx.lineTo(OFFSET + GRID_DIM * GRID_SIZE, OFFSET + i * GRID_SIZE);
        ctx.stroke();
    }
}
// ---------------- End Picture Grid ----------------

// -------- Blanko table --------
function createBlankoRow(coord, letter) {
    const row = document.createElement('tr')

    if (letter == '_') letter = ''
    row.innerHTML = `
                <td class="coords text-center edit-text" style="width:4em">${coord}</td>
                <td>
                    <div class="letter border border-info rounded text-center edit-text blanko" contenteditable="plaintext-only" style="width:2em">${letter}</div>
                </td>
                <td>
                    <div class="float-end">
                        <button type="button" class="btn btn-outline-primary btn-sm"
                            name="btnblanko" value="Update" title="Update"><i class="bi-check2-square"></i></button>
                        <button type="button" class="btn btn-outline-danger btn-sm"
                            name="btnblankodelete" value="Delete" title="Delete Blanko">
                            <i class="bi-trash"></i></button>
                    </div>
                </td>
            `;
    return row;
}

function fillBlankoTableWS(msg) {
    if (msg.blankos) {
        const blankotbody = blankoTableBody.querySelector("tbody");
        const blankofragment = document.createDocumentFragment();
        msg.blankos.forEach((entry) => {
            blankofragment.appendChild(createBlankoRow(entry[0], entry[1]));
        });
        blankotbody.innerHTML = ""
        blankotbody.appendChild(blankofragment);
    }
}
// -------- End Blanko table --------

function highlightCells(coords) {
    drawGrid();
    ctx.fillStyle = "rgba(255, 255, 0, 0.5)";
    coords.forEach(([col, row]) => {
        ctx.fillRect(
            OFFSET + col * GRID_SIZE,
            OFFSET + row * GRID_SIZE,
            GRID_SIZE,
            GRID_SIZE
        );
    });
    // highlight in Letter-Grid
    letterGrid.querySelectorAll("td").forEach(td => td.classList.remove("highlight"));
    coords.forEach(([col, row]) => {
        const td = letterGrid.rows[row + 1].cells[col + 1];
        if (td) td.classList.add("highlight");
    });
}

// ---------------- letter Grid ----------------
function buildLetterGrid() {
    letterGrid.innerHTML = "";

    // header columns 1..15
    const headerRow = document.createElement("tr");
    const corner = document.createElement("th"); // Ecke oben links
    corner.textContent = "";
    headerRow.appendChild(corner);
    for (let c = 1; c <= GRID_DIM; c++) {
        const th = document.createElement("th");
        th.textContent = c;
        headerRow.appendChild(th);
    }
    letterGrid.appendChild(headerRow);

    // rows with A..O
    for (let r = 0; r < GRID_DIM; r++) {
        const tr = document.createElement("tr");
        // Header
        const th = document.createElement("th");
        th.textContent = String.fromCharCode(65 + r); // A=65
        tr.appendChild(th);
        // cells
        for (let c = 0; c < GRID_DIM; c++) {
            const td = document.createElement("td");
            tr.appendChild(td);
        }
        letterGrid.appendChild(tr);
    }
}

function updateLetterGrid(board) {
    buildLetterGrid();
    if (board) {
        for (index in board) {
            [c, r] = gcgToCoord(index)
            if (letterGrid.rows[r + 1] && letterGrid.rows[r + 1].cells[c + 1]) {
                letterGrid.rows[r + 1].cells[c + 1].textContent = board[index];
            }
        }
    };
};
// ---------------- End letter Grid ----------------

function gcgToCoord(gcgString) {
    const ORD_A = "A".charCodeAt(0);
    const gcgCoordH = /^([A-Oa-o])(\d+)$/;
    const gcgCoordV = /^(\d+)([A-Oa-o])$/;

    let col = 0;
    let row = 0;
    let match;

    if ((match = gcgCoordV.exec(gcgString))) {
        col = parseInt(match[1], 10) - 1;
        row = match[2].toUpperCase().charCodeAt(0) - ORD_A;
    } else if ((match = gcgCoordH.exec(gcgString))) {
        col = parseInt(match[2], 10) - 1;
        row = match[1].toUpperCase().charCodeAt(0) - ORD_A;
    }
    return [col, row];
}

function selectTableRow(tr) {
    if (!tr) return;
    table.querySelectorAll("tbody tr").forEach(r => r.classList.remove("selected"));
    tr.classList.add("selected");
    selectedMoveId = tr.dataset.id;
    m = current_moves[selectedMoveId];
    let coords = []
    for (index in m.new_letter) {
        [c, r] = gcgToCoord(index)
        coords.push([c, r]);
    }
    if (coords.length > 0) {
        highlightCells(coords);
    } else {
        drawGrid();
    }
    activateButtons(m.move_type)
}

table.addEventListener("click", e => { // select table row
    const tr = e.target.closest("tr[data-id]");
    selectTableRow(tr);
});

canvas.addEventListener("click", e => { // select on image
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left - OFFSET;
    const y = e.clientY - rect.top - OFFSET;
    if (x < 0 || y < 0) return;
    const col = Math.floor(x / GRID_SIZE);
    const row = Math.floor(y / GRID_SIZE);
    if (col < 0 || col >= GRID_DIM || row < 0 || row >= GRID_DIM) return;
    current_moves.forEach((m, index) => {
        for (coord in m.new_letter) {
            let [c, r] = gcgToCoord(coord);
            if (c === col && r === row) {
                tr = document.querySelector("[data-id='" + index + "']");
                selectTableRow(tr);
                return;
            }
        }
    });
});

table.addEventListener("keydown", (ev) => { // table: ENTER = save
    // move table
    if ((ev.target.classList.contains("coords") || ev.target.classList.contains("letters")) && ev.key === "Enter") {
        ev.preventDefault();
        const tr = table.querySelector(`tr[data-id='${selectedMoveId}']`);
        const coords = tr.cells[2].innerText.trim();
        const word = tr.cells[3].innerText.trim();

        const data = { button: 'btnSave', "btnmove": "btnmove", "move.move": selectedMoveId, "move.type": 'REGULAR', "move.coord": coords, "move.word": word };
        postData(POST_URL, data)
        ev.target.blur();
    }
});

blankoTableBody.addEventListener("keydown", (ev) => { // blankos: ENTER = save
    if (ev.target.classList.contains("blanko") && ev.key === "Enter") {
        ev.preventDefault();
        const tr = ev.target.closest("tr");
        tr.querySelector("button[name='btnblanko']")?.click();
    }
});


// -- Buttons
// blanko buttons
function cellText(el) {
    return (el?.innerText || "").replace(/\s+/g, "").toUpperCase();
}

blankoTableBody.addEventListener("click", (e) => {
    const btn = e.target.closest("button[name='btnblanko'], button[name='btnblankodelete']");
    if (!btn) return;

    const tr = btn.closest("tr");
    const coord = cellText(tr.querySelector(".coords"));
    const letter = cellText(tr.querySelector(".letter"));

    if (btn.name === "btnblanko") {
        postData(POST_URL, { btnblanko: "Update", coord, char: letter });
    } else {
        postData(POST_URL, { btnblankodelete: "Delete", coord });
    }
});
// ende blanko buttons

function activateButtons(move_type) {
    const config = {
        REGULAR: [false, false, true, true, false, false, false],
        WITHDRAW: [false, true, false, false, true, true, true],
        CHALLENGE_BONUS: [false, true, false, false, true, true, false],
        EXCHANGE: [false, true, false, true, true, true, false],
        UNKNOWN: [false, false, false, false, false, false, false],
    };
    const [insert, exchange, del, toggle, challenge, withdraw, save] = config[move_type] || [true, true, true, true, true, true, true];
    document.getElementById('btnInsert').disabled = insert;
    document.getElementById('btnExchange').disabled = exchange;
    document.getElementById('btnDelete').disabled = del;
    document.getElementById('btnToggle').disabled = toggle;
    document.getElementById('btnChallenge').disabled = challenge;
    document.getElementById('btnWithdraw').disabled = withdraw;
    document.getElementById('btnSave').disabled = save;
}

// post data via POST request
function postData(path, params, method) {
    // Create form
    const hidden_form = document.createElement('form');
    // Set method to post by default
    hidden_form.method = method || 'post';
    // Set path
    hidden_form.action = path;
    for (const key in params) {
        if (params.hasOwnProperty(key)) {
            const hidden_input = document.createElement('input');
            hidden_input.type = 'hidden';
            hidden_input.name = key;
            hidden_input.value = params[key];
            hidden_form.appendChild(hidden_input);
        }
    }
    document.body.appendChild(hidden_form);
    hidden_form.submit();
    document.body.removeChild(hidden_form);
}

document.getElementById("btnInsert").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");
    const data = { button: 'btnInsert', "btninsmoves": "btninsmoves", "move.move": selectedMoveId };
    postData(POST_URL, data)
});

document.getElementById("btnExchange").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");
    const data = { button: 'btnExchange', "btnexchange": "btnexchange", "move.move": selectedMoveId };
    postData(POST_URL, data)
});

document.getElementById("btnDelete").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");
    const data = { button: 'btnDelete', "btndelchallenge": "btndelchallenge", "move.move": selectedMoveId };
    postData(POST_URL, data)
});

document.getElementById("btnToggle").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");
    const data = { button: 'btnToggle', "btntogglechallenge": "btntogglechallenge", "move.move": selectedMoveId };
    postData(POST_URL, data)
});

document.getElementById("btnChallenge").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");
    const data = { button: 'btnChallenge', "btninschallenge": "btninschallenge", "move.move": selectedMoveId };
    postData(POST_URL, data)
});

document.getElementById("btnWithdraw").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");
    const data = { button: 'btnWithdraw', "btninswithdraw": "btninswithdraw", "move.move": selectedMoveId };
    postData(POST_URL, data)
});

document.getElementById("btnSave").addEventListener("click", async () => {
    if (!selectedMoveId) return alert("No move selected!");

    const tr = table.querySelector(`tr[data-id='${selectedMoveId}']`);
    const coords = tr.cells[2].innerText.trim();
    const word = tr.cells[3].innerText.trim();
    if ((coords != current_moves[selectedMoveId].start) || (word != current_moves[selectedMoveId].word)) {
        const data = { button: 'btnSave', "btnmove": "btnmove", "move.move": selectedMoveId, "move.type": 'REGULAR', "move.coord": coords, "move.word": word };
        postData(POST_URL, data)
    }
});

// inital data load
fillTableWS(json_msg);
fillBlankoTableWS(json_msg);
drawGrid();
buildLetterGrid();
