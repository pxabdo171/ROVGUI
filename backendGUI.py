import json
import base64
from datetime import datetime
from typing import Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

# Image processing and AI libraries
import cv2
import numpy as np
from ultralytics import YOLO
import contextlib
import io

app = FastAPI()

# Track connected clients
gui_clients: Set[WebSocket] = set()
esp_client: Optional[WebSocket] = None

# Load both models
model_shapes = YOLO("Shapes_Task.pt")
model_shapes.verbose = False

model_waste = YOLO("Waste_Model.pt")
model_waste.verbose = False

# Analyze image with shapes model
def process_shapes(img_bytes: bytes):
    img_array = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

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

    equation_output = (
        counts["Circle"] * 20 +
        counts["Square"] * 15 +
        counts["Triangle"] * 10 +
        counts["Cross"] * 5
    )

    # Print to terminal
    print(f"\nShapes Detection:")
    for shape, count in counts.items():
        print(f" - {shape}: {count}")
    print(f" ➕ Equation = {equation_output}")

    return {
        "Circle": counts["Circle"],
        "Square": counts["Square"],
        "Triangle": counts["Triangle"],
        "Cross": counts["Cross"],
        "equation": equation_output
    }

# Analyze image with waste model
def process_waste(img_bytes: bytes):
    img_array = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

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
            print("⚠Error in waste box:", e)

    # Print to terminal
    print("\nWaste Detection:")
    for label, count in waste_counts.items():
        print(f" - {label}: {count}")

    return waste_counts

# WebSocket endpoint for GUI clients
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
                model_type = msg.get("model_type", "shapes")  # default to shapes

                if "," in img_b64:
                    _, imgstr = img_b64.split(",", 1)
                else:
                    imgstr = img_b64

                try:
                    img_bytes = base64.b64decode(imgstr)
                    filename = msg.get("filename") or f"screenshot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    print(f"\n📸 Screenshot saved: {filename}")

                    # Run selected model only
                    if model_type == "shapes":
                        result = process_shapes(img_bytes)
                        await websocket.send_text(json.dumps({
                            "type": "shapes_analysis",
                            "data": result
                        }))
                    elif model_type == "waste":
                        result = process_waste(img_bytes)
                        await websocket.send_text(json.dumps({
                            "type": "waste_analysis",
                            "data": result
                        }))
                    else:
                        print("Unknown model_type:", model_type)

                except Exception as e:
                    print("Failed to process image:", e)

            else:
                print("GUI message:", msg)

    except WebSocketDisconnect:
        gui_clients.remove(websocket)
        print("GUI disconnected")

# WebSocket endpoint for ESP client
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

# Run the server
if __name__ == "__main__":
    uvicorn.run("backendGUI:app", host="0.0.0.0", port=8000, reload=True)