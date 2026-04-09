import RPi.GPIO as GPIO 
import board
import adafruit_dht
import json
import socket
import threading 
from time import sleep
from simple_websocket_server import WebSocketServer, WebSocket 

# -------------------- GPIO SETUP --------------------
GPIO.setmode(GPIO.BCM)
Lamp = 17
Fan  = 27
ENA  = 13

Dht = adafruit_dht.DHT11(board.D18)
GPIO.setup(Lamp, GPIO.OUT)
GPIO.setup(Fan,  GPIO.OUT)
GPIO.setup(ENA,  GPIO.OUT)
pwm = GPIO.PWM(ENA, 50)
pwm.start(0)

# -------------------- Shared State --------------------
state = {
    "temperature": 0,
    "humidity":    0,
    "fan":         "off",
    "light":       "off",
    "fanspeed":    "off",
    "autoMode":    False,
    "threshold":   15,
    "manual":      False,
    "running":     False  
}
state_lock = threading.Lock()

# -------------------- Helpers --------------------
def fan_level(level):
    duty = {"low": 30, "medium": 60, "high": 100}.get(level.lower(), 0)
    pwm.ChangeDutyCycle(duty)

def update_dht():
    try:
        state["temperature"] = Dht.temperature
        state["humidity"]    = Dht.humidity
    except Exception as e:
        print("DHT11 Error:", e)

def update_window():
    # Light control
    GPIO.output(Lamp, GPIO.HIGH if state["light"] == "on" else GPIO.LOW)

    # Fan logic
    if state["autoMode"] and state["running"]:
        # Auto mode: set speed based on temperature
        if state["temperature"] <= 20:
            state["fanspeed"] = "low"
        elif state["temperature"] <= 35:
            state["fanspeed"] = "medium"
        else:
            state["fanspeed"] = "high"

        GPIO.output(Fan, GPIO.HIGH)
        fan_level(state["fanspeed"])
        state["fan"] = "on"

    elif state["manual"] and state["running"]:
        # Manual mode: fan runs only if temperature >= threshold
        if state["temperature"] >= state["threshold"]:
            GPIO.output(Fan, GPIO.HIGH)
            fan_level(state["fanspeed"])
            state["fan"] = "on"
        else:
            GPIO.output(Fan, GPIO.LOW)
            pwm.ChangeDutyCycle(0)
            state["fan"] = "off"
    else:
        # Stop fan
        GPIO.output(Fan, GPIO.LOW)
        pwm.ChangeDutyCycle(0)
        state["fan"] = "off"

# -------------------- WebSocket --------------------
clients = []

class RealTimeData(WebSocket):
    def connected(self):
        print(self.address, "Connected")
        clients.append(self)
        with state_lock:
            self.send_message(json.dumps(state))

    def handle(self):
        try:
            data = json.loads(self.data)
            with state_lock:

                # Light control
                if "light" in data:
                    state["light"] = data["light"]

                # Mode control
                if "autoMode" in data:
                    state["autoMode"] = data["autoMode"]
                    if state["autoMode"]:
                        state["manual"] = False

                # Manual mode settings
                if not state["autoMode"]:
                    if "fanspeed" in data:
                        state["fanspeed"] = data["fanspeed"]
                    if "threshold" in data:
                        state["threshold"] = int(data["threshold"])
                    if "manual" in data:
                        state["manual"] = data["manual"]

                # Start/Stop fan commands
                if "start" in data:
                    state["running"] = True
                if "stop" in data:
                    state["running"] = False

                update_window()

        except Exception as e:
            print("Handle Error:", e)

    def handle_close(self):
        print(self.address, "Disconnected")
        if self in clients:
            clients.remove(self)

# -------------------- Update Loop --------------------
def update_loop():
    while True:
        update_dht()
        with state_lock:
            msg = json.dumps(state)
            current_clients = list(clients)

        for c in current_clients:
            try:
                c.send_message(msg)
            except:
                pass
        sleep(3)

# -------------------- WebSocket Server --------------------
def Start_websocket():
    server = WebSocketServer('0.0.0.0', 5000, RealTimeData)
    thr = threading.Thread(target=update_loop, daemon=True)
    thr.start()
    server.serve_forever()

# -------------------- HTTP Server --------------------
def serve_file(client_socket, path):
    if path == "/":
        path = "/index.html"
    try:
        ext = path.split(".")[-1]
        file_type = {"html": "text/html", "css": "text/css", "js": "application/javascript"}.get(ext, "text/plain")
        with open(path[1:], "rb") as f:
            client_socket.send(f"HTTP/1.1 200 OK\r\nContent-Type: {file_type}\r\n\r\n".encode())
            while True:
                content = f.read(1024)
                if not content:
                    break
                client_socket.send(content)
    except:
        client_socket.send("HTTP/1.1 404 Not Found\r\n\r\nFile Not Found".encode())

def start_http_server():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(5)
    print("HTTP Server running on port 8080")

    while True:
        client_socket, addr = server_socket.accept()
        try:
            request = client_socket.recv(1024).decode()
            if not request:
                client_socket.close()
                continue

            method = request.split()[0]
            path   = request.split()[1]

            if method == "GET" and path == "/status":
                update_dht()
                with state_lock:
                    response = json.dumps(state)
                client_socket.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n".encode())
                client_socket.send(response.encode())

            elif method == "POST" and path == "/login":
                body = request.split("\r\n\r\n")[1]
                data = json.loads(body)
                if data.get("user") == "Abdelkarim" and data.get("pass") == "12345":
                    client_socket.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"ok\": true}".encode())
                else:
                    client_socket.send("HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\n\r\n{\"ok\": false}".encode())

            elif method == "GET":
                serve_file(client_socket, path)

        except Exception as e:
            print("Request Error:", e)
        finally:
            client_socket.close()

# -------------------- Start Servers --------------------
ws_thread = threading.Thread(target=Start_websocket, daemon=True)
ws_thread.start()
start_http_server()
