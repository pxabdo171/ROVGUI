import json
import base64
from datetime import datetime
from typing import Set, Optional
from ultralytics import YOLO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import threading
import time
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import os
from nicegui import ui
import contextlib
import io
import asyncio

# ---------------- FastAPI & YOLO ----------------
app = FastAPI()
gui_clients: Set[WebSocket] = set()
esp_client: Optional[WebSocket] = None

model_shapes = YOLO(r"C:\Users\Ali\ROV_GUI_exe_FileVersion1\Shapes_Task.pt")
model_shapes.verbose = False

model_fish = YOLO(r"C:\Users\Ali\ROV_GUI_exe_FileVersion1\best_fish_no_augmentation.pt")
model_fish.verbose = False

model_waste = YOLO(r"C:\Users\Ali\ROV_GUI_exe_FileVersion1\Waste_Model.pt")
model_waste.verbose = False

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

def _jpeg_bytes(img_bgr, quality: int = 85) -> bytes | None:
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return buf.tobytes() if ok else None

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

# ---------------- YOLO Models ----------------
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
            print("GUI message:", msg)
    except WebSocketDisconnect:
        gui_clients.remove(websocket)
        print("GUI disconnected")

# ---------------- Main ----------------
if __name__ == "__main__":
    ui.run_with(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)
