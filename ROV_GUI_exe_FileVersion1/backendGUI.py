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

# ---------------- Arduino Setup ----------------
COM_PORT = "COM3"  
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

model_shapes = YOLO(r"C:\Users\mokaa\PilotGUI\Shapes_Task.pt")
model_shapes.verbose = False

model_fish = YOLO(r"C:\Users\mokaa\PilotGUI\best_fish_no_augmentation.pt")
model_fish.verbose = False

model_waste = YOLO(r"C:\Users\mokaa\PilotGUI\Waste_Model.pt")
model_waste.verbose = False

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------- Camera Capture ----------------
latest_frame = None
rtsp_url = "rtsp://admin:sall1221A@10.0.0.12:554/Streaming/Channels/101"

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

# ---------------- Arduino Communication ----------------
def write_arduino(message: str) -> bool:
    try:
        serialInst.write((message + "\n").encode())
        print(f"📤 Sent to Arduino: {message}")
        return True
    except Exception as e:
        print(f"⚠ Error sending to Arduino: {e}")
        return False

def read_arduino():
    while True:
        try:
            data = serialInst.readline().decode('utf-8').strip()
            if data:
                print("📥 Arduino:", data)
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

    # Start FastAPI / Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)
