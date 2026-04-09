# 🏠 Smart System Based IoT

A real-time IoT smart system running on a **Raspberry Pi** to monitor and control a room's fan and light through a browser-based web interface. Built with WebSockets for live updates and a lightweight built-in HTTP server — no external frameworks required.

> ⚠️ **Tested on:** Raspberry Pi OS | **Python:** 3.9+

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Hardware Requirements](#-hardware-requirements)
- [Installation](#-installation)
- [Running the Project](#-running-the-project)
- [Multi-Device Support](#-multi-device-support)
- [Fan Auto Mode Logic](#-fan-auto-mode-logic)
- [API Reference](#-api-reference)
- [Error Handling](#-error-handling)
- [Customization](#-customization)
- [Future Improvements](#-future-improvements)
- [Notes](#-notes)

---

## ✨ Features

- 🌡️ Live **temperature & humidity** monitoring via DHT11 sensor
- 💡 Remote **light control** (on/off)
- 🌀 **Fan control** with two modes:
  - **Auto Mode** — speed adjusts automatically based on temperature
  - **Manual Mode** — set your own threshold and speed
- 🔐 **Owner login** — protected dashboard access
- 📡 **WebSocket** — instant state sync across all connected devices
- 🌐 **Multi-device** — multiple browsers can connect at the same time

---

## 🏗️ System Architecture

```
                        ┌─────────────────────────┐
                        │      Raspberry Pi        │
                        │                         │
  Browser / Device ◄────►   WebSocket Server      │
        (port 5000)     │   (Real-time updates)   │
                        │          │              │
  Browser / Device ◄────►   HTTP Server           │
        (port 8080)     │   (UI + REST API)       │
                        │          │              │
                        │   GPIO Controller       │
                        │   ┌──────┴──────┐       │
                        │  Fan          Lamp      │
                        │  DHT11 Sensor           │
                        └─────────────────────────┘
```

---

## 🗂️ Project Structure

```
├── iot_controller.py   # Backend: GPIO, DHT11, HTTP server, WebSocket server
├── index.html          # Frontend: dashboard layout
├── index.css           # Frontend: styling
└── index.js            # Frontend: WebSocket client & control logic
```

> 💡 Rename `Raspi_code.py` → `iot_controller.py` for a cleaner project structure.

---

## ⚙️ Hardware Requirements

| Component           | Details                  | GPIO Pin (BCM) |
|---------------------|--------------------------|----------------|
| Raspberry Pi        | Pi 3 / Pi 4 recommended  | —              |
| DHT11 Sensor        | Temperature & humidity   | D18            |
| Lamp / LED          | Room light               | GPIO 17        |
| Fan Motor           | 12V DC fan               | GPIO 27        |
| Motor Driver L298N  | Controls fan via PWM     | GPIO 13 (ENA)  |
| Battery             | 12V power supply for fan | —              |

> ⚡ The 12V battery powers the fan through the **L298N motor driver**. The Raspberry Pi itself runs on its standard 5V supply.

---

## 🛠️ Installation

**Requirements:** Python 3.9+ | Raspberry Pi OS

**1. Install system dependency:**
```bash
sudo apt install libgpiod2
```

**2. Install Python libraries:**
```bash
pip install RPi.GPIO adafruit-circuitpython-dht simple-websocket-server
```

---

## 🚀 Running the Project

**1. Start the backend:**
```bash
python iot_controller.py
```

This launches two servers:

| Server    | Port   | Purpose                       |
|-----------|--------|-------------------------------|
| HTTP      | `8080` | Serves the web UI             |
| WebSocket | `5000` | Real-time state communication |

**2. Open the dashboard** from any device on the same network:
```
http://<raspberry-pi-ip>:8080
```

**3. Login** using your configured credentials from the backend (`iot_controller.py`).

> 🔐 **Security note:** Never hardcode credentials in production. Consider using environment variables or a config file excluded from version control.

---

## 📡 Multi-Device Support

Multiple browsers or devices can connect **simultaneously** with no hard limit in the code. All clients receive live updates every **3 seconds**.

> **About `listen(5)`** — this is only the TCP backlog queue size, not a connection cap. You can safely increase it:
> ```python
> server_socket.listen(20)
> ```

On a **Raspberry Pi 4**, expect comfortable support for **20–50 concurrent devices** depending on your network.

---

## 🌀 Fan Auto Mode Logic

| Temperature  | Fan Speed |
|--------------|-----------|
| ≤ 20°C       | 🟢 Low    |
| 21°C – 35°C  | 🟡 Medium |
| > 35°C       | 🔴 High   |

---

## 🔌 API Reference

### HTTP Endpoints

| Method | Path      | Description                  |
|--------|-----------|------------------------------|
| GET    | `/`       | Serves `index.html`          |
| GET    | `/status` | Returns current state (JSON) |
| POST   | `/login`  | Authenticates the user       |

### WebSocket Commands (Client → Server)

| Key         | Values                           | Description                         |
|-------------|----------------------------------|-------------------------------------|
| `light`     | `"on"` / `"off"`                | Toggle the light                    |
| `autoMode`  | `true` / `false`                | Enable / disable auto mode          |
| `manual`    | `true` / `false`                | Enable / disable manual mode        |
| `fanspeed`  | `"low"` / `"medium"` / `"high"` | Set fan speed (manual mode)         |
| `threshold` | integer (°C)                     | Temperature threshold (manual mode) |
| `start`     | `true`                           | Start fan control                   |
| `stop`      | `true`                           | Stop the fan                        |

---

## ⚠️ Error Handling

| Scenario                        | Current Behavior                                      |
|---------------------------------|-------------------------------------------------------|
| DHT11 read failure              | Error printed to console, system continues running   |
| WebSocket client disconnects    | Client removed from list automatically               |
| Invalid WebSocket message       | Exception caught and printed, connection stays open  |
| Network drops (client side)     | Browser WebSocket will show a connection failed alert |
| HTTP request parse error        | Exception caught, socket closed safely               |

> 🔧 For production use, consider adding automatic DHT11 retry logic and persistent logging to a file.

---

## 🔧 Customization

| What to change         | Where                                              |
|------------------------|----------------------------------------------------|
| Login credentials      | `/login` handler in `iot_controller.py`           |
| GPIO pin numbers       | `Lamp`, `Fan`, `ENA` variables                    |
| Sensor update interval | `sleep(3)` in `update_loop()`                     |
| WebSocket server IP    | `index.js` → `new WebSocket("ws://<ip>:5000")`   |
| HTTP backlog size      | `server_socket.listen(5)` → increase as needed    |

---

## 🚀 Future Improvements

- [ ] 📱 Mobile app (React Native / Flutter)
- [ ] ☁️ Cloud integration (AWS IoT / MQTT broker)
- [ ] 🗄️ Database logging (SQLite / InfluxDB for sensor history)
- [ ] 🔐 Proper authentication system (JWT / hashed passwords)
- [ ] 📊 Historical charts for temperature & humidity
- [ ] 🔔 Push notifications on threshold breach
- [ ] 🌍 Remote access over the internet (ngrok / VPN)

---

## 📝 Notes

- Uses a **raw TCP socket** for HTTP — no Flask or external web framework needed.
- Shared state is protected with `threading.Lock()` for thread safety.
- The **L298N motor driver** handles the 12V fan power; PWM duty cycle maps to Low (30%) / Medium (60%) / High (100%).
- DHT11 read errors are caught silently and printed to the console without crashing the server.
# Smart-System-based-IoT
# Smart-System-based-IoT
