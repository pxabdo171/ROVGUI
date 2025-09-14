import json
import base64
from datetime import datetime
from typing import Optional, Set
from ultralytics import YOLO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

# Image processing and AI libraries
import cv2
import numpy as np
import contextlib
import io
import os

# Directory to save screenshots
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

def _save_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)

app = FastAPI()

# Track connected clients
gui_clients: Set[WebSocket] = set()
esp_client: Optional[WebSocket] = None

# Load AI models (Eraky)
model_shapes = YOLO(r"C:\Users\mokaa\PilotGUI\Shapes_Task.pt")
model_shapes.verbose = False

model_fish = YOLO(r"C:\Users\mokaa\PilotGUI\best_fish_no_augmentation.pt")
model_fish.verbose = False

model_waste = YOLO(r"C:\Users\mokaa\PilotGUI\Waste_Model.pt")
model_waste.verbose = False

# help for back image (Eraky)
# 1- Convert BGR image to JPEG bytes
def _jpeg_bytes(img_bgr, quality: int = 85) -> bytes | None:
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return buf.tobytes() if ok else None

# 2- Convert JPEG bytes to data URL
def _to_data_url(jpeg_bytes: bytes) -> str:
    b64 = base64.b64encode(jpeg_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"

# 3- Run models and return counts and overlay image (Eraky)
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


@app.websocket("/ws/gui")
async def gui_ws(websocket: WebSocket):
    await websocket.accept()
    gui_clients.add(websocket)
    print("✅ GUI connected")

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "command" and esp_client:
                await esp_client.send_text(json.dumps(msg))

            elif msg.get("type") == "screenshot":
                img_b64 = msg.get("image", "")
                model_type = msg.get("model_type", "shapes")
                request_id = msg.get("requestId")

                if "," in img_b64:
                    _, imgstr = img_b64.split(",", 1)
                else:
                    imgstr = img_b64

                try:
                    img_bytes = base64.b64decode(imgstr)    
                    filename = msg.get("filename") or f"screenshot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"

                    if model_type == "shapes":
                        data, overlay_jpeg = run_shapes_with_overlay(img_bytes)
                        payload = {"type": "shapes_analysis", "data": data, "requestId": request_id}
                        
                    elif model_type == "waste":
                        data, overlay_jpeg = run_waste_with_overlay(img_bytes)
                        payload = {"type": "waste_analysis", "data": data, "requestId": request_id}
                    
                    elif model_type == "fish":
                        data, overlay_jpeg = run_fish_with_overlay(img_bytes)
                        payload = {"type": "fish_analysis", "data": data, "requestId": request_id}
                    else:
                        payload = {"type": "error", "message": f"Unknown model_type: {model_type}", "requestId": request_id}
                        overlay_jpeg = None

                    if overlay_jpeg:
                        name, ext = os.path.splitext(filename)
                        annotated_path = os.path.join(SAVE_DIR, f"{name}_annotated{ext}")
                        _save_bytes(annotated_path, overlay_jpeg)
                        print(f"🖼️ Annotated saved: {annotated_path}")

                        payload["image"] = _to_data_url(overlay_jpeg)

                    await websocket.send_text(json.dumps(payload))

                except Exception as e:
                    print("Failed to process image:", e)
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"failed to process image: {e}",
                        "requestId": request_id
                    }))

            else:
                print("GUI message:", msg)

    except WebSocketDisconnect:
        gui_clients.remove(websocket)
        print("GUI disconnected")

@app.websocket("/ws/esp")
async def esp_ws(websocket: WebSocket):
    global esp_client
    await websocket.accept()
    esp_client = websocket
    print("✅ ESP connected")

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            print("📩 ESP message:", msg)

            for gui in list(gui_clients):
                try:
                    await gui.send_text(json.dumps(msg))
                except Exception:
                    gui_clients.remove(gui)

    except WebSocketDisconnect:
        esp_client = None
        print("❌ ESP disconnected")

if __name__ == "__main__":
    uvicorn.run("backendGUI:app", host="0.0.0.0", port=8000, reload=True)
