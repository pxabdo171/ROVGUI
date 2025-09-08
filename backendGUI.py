#importing json for using json format
import json
import base64
from datetime import datetime
from typing import Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

# Track connections
gui_clients: Set[WebSocket] = set()
esp_client: Optional[WebSocket] = None


# GUI endpoint
@app.websocket("/ws/gui")
async def gui_ws(websocket: WebSocket):
    #Connect to GUI clients
    await websocket.accept()
    gui_clients.add(websocket)
    print("GUI connected")

    try:
        while True:
            #Get msg from any GUI client
            data = await websocket.receive_text()
            msg = json.loads(data)

            # If the msg is command send it to the ESP client (will update it)
            if msg.get("type") == "command" and esp_client:
                await esp_client.send_text(json.dumps(msg))
            # get the screenshot from front
            elif msg.get("type") == "screenshot":
                img_b64 = msg.get("image", "")
                if "," in img_b64:
                    _, imgstr = img_b64.split(",", 1)
                else:
                    imgstr = img_b64
                try:
                    img_bytes = base64.b64decode(imgstr)
                    filename = msg.get("filename") or f"screenshot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    print("Saved screenshot:", filename)
                except Exception as e:
                    print("Failed to save screenshot:", e)

            else:
                print("GUI message:", msg)
    except WebSocketDisconnect:
        gui_clients.remove(websocket)
        print("GUI disconnected")


#ESP endpoint
@app.websocket("/ws/esp")
async def esp_ws(websocket: WebSocket):
    #Connect to the ESP client
    global esp_client
    await websocket.accept()
    esp_client = websocket
    print("ESP connected")

    try:
        while True:
            #Get the msg from the ESP
            data = await websocket.receive_text()
            msg = json.loads(data)
            print(msg)
            # Send the msg to all GUI clients
            for gui in list(gui_clients):
                try:
                    await gui.send_text(json.dumps(msg))
                except Exception:
                    gui_clients.remove(gui)

    except WebSocketDisconnect:
        esp_client = None
        print("ESP disconnected")


# Running the server
if __name__ == "__main__":
    uvicorn.run("backendGUI:app", host="0.0.0.0", port=8000, reload=True)

