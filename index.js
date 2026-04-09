let isVisitor = false;
let socket = null;

let currentMode = null; 
const settingWin = document.querySelector(".SettingWindow");

// ===== LOGIN =====
async function checkLogin() {
    const u = document.getElementById("username").value;
    const p = document.getElementById("password").value;
    try {
        const res = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: u, pass: p }),
        });
        const data = await res.json();
        if (data.ok) {
            document.getElementById("login-screen").classList.add("hidden");
            document.getElementById("main-dashboard").classList.remove("hidden");
            connectWebSocket();
        } else {
            alert("Username or password is incorrect!");
        }
    } catch (e) {
        alert("Cannot connect to server!");
    }
}

//-------------------------------WEBSOCKET--------------------------
function connectWebSocket() {
    socket = new WebSocket("ws://192.168.1.22:5000");

    socket.onmessage = function (event) {
        const state = JSON.parse(event.data);

        document.getElementById("temp").innerText = state.temperature;
        document.getElementById("hum").innerText = state.humidity;

        const fanText = state.fan === "on" ? "ON" : "OFF";
        document.getElementById("fan-speed-info").innerText =
            `Speed: ${state.fanspeed} // State: ${fanText}`;

        document.getElementById("auto-state").innerText =
            state.autoMode ? "ON" : "OFF";
    };

    socket.onerror = function () {
        alert("WebSocket connection failed!");
    };
}

// ------------------------ CONTROL--------------------------------------------- 

function enableAutoMode() {
    if (!socket) return; //check if WebSocket is connected

    currentMode = "auto";
    console.log("Mode set to AUTO");
    //send command to server to enable auto mode and disable manual mode
    socket.send(JSON.stringify({ manual: false }));
    socket.send(JSON.stringify({ autoMode: true }));
}

// Record manual and stop auto mode
function openSettings() {
    settingWin.classList.remove("hidden");

    currentMode = "manual";  // Record manual
    console.log("Mode set to MANUAL");

    if (!socket) return;
    socket.send(JSON.stringify({ manual: true }));
    socket.send(JSON.stringify({ autoMode: false }));
    document.getElementById("auto-state").innerText = "off"; 
            
    // Update threshold display
    const thresholdInput = document.getElementById('tempthreshold');
    const display = document.getElementById('threshold-display');
    const updateDisplay = function() {
        const value = thresholdInput.value;
        const percentage = Math.round((value / 50) * 100);
        display.innerText = value + '°C (' + percentage + '%)';
    };
    updateDisplay();
    
    thresholdInput.addEventListener('input', updateDisplay);
}

function closeSettings() {
    settingWin.classList.add("hidden");
}

// Save settings and send to server, also ensures manual mode is active
function saveSettings() {
    const threshold = document.getElementById("tempthreshold").value;
    const speed = document.querySelector('input[name="options"]:checked');

    if (!speed) {
        alert("Please select a fan speed!");
        return;
    }

    if (!socket) return;

    socket.send(JSON.stringify({
        threshold: threshold,
        fanspeed: speed.value,
    }));

}
closeSettings();

    // Start button in auto mode or manual mode
function startControl() {
    if (!socket) return;

    // Prevent starting if no mode is selected or if already running
    if (!currentMode) {
        alert("Please select Auto or Manual first!");
        return;
    }

    if (currentMode === "auto") {
        console.log("Starting AUTO mode");
        socket.send(JSON.stringify({ autoMode: true }));
        socket.send(JSON.stringify({ start: true }));
    } 
    else if (currentMode === "manual") {
        console.log("Starting MANUAL mode");
        socket.send(JSON.stringify({ manual: true }));
        socket.send(JSON.stringify({ autoMode: false }));
        socket.send(JSON.stringify({ start: true }));
    }
}
// stop only without change in the mode 
function stopControl() {
    if (!socket) return; 

    isRunning = false;

    console.log("Fan stopped");
    socket.send(JSON.stringify({ stop: true }));
}

function sendControl(device, status) {
    if (isVisitor || !socket) return;
    if (device === "fan") return;

    const data = {};
    data[device] = status;
    socket.send(JSON.stringify(data));
}