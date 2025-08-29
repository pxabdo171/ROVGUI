#importing json for using json format
import json
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

