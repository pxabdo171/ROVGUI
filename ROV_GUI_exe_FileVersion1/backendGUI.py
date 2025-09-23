import json
import base64
from datetime import datetime
from typing import Set
from ultralytics import YOLO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import threading
import time
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import os
import serial
from nicegui import ui
import json
import base64
from datetime import datetime
from typing import Optional, Set
from ultralytics import YOLO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import threading
import time
from fastapi.responses import StreamingResponse
# Image processing and AI libraries
import cv2
import numpy as np
import contextlib
import io
import os
import asyncio
# ---------------- Arduino Setup ----------------
COM_PORT = "COM6"  
BAUD_RATE = 9600

serialInst = serial.Serial()
serialInst.port = COM_PORT
serialInst.baudrate = BAUD_RATE
serialInst.timeout = 0.1  

try:
    serialInst.open()
    print(f"✅ Arduino connected on {COM_PORT}")
except serial.SerialException as e:
    print(f"❌ Failed to open {COM_PORT}: {e}")
    exit()

# ---------------- FastAPI & YOLO ----------------
app = FastAPI()
gui_clients: Set[WebSocket] = set()
esp_client: Optional[WebSocket] = None


model_shapes = YOLO(r"C:\Users\mokaa\PilotGUI\Shapes_Task.pt")
model_shapes.verbose = False

model_fish = YOLO(r"C:\Users\mokaa\PilotGUI\best_fish_no_augmentation.pt")
model_fish.verbose = False

model_waste = YOLO(r"C:\Users\mokaa\PilotGUI\Waste_Model.pt")
model_waste.verbose = False

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

def _jpeg_bytes(img_bgr, quality: int = 85) -> bytes | None:
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return buf.tobytes() if ok else None

def _save_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)

# 2- Convert JPEG bytes to data URL
def _to_data_url(jpeg_bytes: bytes) -> str:
    b64 = base64.b64encode(jpeg_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"

# ---------------- Camera Capture ----------------
latest_frame = None
rtsp_url = "rtsp://admin:sall1221A@192.168.1.3:554/Streaming/Channels/101"

def capture_loop():
    global latest_frame
    cap = None
    while True:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print("❌ RTSP stream connection failed")
                time.sleep(1)
                continue
        ok, frame = cap.read()
        if ok:
            latest_frame = frame
        else:
            print("⚠ Error reading frame, reconnecting...")
            latest_frame = None
            cap.release()
            cap = None

threading.Thread(target=capture_loop, daemon=True).start()

def gen_frames():
    global latest_frame
    while True:
        if latest_frame is not None:
            ok, buffer = cv2.imencode('.jpg', latest_frame)
            if ok:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        else:
            img = np.zeros((400, 600, 3), dtype=np.uint8)
            cv2.putText(img, "No Camera Signal", (50, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            ok, buffer = cv2.imencode('.jpg', img)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.get("/video")
def video():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


def run_shapes_with_overlay(img_bytes: bytes):
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    with contextlib.redirect_stdout(io.StringIO()):
        results = model_shapes(img)

    counts = {"Circle": 0, "Square": 0, "Triangle": 0, "Cross": 0}
    for box in results[0].boxes:
        try:
            cls = int(box.cls[0])
            label = model_shapes.names[cls]
            if label in counts:
                counts[label] += 1
        except Exception as e:
            print("Error in shapes box:", e)

    counts["equation"] = (
        counts["Circle"] * 20 +
        counts["Square"] * 15 +
        counts["Triangle"] * 10 +
        counts["Cross"] * 5
    )

    overlay_bgr = results[0].plot()
    overlay_jpeg = _jpeg_bytes(overlay_bgr, 85)
    return counts, overlay_jpeg

def run_waste_with_overlay(img_bytes: bytes):
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    with contextlib.redirect_stdout(io.StringIO()):
        results = model_waste(img)

    waste_counts = {}
    for box in results[0].boxes:
        try:
            conf = float(box.conf[0])
            if conf > 0.6:
                cls = int(box.cls[0])
                label = model_waste.names[cls]
                waste_counts[label] = waste_counts.get(label, 0) + 1
        except Exception as e:
            print("⚠ Error in waste box:", e)

    overlay_bgr = results[0].plot()
    overlay_jpeg = _jpeg_bytes(overlay_bgr, 85)
    return waste_counts, overlay_jpeg

def run_fish_with_overlay(img_bytes: bytes):
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
   
    with contextlib.redirect_stdout(io.StringIO()):
        results = model_fish(img)

    fish_counts = {}
    for box in results[0].boxes:
        try:
            conf = float(box.conf[0])
            if conf >= 0.6:
                cls = int(box.cls[0])
                label = model_fish.names[cls]
                fish_counts[label] = fish_counts.get(label, 0) + 1
        except Exception as e:
            print("⚠ Error in fish box:", e)
  
    overlay_bgr = results[0].plot()
    overlay_jpeg = _jpeg_bytes(overlay_bgr, 85)
    return fish_counts, overlay_jpeg






# ---------------- Arduino Communication ----------------
def write_arduino(message: str) -> bool:
    try:
        serialInst.write((message + "\n").encode())
        print(f"📤 Sent to Arduino: {message}")
        return True
    except Exception as e:
        print(f"⚠ Error sending to Arduino: {e}")
        return False
async def send_to_gui(message: dict):

    msg_json = json.dumps(message)
    disconnected_clients = set()
    for ws in gui_clients:
        try:
            await ws.send_text(msg_json)
        except Exception as e:
            print(f"⚠ Failed to send to GUI: {e}")
            disconnected_clients.add(ws)

    for ws in disconnected_clients:
        gui_clients.remove(ws)    

def read_arduino():
    while True:
        try:
            data = serialInst.readline().decode('utf-8').strip()
            if data:
                print("📥 Arduino:", data)
                asyncio.run(send_to_gui(data))
        except Exception as e:
            print(f"⚠ Arduino read error: {e}")
        time.sleep(0.01)
    
# ---------------- WebSocket ----------------
@app.websocket("/ws/gui")
async def gui_ws(websocket: WebSocket):
    await websocket.accept()
    gui_clients.add(websocket)
    print("✅ GUI connected")

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await on_command(msg)
            if msg.get("type") == "command":
                command = msg.get("value", "")
                if command:
                    success = write_arduino(command)
                    if success:
                        print(f"✅ Command sent to Arduino: {command}")
                    else:
                        print(f"❌ Failed to send command: {command}")
                else:
                    print("⚠ Empty command received")
            else:
                print("GUI message:", msg)
    except WebSocketDisconnect:
        gui_clients.remove(websocket)
        print("GUI disconnected")


async def on_command(msg: dict):
    if msg["type"] == "command":
        direction = msg.get("dir")
        print(f"🎮 Received command: {direction}")
        write_arduino(direction)        

# ---------------- Main ----------------
if __name__ == "__main__":
    # Arduino reader in background
    threading.Thread(target=read_arduino, daemon=True).start()

    # Send "manual" to Arduino and wait 2 seconds for response
    time.sleep(2)
    if write_arduino("manual"):
        print("⌛ Waiting 2 seconds for Arduino response...")
        try:
            while serialInst.in_waiting:
                data = serialInst.readline().decode('utf-8').strip()
                if data:
                    print("📥 Arduino (initial):", data)
        except Exception as e:
            print(f"⚠ Error reading initial Arduino data: {e}")
    ui.run_with(app)
    # Start FastAPI / Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)
