from fastapi import Request
from nicegui import ui, app
import os
from flask import Flask, Response
import cv2
from starlette.responses import StreamingResponse
import threading
import numpy as np
import json
import websockets
import asyncio

ws = None

async def connect_ws():
    global ws
    try:
        ws = await websockets.connect("ws://localhost:8000/ws/gui")
        print("GUI connected to backend")

        async def listen():
            try:
                while True:
                    msg = await ws.recv()
                    print("From backend:", msg)
            except Exception as e:
                print("Disconnected from backend:", e)

        asyncio.create_task(listen())
    except Exception as e:
        print("Failed to connect:", e)

app.on_startup(connect_ws)



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
app.add_static_files('/static', STATIC_DIR)

@ui.page('/')
def index_page():
   
    custom_html = """
    <!doctype html>
<html lang="ar">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>ROV Control - Prototype</title>
  <style>
    :root{
      --bg:#071126;
      --panel:#0f2b45;
      --accent:#0ea5a4;
      --muted:#9fb0c4;
      --glass: rgba(255,255,255,0.04);
      --success:#27ae60;
      --danger:#e53e3e;
      --card-radius:14px;
      font-family: 'Segoe UI', Tahoma, system-ui, Arial, sans-serif;
    }
    *{box-sizing:border-box}

    html, body {
      height: 100%;
      margin: 0;
      background-image: url("/static/background.jpg");
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      color: #dbeafe;
    }
    body {
  overflow: hidden;
  }


    .app {
      width: min(100vw, 1600px);
      margin: 10px auto;         
      box-sizing: border-box;
     
    }

    .app {
  transform: scale(0.67) translate(0px, -25px); 
  transform-origin: top left; 
  width: 145%;             
  height: auto;
  margin-left:20px;
  }


    .grid{
      display:grid;
      /* make side columns flexible so the app can shrink */
      grid-template-columns: minmax(240px, 1fr) minmax(360px, 2fr) minmax(220px, 1fr);
      gap:18px
    }

    .panel{
      background: linear-gradient(180deg, var(--bg) 0%, #0d1b2a 100%);
      padding:20px;
      border-radius:var(--card-radius);
      box-shadow:0 4px 18px rgba(2,6,23,0.6);
      border:1px solid rgba(255,255,255,0.03);
      min-width: 0; /* IMPORTANT: enables content to shrink within grid tracks */
    }

    h2{margin:0 0 12px 0;font-weight:600;color:#e6f0ff}

    .motors{display:flex;flex-direction:column;gap:12px;margin-bottom: 100px;}
    .motor{display:flex;align-items:center;gap:12px;padding:10px;border-radius:10px;background:var(--glass)}
    .led{width:14px;height:14px;border-radius:50%;background-color: rgb(192, 19, 19);box-shadow:0 0 8px rgba(39,174,96,0.35)}
    .motor label{flex:1;font-size:15px;color:#cfe8ff}
    .speed{width:110px;display:flex;gap:8px;align-items:center}
    input[type=range]{accent-color:var(--accent);width:100%}
    .speed-value{width:26px;text-align:center;color:var(--muted)}

    .left-bottom{display:flex;flex-direction:column;gap:12px;margin-top:10px}
      .joystick-wrap {
  display: flex;
  flex-direction: column; 
  align-items: center; 
  gap: 16px;
 }

.joystick {
  width: 150px;
  height: 150px;
  background: #0b3b54;
  border-radius: 50%;
  position: relative;
}

.stick {
  width: 50px;
  height: 50px;
  background: #e8f7ff;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

    select, button{padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:var(--muted)}
    .port-indicator{display:flex;align-items:center;gap:8px}
    .port-indicator .led{width:12px;height:12px}

    /* center video */
    .video-area{display:flex;flex-direction:column;gap:10px;align-items:center;}
    .video{width:100%;height:450px;background:linear-gradient(180deg,#021323,#000000);border-radius:10px;border:1px solid rgba(255,255,255,0.03);display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.08);font-size:18px}
    .controls{width:100%;display:flex;gap:12px;justify-content:center}
    .btn {padding:3px 3px;border-radius:10px;border:none;background:#123548;color:#e8f7ff;cursor:pointer;height: 50px;font-size: 16px;flex: 0 0 auto}
    .btn.secondary{background:rgba(255,255,255,0.03);color:var(--muted)}

    /* right column */
    .sensors{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .gauge{padding:12px;border-radius:10px;background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent)}
    .gauge h3{margin:0 0 6px 0;font-size:22px;color:var(--muted)}
    .g-value{font-size:20px;font-weight:700}

    /* make IMU gauge span two columns without overflowing */
    .gauge.imu {grid-column: 1 / -1}

    .timer{display:flex;flex-direction:column;gap:8px;align-items:center}
    .timer .time{font-size:28px;font-weight:700;color:#fff}

    /* Error box */
    .error-box{margin-top:8px;padding:12px;border-radius:10px;background:rgba(229,62,62,0.09);border:1px solid rgba(229,62,62,0.12);color:#ffdede}
    .error-ok{background:rgba(39,174,96,0.06);border:1px solid rgba(39,174,96,0.12);color:#d7ffea;height: 25px}

 
    .bottom {grid-column: 3 / span 1;display: grid;grid-template-columns: 1fr 1fr; gap: 12px;margin-top: 12px;}
    .bottom .task:nth-child(3) {grid-column: 1 / span 2; }
    .task{flex:1;padding:5px;border-radius:12px;background:rgba(255,255,255,0.02);text-align:center}

    .stop-row{display:flex;gap:12px;align-items:center}
    .stop{flex:1;padding:14px;border-radius:10px;background:rgba(255,255,255,0.03);text-align:center}
    .e-stop{padding:12px 18px;border-radius:12px;background:linear-gradient(180deg,#e74b4b,#c33b3b);color:white;font-weight:700}

    .port-select {text-align: center}

    #gauge-imu {display: grid;grid-template-columns: repeat(3, auto)}
    #gauge-imu span {text-align: center}

    /* Leakage Sensor Color States */
    .leakage .g-value {padding: 8px;border-radius: 6px;background-color: #14532d;transition: background-color 0.3s;width: 100%;text-align: center}
    .leak-detected {background-color: #7f1d1d !important}

    input[type=range] {-webkit-appearance: none;width: 100%;height: 8px;border-radius: 5px;background: black;cursor: pointer;outline: none}
    input[type=range]::-webkit-slider-thumb {-webkit-appearance: none;appearance: none;width: 20px;height: 20px;background: #1e40af;border-radius: 50%;border: 2px solid #1e3a8a;cursor: pointer;position: relative;z-index: 1}
    input[type=range]::-moz-range-thumb {width: 20px;height: 20px;background: #1e40af;border-radius: 50%;border: 2px solid #1e3a8a;cursor: pointer;position: relative;z-index: 1}

    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button {-webkit-appearance: none;margin: 0}
    input[type=number] { -moz-appearance: textfield }

    .icon-container {
  display: flex;
  align-items: center;
  gap: 20px;
  justify-content: center;
  margin-top: 24px;
  z-index: 999;
  position: relative;
  transform: scale(1);  
  overflow: visible;    
 }
 


    .icon-container img {width: 60px;height: 60px;border-radius: 50%;object-fit: cover;padding: 6px;background: radial-gradient(circle, #0f2b45 70%, #123548 100%);border: 2px solid #0ea5a4;animation: pulseGlow 2s infinite ease-in-out;transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease}
    .icon-container img:hover {transform: scale(1.2) rotate(5deg);box-shadow: 0 0 25px rgba(14, 165, 164, 0.9), 0 0 40px rgba(14, 165, 164, 0.6);border-color: #1ff5f2}

    @keyframes pulseGlow {0%, 100% {box-shadow: 0 0 10px rgba(14, 165, 164, 0.5)} 50% {box-shadow: 0 0 25px rgba(14, 165, 164, 0.9)}}

    @media (max-width:980px){
      .grid{grid-template-columns:1fr}
      .bottom{flex-direction:column}
    }
    .compass-card {
      width: 300px;
      border-radius: 20px;
      padding: 18px;
      text-align: center;
      transform:translate(87px,-10px);
    }
    .compass {
      width: 250px;
      height: 250px;
      margin: 0 auto;
      display: block;
    }
    .heading {
      margin-top: 12px;
      font-size: 20px;
      letter-spacing: 0.4px;
    }
    .servo-control {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 20px;
      padding: 20px;
      background: #1a2233;
      border-radius: 15px;
      box-shadow: 0 4px 12px rgba(0,0,50,0.4);
     }

    label {
      margin-bottom: 10px;
      font-size: 18px;
      color: #aad4ff;
    }

    input[type=range] {
      -webkit-appearance: none;
      appearance: none;
      background: #2a3b55;
      height: 6px;
      border-radius: 4px;
      outline: none;
      width: 350px;
      transform: translate(0px,8px);
    }

    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #66aaff;
      cursor: pointer;
      box-shadow: 0 0 6px rgba(100,150,255,0.7);
    }

    input[type=range]::-moz-range-thumb {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #66aaff;
      cursor: pointer;
      box-shadow: 0 0 6px rgba(100,150,255,0.7);
    }

   

    .value {
      margin-top: 8px;
      margin-bottom: 0px;
      font-size: 16px;
      color: #88c0ff;
      transform: translate(3px,10px);
    }

    #video img {
    width: 1000px !important;
    height: 530px !important;
    border: 2px solid #123548;
    border-radius: 10px;
    object-fit: cover;
    transform:translate(0px,-50px)
}
  </style>
</head>
<body>
  <div class="app">
    <div class="grid">
      <!-- LEFT COLUMN -->
      <div class="panel">
        <h2 style="font-size: 30px;">Motors</h2>
        <div class="motors" id="motors-list"></div>

        <div class="left-bottom">
        
          <div><h2 style="font-size: 30px;transform:translate(0px,15px)">Servo Motors</h2>
          <div class="servo-control">
    <label for="horizontal-range">Horizontal Servo</label>
    <input type="range" id="horizontal-range" min="0" max="180" value="90">
    <div class="value" id="horizontal-value">90°</div>
  </div>
  <div class="servo-control" >
    <label for="vertical-range">Vertical Servo</label>
    <input type="range" id="vertical-range" min="0" max="180" value="90">
    <div class="value" id="vertical-value">90°</div>
  </div>
          </div>
          <div class="joystick-wrap">
  <span style="font-size:15px">Navigation Joystick</span>
  
  <div class="joystick">
    <div class="stick"></div>
  </div>
  
  <div class="port-select">
    <label style="color:var(--muted);font-size:17px">Joystick Port</label>
    <div style="display:flex;gap:8px;align-items:center;transform:translate(0px,10px);">
      <select class="port">
        <option>COM1</option>
        <option>COM2</option>
        <option selected>COM3</option>
        <option>COM4</option>
      </select>
      <div class="port-indicator">
        <div class="led port-led" style="background-color: rgb(192, 19, 19);"></div>
        <div style="color:var(--muted);font-size:17px" class="port-status">Disconnected</div>
      </div>
    </div>
  </div>
</div>

        </div>
      </div>

      <!-- CENTER -->
      <div class="panel video-area">
        <h2 style="font-size: 30px;">Video</h2>
        <div class="video" id="video">Video feed (placeholder)</div>
        <div class="controls" style="display:flex;flex-direction:column;gap:12px">
          <button class="btn" id="open-camera" style="font-size: 20px;">Open Camera</button>
          <div style="display:grid;grid-template-columns: repeat(2, 1fr); gap: 10px; width:100%">
            <button class="btn" id="cam1" style="font-size: 20px;">Camera 1</button>
            <button class="btn" id="cam2" style="font-size: 20px;">Camera 2</button>
          </div>
          <div class="timer panel" style="padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);width:100%;height:170px">
            <div style="font-size:17px;color:var(--muted)">Timer</div>
            <div class="time" id="timer" style="font-size: 30px;">0.0</div>
            <div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap;justify-content:center">
              <button class="btn secondary" id="start" style="width: 160px;font-size: 20px;">Start</button>
              <button class="btn secondary" id="pause" style="width: 160px;font-size: 20px;">Pause</button>
              <button class="btn secondary" id="reset" style="width: 160px;font-size: 20px;">Reset</button>
            </div>
          </div>

          <div class="panel" style="padding:10px;background:rgba(255,255,255,0.02);width:100%;height:250px;margin-bottom:0">
            <h2 style="margin-bottom:8px;font-size:20px; transform:translate(0px,-10px)">PID Control</h2>
            <div style="display:flex;flex-direction:column;gap:10px;transform:translate(0px,-20px)">
             <div style="display:flex;align-items:center;gap:5px;">
  <label style="width:18px;color:var(--muted);font-size:18px;">PID</label>
  <select class="port1" style="width:90%;margin-left:45px;text-align:center;font-size:17px">
        <option selected>Heave</option>
        <option>Yaw</option>
        <option>Surge</option>
        <option>Sway</option>
      </select>
</div>

              <div style="display:flex;align-items:center;gap:8px;">
  <label style="width:18px;color:var(--muted);font-size:18px;">P</label>
  <input type="number" id="pid-p" min="0" max="10" step="0.1" value="0" 
         style="flex:0 0 auto;
                background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:18px;
                outline:none;
                text-align:center;
                width:90%;transform:translate(40px,0px);">
</div>

      <div style="display:flex;align-items:center;gap:8px;">
        <label style="width:18px;color:var(--muted);font-size:18px;">I</label>
        <input type="number" id="pid-i" min="0" max="10" step="0.1" value="0" style="flex:0 0 auto;background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:18px;
                outline:none;
                text-align:center;
                width:90%;transform:translate(40px,0px);">
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <label style="width:18px;color:var(--muted);font-size:18px;">D</label>
        <input type="number" id="pid-d" min="0" max="10" step="0.1" value="0" style="flex:0 0 auto;background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:18px;
                outline:none;
                text-align:center;
                width:90%;transform:translate(40px,0px);">
      </div>
              
            </div>
          </div>
        </div>

        <div class="icon-container" style="transform: translate(0px,40px)">
          <a href="http://localhost:8080/Ai"><img src="/static/artificial-intelligence.png"></a>
          <a href="http://localhost:8080/"><img src="/static/pilot%20(1).png"></a>
          <a href="http://localhost:8080/copilot">
  <img src="/static/pilot.png" alt="Pilot">
</a>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="panel">
        <h2 style="font-size: 30px;">Sensors</h2>
        <div class="sensors">
          <div class="gauge">
            <h3>Temperature</h3>
            <div class="g-value" id="temp">24°C</div>
          </div>

          <div class="gauge">
            <h3>Depth</h3>
            <div class="g-value" id="depth">0.0 m</div>
          </div>

          <div class="gauge imu">
            <h3>IMU Sensor</h3>
            <div class="compass-card">
    <svg id="compass" class="compass" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <!-- outer ring -->
      <circle cx="100" cy="100" r="94" fill="#0f0f0f" stroke="#222" stroke-width="4"/>

      <!-- needle group rotates -->
      <g id="needleGroup" transform="rotate(0 100 100)">
        <!-- north (red) -->
        <path d="M100 30 L110 100 L100 92 L90 100 Z" fill="#d94a4a" stroke="#b03b3b" stroke-width="0.7"/>
        <!-- south (blue) -->
        <path d="M100 170 L110 100 L100 108 L90 100 Z" fill="#3b88b0" stroke="#2c6b8a" stroke-width="0.7"/>
        <!-- center hub -->
        <circle cx="100" cy="100" r="6" fill="#333" stroke="#111" stroke-width="1.2"/>
      </g>

      <!-- compass cardinal letters -->
      <text x="100" y="22" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">N</text>
      <text x="178" y="105" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">E</text>
      <text x="100" y="190" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">S</text>
      <text x="22" y="105" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">W</text>
    </svg>

  </div>
            <div class="g-value" id="gauge-imu">
  <span id="pitch">Pitch: 0°</span>
  <span id="roll">Roll: 0°</span>
  <span id="yaw">Yaw: 0°</span>
</div>
          </div>

          <div class="gauge leakage">
            <h3>Leakage Sensor</h3>
            <div class="g-value" id="leakage-status">Safe</div>
          </div>
        </div>

        <div style="margin-top:3px">
          <h2 style="margin-top:0;font-size: 25px;margin-bottom:0;">Error</h2>
          <div id="error" class="error-ok" style="font-size: 20px; margin-top:5px;">No Errors</div>
        </div>


        <div class="bottom">
          <button class="task" style="font-size: 20px;">Task 1</button>
          <button class="task" style="font-size: 20px;">Task 2</button>
          <button class="task" style="font-size: 20px;">Task 3</button>
        </div>
        <div class="joystick-wrap" style="transform:translate(0px,30px)">
  <span style="font-size:15px">Pitch Joystick</span>
  <div class="joystick">
    <div class="stick"></div>
  </div>
  <div class="port-select">
    <label style="color:var(--muted);font-size:17px">Joystick Port</label>
    <div style="display:flex;gap:8px;align-items:center;transform:translate(0px,10px);">
      <select class="port">
        <option>COM1</option>
        <option>COM2</option>
        <option selected>COM3</option>
        <option>COM4</option>
      </select>
      <div class="port-indicator">
        <div class="led port-led" style="background-color: rgb(192, 19, 19);"></div>
        <div style="color:var(--muted);font-size:17px" class="port-status">Disconnected</div>
      </div> 
    </div>   
  </div>   
</div>

        
      </div>

    </div>
  </div>
</body>
</html>
    """

    ui.html(custom_html).classes('w-full')

    ui.add_body_html("""
     <script>
  window.addEventListener('load', () => {
    const motorsList = document.getElementById('motors-list');
  if (!motorsList) { console.error('motors-list not found'); }

  const maxValue = 255; 

  for (let i = 1; i <= 6; i++) {
    const m = document.createElement('div');
    m.className = 'motor';
    m.innerHTML = `
      <div class='led' id='led-${i}' style="transform:translate(-5px,0px);"></div>
      <label style="transform:translate(7px,0px);font-size: 20px;">Motor ${i}</label>
      <div class='speed'>
        <input type='number' min='0' max='${maxValue}' value='0' id='r-${i}' 
          style="background-color:#0f2b45;
          border:1px solid #1f4b75;color:#fff;padding:4px 6px;border-radius:6px;font-size:20px;
          outline:none;text-align:center;transition:all 0.2s ease;width:110%">
      </div>`;
    motorsList.appendChild(m);
      const r = m.querySelector(`#r-${i}`);
      const v = m.querySelector(`#v-${i}`);
        const led = m.querySelector(`#led-${i}`);
  const input = m.querySelector(`#r-${i}`);
                     
                     input.addEventListener('input', () => {
    const val = parseInt(input.value) || 0;
    if (val > 0) {
      led.style.backgroundColor = 'limegreen';
    } else {
      led.style.backgroundColor = 'rgb(192, 19, 19)';
    }
  });
                     
      r.addEventListener('input', () => { if (v) v.textContent = r.value; });
    }
                     
      
  

  const horizontalRange = document.getElementById('horizontal-range');
    const verticalRange = document.getElementById('vertical-range');
    const horizontalValue = document.getElementById('horizontal-value');
    const verticalValue = document.getElementById('vertical-value');

    horizontalRange.addEventListener('input', () => {
      horizontalValue.textContent = horizontalRange.value + '°';
      console.log('Horizontal servo:', horizontalRange.value);
    });

    verticalRange.addEventListener('input', () => {
      verticalValue.textContent = verticalRange.value + '°';
      console.log('Vertical servo:', verticalRange.value);
    });
  
    const ws = new WebSocket("ws://localhost:8000/ws/gui");

    ws.onopen = () => {
        console.log("Connected to backend");
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log("Message from ESP:", msg);
    };


    horizontalRange.addEventListener('input', sendServoValues);
    verticalRange.addEventListener('input', sendServoValues);

    function sendServoValues() {
        const horizontalValue = horizontalRange.value;
        const verticalValue = verticalRange.value;

        document.getElementById('horizontal-value').innerText = horizontalValue + '°';
        document.getElementById('vertical-value').innerText = verticalValue + '°';

        const msg = {
            type: "command",
            servo: { horizontal: horizontalValue, vertical: verticalValue }
        };

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(msg));
        }
    }

  document.querySelectorAll('.joystick-wrap').forEach(wrapper => {
  const joystick = wrapper.querySelector('.joystick');
  const stick = wrapper.querySelector('.stick');
  const portSelect = wrapper.querySelector('.port');
  const portLed = wrapper.querySelector('.port-led');
  const portStatus = wrapper.querySelector('.port-status');

  if (portSelect && portLed && portStatus) {
    portSelect.addEventListener('change', () => {
      portLed.style.background = '#f59e0b';
      portStatus.textContent = 'Connecting...';
      setTimeout(() => {
        portLed.style.background = 'var(--success)';
        portStatus.textContent = 'Connected';
      }, 700);
    });
  }

  let dragging = false;
  if (joystick && stick) {
    joystick.addEventListener('pointerdown', e => {
      dragging = true;
      joystick.setPointerCapture(e.pointerId);
    });
    window.addEventListener('pointerup', () => {
      dragging = false;
      stick.style.transform = 'translate(-50%, -50%)';
    });
    joystick.addEventListener('pointermove', e => {
      if (!dragging) return;
      const rect = joystick.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = Math.max(-48, Math.min(48, e.clientX - cx));
      const dy = Math.max(-48, Math.min(48, e.clientY - cy));
      stick.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
    });
  }
});


                     

    let t = 0; let timerId = null; const timerEl = document.getElementById('timer');
    document.getElementById('start')?.addEventListener('click', () => {
      if (timerId) return;
      timerId = setInterval(() => { t += 0.1; if (timerEl) timerEl.textContent = t.toFixed(1); }, 100);
    });
    document.getElementById('pause')?.addEventListener('click', () => { clearInterval(timerId); timerId = null; });
    document.getElementById('reset')?.addEventListener('click', () => { clearInterval(timerId); timerId = null; t = 0; if (timerEl) timerEl.textContent = '0.0'; });

    let cameraOpen = false;

    document.getElementById("open-camera").addEventListener("click", function () {
        let videoDiv = document.getElementById("video");

        if (!cameraOpen) {
 
            videoDiv.innerHTML =
                '<img id="camera-stream" src="/video_feed" ' +
                'style="width:500px; height:300px; border:none;" />';
            this.innerText = "Close Camera";
            cameraOpen = true;
        } else {

            videoDiv.innerHTML = "Video feed (placeholder)";
            this.innerText = "Open Camera";
            cameraOpen = false;
        }
    });
                     
      document.getElementById("cam1").addEventListener("click", function() {
    fetch("/set_camera/0");
});
document.getElementById("cam2").addEventListener("click", function() {
    fetch("/set_camera/1");
});

    
  let currentYaw = 0;   
  let targetYaw = 0;    

  function updateYaw(newYaw) {
    targetYaw = newYaw;
  }

  function animateCompass() {
    
    currentYaw += (targetYaw - currentYaw) * 0.1; 
    document.getElementById("needleGroup")
      .setAttribute("transform", `rotate(${currentYaw} 100 100)`);
    requestAnimationFrame(animateCompass);
  }

  animateCompass();

  const socket = new WebSocket("ws://localhost:8000/ws/gui");

  socket.onopen = () => {
    console.log("Connected to backend");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "imu") {
   
      document.getElementById("pitch").textContent = `Pitch: ${data.pitch}°`;
      document.getElementById("roll").textContent = `Roll: ${data.roll}°`;
      document.getElementById("yaw").textContent = `Yaw: ${data.yaw}°`;

   
      updateYaw(data.yaw);
    }
    if (data.type === "temp") {
      document.getElementById("temp").textContent = `${data.degree}°C`;
    }
    if (data.type === "depth") {
      document.getElementById("depth").textContent = `${data.distance} m`;
    }
    if (data.type === "leakage") {
    const leakageDiv = document.getElementById("leakage-status");
    if (data.status === 1) {
      leakageDiv.textContent = "Danger";
      leakageDiv.style.backgroundColor = "#7f1d1d";
      leakageDiv.style.color = "white";
    } else {
      leakageDiv.textContent = "Safe";
      leakageDiv.style.backgroundColor = "#14532d";
      leakageDiv.style.color = "inherit";
    }
  }
  };

    window.setROVError = function (msg) {
      const e = document.getElementById('error');
      if (!e) return;
      if (!msg) { e.className = 'error-ok'; e.textContent = 'No Errors'; }
      else { e.className = 'error-box'; e.textContent = msg; }
    };
    
  });
</script>

    """)

    max_value = 255

    async def send_motors(mode):
        motors = {f"M{i}": (max_value if mode == "on" else 0) for i in range(1, 7)}
        data = {"type": "Motors", "mode": mode, "data": motors}
        if ws:
            await ws.send(json.dumps(data))
        print("Sent:", data)
    async def send_motors1():
      motors = {}
      for i in range(1, 7):
        val = await ui.run_javascript(f'document.getElementById("r-{i}").value')
        motors[f"M{i}"] = val
        data = {
        "type": "Motors",
        "data": motors
        }
      if ws:
        await ws.send(json.dumps(data))
      else:
        print("Motors data:", data) 
    async def send_pid():
        valPID = await ui.run_javascript('document.querySelector(".port1").value')
        valP   = await ui.run_javascript('document.getElementById("pid-p").value')
        valI   = await ui.run_javascript('document.getElementById("pid-i").value')
        valD   = await ui.run_javascript('document.getElementById("pid-d").value')

        data = {
            "type" : "PID",
            "PID": valPID,
            "P": valP,
            "I": valI,
            "D": valD
        }
        
        await ws.send(json.dumps(data))
        
    ui.button('Send', on_click=send_pid).style(
    'position: fixed; right: 20px; bottom: 20px; z-index: 9999; '
    'width:100px !important; margin-top:8px; padding:1px 1px; border-radius:8px; '
    'border:none; background:#123548 !important; color:#e8f7ff; cursor:pointer; '
    'height:30px; font-size:13.5px; flex:0 0 auto; text-transform:none !important;'
    'transform: translate(-750px,-43px) !important;'
    )
    
    ui.button('Auto').style(
    'position: fixed; right: 20px; bottom: 20px; z-index: 9999; '
    'width:100px !important; margin-top:8px; padding:1px 1px; border-radius:8px; '
    'border:none; background:#123548 !important; color:#e8f7ff; cursor:pointer; '
    'height:30px; font-size:13.5px; flex:0 0 auto; text-transform:none !important;'
    'transform: translate(-645px,-43px) !important;'
    )

    async def turn_on_all():
        await ui.run_javascript(f"""
            for (let i = 1; i <= 6; i++) {{
                document.getElementById(`led-${{i}}`).style.backgroundColor = 'limegreen';
                document.getElementById(`r-${{i}}`).value = {max_value};
            }}
        """)

    async def stop_all():
        await ui.run_javascript("""
            for (let i = 1; i <= 6; i++) {
                document.getElementById(`led-${i}`).style.backgroundColor = 'rgb(192, 19, 19)';
                document.getElementById(`r-${i}`).value = 0;
            }
        """)

    async def handle_turn_on():
        await turn_on_all()
        await send_motors("on")

    async def handle_stop_all():
        await stop_all()
        await send_motors("off")
    ui.button(
    "Turn on All",
    on_click=handle_turn_on
    ).style(
    'position: fixed; right: 20px; bottom: 20px; z-index: 9999; '
    'width:160px !important; margin-top:8px; padding:1px 1px; border-radius:8px; '
    'border:none; background:#123548 !important; color:#e8f7ff; cursor:pointer; '
    'height:35px; font-size:13.5px; flex:0 0 auto; text-transform:none !important;'
    'transform: translate(-1305px,-450px) !important;'
)

    ui.button(
    "Stop All",
    on_click=handle_stop_all
).style(
    'position: fixed; right: 20px; bottom: 20px; z-index: 9999; '
    'width:160px !important; margin-top:8px; padding:1px 1px; border-radius:8px; '
    'border:none; background:#123548 !important; color:#e8f7ff; cursor:pointer; '
    'height:35px; font-size:13.5px; flex:0 0 auto; text-transform:none !important;'
    'transform: translate(-1136px,-450px) !important;'
)
    ui.button(
    "Send",on_click=send_motors1
).style(
    'position: fixed; right: 20px; bottom: 20px; z-index: 9999; '
    'width:330px !important; margin-top:8px; padding:1px 1px; border-radius:8px; '
    'border:none; background:#123548 !important; color:#e8f7ff; cursor:pointer; '
    'height:20px; font-size:14px; flex:0 0 auto; text-transform:none !important;'
    'transform: translate(-1136px,-410px) !important;font-size: 13.5px !important;'
)




@ui.page('/copilot')
def copilot_page():
   
    custom_html = """
    <!doctype html>
<html lang="ar">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>ROV Control - Prototype</title>
  <style>
    :root{
      --bg:#071126;
      --panel:#0f2b45;
      --accent:#0ea5a4;
      --muted:#9fb0c4;
      --glass: rgba(255,255,255,0.04);
      --success:#27ae60;
      --danger:#e53e3e;
      --card-radius:14px;
      font-family: 'Segoe UI', Tahoma, system-ui, Arial, sans-serif;
    }
    *{box-sizing:border-box}

    html, body {
      height: 100%;
      margin: 0;
      background-image: url("/static/grunge-wall-texture.jpg");
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      color: #dbeafe;
    }
    body {
  overflow: hidden;
  }


    .app {
      width: min(100vw, 1600px);
      margin: 10px auto;         
      box-sizing: border-box;
     
    }

    .app {
  transform: scale(0.67) translate(0px, -25px); 
  transform-origin: top left; 
  width: 145%;             
  height: auto;
  margin-left:20px;
  }


    .grid{
      display:grid;
      /* make side columns flexible so the app can shrink */
      grid-template-columns: minmax(240px, 1fr) minmax(360px, 2fr) minmax(220px, 1fr);
      gap:18px
    }

    .panel{
      background: linear-gradient(to bottom, #1a1a1a, #000000);
      padding:20px;
      border-radius:var(--card-radius);
      box-shadow:0 4px 18px rgba(2,6,23,0.6);
      border:1px solid rgba(255,255,255,0.03);
      min-width: 0; /* IMPORTANT: enables content to shrink within grid tracks */
    }

    h2{margin:0 0 12px 0;font-weight:600;color:white}

    .motors{display:flex;flex-direction:column;gap:12px}
    .motor{display:flex;align-items:center;gap:12px;padding:10px;border-radius:10px;background:var(--glass)}
    .led{width:14px;height:14px;border-radius:50%;background-color: rgb(192, 19, 19);box-shadow:0 0 8px rgba(39,174,96,0.35)}
    .motor label{flex:1;font-size:15px;color:#cfe8ff}
    .speed{width:110px;display:flex;gap:8px;align-items:center}
    input[type=range]{accent-color:var(--accent);width:100%}
    .speed-value{width:26px;text-align:center;color:var(--muted)}

    .left-bottom{display:flex;flex-direction:column;gap:12px;margin-top:10px}
      .joystick-wrap {
  display: flex;
  flex-direction: column; 
  align-items: center; 
  gap: 16px;
  margin-top: 10px;
 }

.joystick {
  width: 150px;
  height: 150px;
  background: rgb(227, 227, 227);
  border-radius: 50%;
  position: relative;
}

.stick {
  width: 50px;
  height: 50px;
  background: rgb(67, 67, 67);
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

    select, button{padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:var(--muted)}
    .port-indicator{display:flex;align-items:center;gap:8px}
    .port-indicator .led{width:12px;height:12px}

    /* center video */
    .video-area{display:flex;flex-direction:column;gap:10px;align-items:center;}
    .video{width:100%;height:450px;background: linear-gradient(to right, #2e2e2e, #0d0d0d);border-radius:10px;border:1px solid rgba(255,255,255,0.03);display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.08);font-size:18px}
    .controls{width:100%;display:flex;gap:12px;justify-content:center}
    .btn {padding:3px 3px;border-radius:10px;border:none;background:rgb(59, 57, 57);color:#ffffff;cursor:pointer;height: 50px;font-size: 16px;flex: 0 0 auto}
    .btn.secondary{background:rgba(167, 167, 167, 0.093);color:var(--muted)}

    /* right column */
    .sensors{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .gauge{padding:12px;border-radius:10px;background:linear-gradient(180deg, rgba(73, 73, 73, 0.356), transparent)}
    .gauge h3{margin:0 0 6px 0;font-size:22px;color:rgb(187, 187, 187);}
    .g-value{font-size:20px;font-weight:700;color:rgb(255, 255, 255);}

    /* make IMU gauge span two columns without overflowing */
    .gauge.imu {grid-column: 1 / -1}

    .timer{display:flex;flex-direction:column;gap:8px;align-items:center}
    .timer .time{font-size:28px;font-weight:700;color:#fff}

    /* Error box */
    .error-box{margin-top:8px;padding:12px;border-radius:10px;background:rgba(229,62,62,0.09);border:1px solid rgba(229,62,62,0.12);color:#ffdede}
    .error-ok{background:rgba(39,174,96,0.06);border:1px solid rgba(39,174,96,0.12);color:#d7ffea;height: 25px}

    /* bottom task bar */
    .bottom {grid-column: 1 / span 3;display: flex;flex-direction: column;gap: 12px;margin-top: 12px}
    .task{flex:1;padding:14px;border-radius:12px;background:rgba(255,255,255,0.02);text-align:center}

    .stop-row{display:flex;gap:12px;align-items:center}
    .stop{flex:1;padding:14px;border-radius:10px;background:rgba(255,255,255,0.03);text-align:center}
    .e-stop{padding:12px 18px;border-radius:12px;background:linear-gradient(180deg,#e74b4b,#c33b3b);color:white;font-weight:700}

    .port-select {text-align: center}

    #gauge-imu {display: grid;grid-template-columns: repeat(3, auto)}
    #gauge-imu span {text-align: center}

    /* Leakage Sensor Color States */
    .leakage .g-value {padding: 8px;border-radius: 6px;background-color: #14532d;transition: background-color 0.3s;width: 100%;text-align: center}
    .leak-detected {background-color: #7f1d1d !important}

    input[type=range] {-webkit-appearance: none;width: 100%;height: 8px;border-radius: 5px;background: black;cursor: pointer;outline: none}
    input[type=range]::-webkit-slider-thumb {-webkit-appearance: none;appearance: none;width: 20px;height: 20px;background: #1e40af;border-radius: 50%;border: 2px solid #1e3a8a;cursor: pointer;position: relative;z-index: 1}
    input[type=range]::-moz-range-thumb {width: 20px;height: 20px;background: #1e40af;border-radius: 50%;border: 2px solid #1e3a8a;cursor: pointer;position: relative;z-index: 1}

    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button {-webkit-appearance: none;margin: 0}
    input[type=number] { -moz-appearance: textfield }

    .icon-container {
  display: flex;
  align-items: center;
  gap: 20px;
  justify-content: center;
  margin-top: 24px;
  z-index: 999;
  position: relative;
  transform: scale(1);  
  overflow: visible; 
   
 }
 


    .icon-container img {width: 60px;height: 60px;border-radius: 50%;object-fit: cover;padding: 6px;background: radial-gradient(circle, #444 60%, #111 100%);border:none;animation: pulseGlow 2s infinite ease-in-out;transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease}
    .icon-container img:hover {transform: scale(1.2) rotate(5deg);box-shadow: 0 0 25px white, 0 0 40px white;border-color: #1ff5f2}

    @keyframes pulseGlow {0%, 100% {box-shadow: 0 0 10px white} 50% {box-shadow: 0 0 25px white}}

    /* responsive */
    @media (max-width:980px){
      .grid{grid-template-columns:1fr}
      .bottom{flex-direction:column}
    }
    .compass-card {
      width: 300px;
      border-radius: 20px;
      padding: 18px;
      text-align: center;
      transform:translate(87px,-10px);
    }
    .compass {
      width: 250px;
      height: 250px;
      margin: 0 auto;
      display: block;
    }
    .heading {
      margin-top: 12px;
      font-size: 20px;
      letter-spacing: 0.4px;
    }
    .servo-control {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 20px;
      padding: 20px;
      background: #2b2b2b;
      border-radius: 15px;
      box-shadow: 0 4px 12px rgba(156, 156, 156, 0.4);
     }

    label {
      margin-bottom: 10px;
      font-size: 18px;
      color: #ffffff;
    }

    input[type=range] {
      -webkit-appearance: none;
      appearance: none;
      background: #d3d3d3;
      height: 6px;
      border-radius: 4px;
      outline: none;
      width: 350px;
      transform: translate(0px,8px);
    }

    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #333333;
      cursor: pointer;
      border: none;
      box-shadow: 0 0 6px rgba(255, 255, 255, 0.7);
    }

    input[type=range]::-moz-range-thumb {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: ;
      cursor: pointer;
      border: none;
      box-shadow: 0 0 6px rgba(255, 255, 255, 0.7);
    }

   

    .value {
      margin-top: 8px;
      margin-bottom: 0px;
      font-size: 16px;
      color: #ffffff;
      transform: translate(3px,10px);
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="grid">
      <!-- LEFT COLUMN -->
      <div class="panel">
        <h2 style="font-size: 30px;">Motors</h2>
        <div class="motors" id="motors-list"></div>

        <div class="left-bottom">
        <div style="display:grid;grid-template-columns: repeat(2, 1fr); gap: 10px; width:100%">
            <button class="btn" style="font-size: 20px;" id="motoron">Turn on All</button>
            <button class="btn" style="font-size: 20px;" id="motoroff">Stop All</button>
          </div>
          <div><h2 style="font-size: 30px;">Servo Motors</h2>
          <div class="servo-control">
    <label for="horizontal-range">Horizontal Servo</label>
    <input type="range" id="horizontal-range" min="0" max="180" value="90">
    <div class="value" id="horizontal-value">90°</div>
  </div>
  <div class="servo-control" >
    <label for="vertical-range">Vertical Servo</label>
    <input type="range" id="vertical-range" min="0" max="180" value="90">
    <div class="value" id="vertical-value">90°</div>
  </div>
          </div>
          <div class="joystick-wrap">
            <div class="joystick" id="joystick">
              <div class="stick" id="stick"></div>
            </div>
            <div class="port-select">
              <label style="color:rgb(187, 187, 187);font-size:17px;">Joystick Port</label>
              <div style="display:flex;gap:8px;align-items:center;transform:translate(0px,10px);">
                <select id="port" style="color:rgb(187, 187, 187);">
                  <option>COM1</option>
                  <option>COM2</option>
                  <option selected>COM3</option>
                  <option>COM4</option>
                </select>
                <div class="port-indicator"><div class="led" id="port-led" style="background-color: rgb(192, 19, 19);"></div><div style="color:rgb(187, 187, 187);font-size:17px" id="port-status">Disconnected</div></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CENTER -->
      <div class="panel video-area">
        <h2 style="font-size: 30px;">Video</h2>
        <div class="video" id="video">Video feed (placeholder)</div>
        <div class="controls" style="display:flex;flex-direction:column;gap:12px">
          <button class="btn" id="open-camera" style="font-size: 20px;">Open Camera</button>
          <div style="display:grid;grid-template-columns: repeat(2, 1fr); gap: 10px; width:100%">
            <button class="btn" style="font-size: 20px;">Camera 1</button>
            <button class="btn" style="font-size: 20px;">Camera 2</button>
          </div>
          <div class="timer panel" style="padding:12px;border-radius:10px;background:var(--glass);width:100%;height:170px">
            <div style="font-size:17px;color:rgb(187, 187, 187);">Timer</div>
            <div class="time" id="timer" style="font-size: 30px;">0.0</div>
            <div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap;justify-content:center">
              <button class="btn secondary" id="start" style="width: 160px;font-size: 20px;color:white;background:rgb(38, 37, 37);">Start</button>
              <button class="btn secondary" id="pause" style="width: 160px;font-size: 20px;color:white;background:rgb(38, 37, 37);">Pause</button>
              <button class="btn secondary" id="reset" style="width: 160px;font-size: 20px;color:white;background:rgb(38, 37, 37);">Reset</button>
            </div>
          </div>

          <div class="panel" style="padding:10px;background:rgba(255,255,255,0.02);width:100%;height:250px;margin-bottom:0">
            <h2 style="margin-bottom:8px;font-size:20px;">PID Control</h2>
            <div style="display:flex;flex-direction:column;gap:10px;transform:translate(0px,-10px)">
             <div style="display:flex;align-items:center;gap:5px;">
  <label style="width:18px;color:rgb(187, 187, 187);font-size:18px;">PID</label>
  <input type="number" id="pid-p" min="0" max="10" step="0.1" value="1"
       style="background-color:rgb(64, 64, 64); border:none;color:#fff;
              padding:4px 6px;border-radius:6px;font-size:18px;outline:none;
              text-align:center;width:90%;flex:0 0 auto;transform:translate(42px,0px)">
</div>

              <div style="display:flex;align-items:center;gap:8px;">
  <label style="width:18px;color:rgb(187, 187, 187);font-size:18px;">P</label>
  <input type="number" id="pid-p" min="0" max="10" step="0.1" value="1" 
         style="flex:0 0 auto;
                background-color:rgb(64, 64, 64); border:none;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:18px;
                outline:none;
                text-align:center;
                width:90%;transform:translate(40px,0px);">
</div>

      <div style="display:flex;align-items:center;gap:8px;">
        <label style="width:18px;color:rgb(187, 187, 187);font-size:18px;">I</label>
        <input type="number" id="pid-i" min="0" max="10" step="0.1" value="0" style="flex:0 0 auto;background-color:rgb(64, 64, 64); border:none;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:18px;
                outline:none;
                text-align:center;
                width:90%;transform:translate(40px,0px);">
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <label style="width:18px;color:rgb(187, 187, 187);font-size:18px;">D</label>
        <input type="number" id="pid-d" min="0" max="10" step="0.1" value="0" style="flex:0 0 auto;background-color:rgb(64, 64, 64); border:none;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:18px;
                outline:none;
                text-align:center;
                width:90%;transform:translate(40px,0px);">
      </div>
              <div style="display:flex;gap:10px;justify-content:center">
                <button class="btn" id="send-pid" style="width:160px;font-size:20px;">Send</button>
                <button class="btn" id="auto-pid" style="width:160px;font-size:20px;">Auto</button>
              </div>
            </div>
          </div>
        </div>

        <div class="icon-container" style="transform: translate(0px,40px)">
          <a href="http://localhost:8080/Ai"><img src="/static/artificial-intelligence.png"></a>
          <a href="http://localhost:8080/"><img src="/static/pilot%20(1).png"></a>
          <a href="http://localhost:8080/copilot">
  <img src="/static/pilot.png" alt="Pilot">
</a>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="panel">
        <h2 style="font-size: 30px;">Sensors</h2>
        <div class="sensors">
          <div class="gauge">
            <h3>Temperature</h3>
            <div class="g-value" id="temp">24°C</div>
          </div>

          <div class="gauge">
            <h3>Depth</h3>
            <div class="g-value" id="depth">0.0 m</div>
          </div>

          <div class="gauge imu">
            <h3>IMU Sensor</h3>
            <div class="compass-card">
    <svg id="compass" class="compass" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <!-- outer ring -->
      <circle cx="100" cy="100" r="94" fill="#0f0f0f" stroke="#222" stroke-width="4"/>

      <!-- needle group rotates -->
      <g id="needleGroup" transform="rotate(0 100 100)">
        <!-- north (red) -->
        <path d="M100 30 L110 100 L100 92 L90 100 Z" fill="#d94a4a" stroke="#b03b3b" stroke-width="0.7"/>
        <!-- south (blue) -->
        <path d="M100 170 L110 100 L100 108 L90 100 Z" fill="#3b88b0" stroke="#2c6b8a" stroke-width="0.7"/>
        <!-- center hub -->
        <circle cx="100" cy="100" r="6" fill="#333" stroke="#111" stroke-width="1.2"/>
      </g>

      <!-- compass cardinal letters -->
      <text x="100" y="22" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">N</text>
      <text x="178" y="105" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">E</text>
      <text x="100" y="190" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">S</text>
      <text x="22" y="105" text-anchor="middle" fill="#eee" font-size="14" font-weight="700">W</text>
    </svg>

  </div>
            <div class="g-value" id="gauge-imu">
              <span>Pitch: 0°</span>
              <span>Roll: 0°</span>
              <span>Yaw: 0°</span>
            </div>
          </div>

          <div class="gauge leakage">
            <h3>Leakage Sensor</h3>
            <div class="g-value" id="leakage-status">Safe</div>
          </div>
        </div>

        <div style="margin-top:12px">
          <h2 style="margin-top:0;font-size: 25px;">Error</h2>
          <div id="error" class="error-ok" style="font-size: 20px;">No Errors</div>
        </div>

        <div style="margin-top:18px" class="stop-row">
          <button class="stop" style="font-size: 20px;background:rgb(59, 57, 57);color: white;">Stop</button>
          <button class="e-stop" style="font-size: 20px;">Emergency Stop</button>
        </div>

        <div class="bottom">
          <button class="task" style="font-size: 20px;background:rgb(59, 57, 57);color: white;">Task 1</button>
          <button class="task" style="font-size: 20px;background:rgb(59, 57, 57);color: white;">Task 2</button>
          <button class="task" style="font-size: 20px;background:rgb(59, 57, 57);color: white;">Task 3</button>
        </div>
      </div>

    </div>
  </div>
  
</body>
</html>
    """

    ui.html(custom_html).classes('w-full')

    ui.add_body_html("""
     <script>
  window.addEventListener('load', () => {
    const motorsList = document.getElementById('motors-list');
  if (!motorsList) { console.error('motors-list not found'); }

  const maxValue = 255; 

  for (let i = 1; i <= 6; i++) {
    const m = document.createElement('div');
    m.className = 'motor';
    m.innerHTML = `
      <div class='led' id='led-${i}' style="transform:translate(-5px,0px);"></div>
      <label style="transform:translate(7px,0px);font-size: 20px;color:white;">Motor ${i}</label>
      <div class='speed'>
        <input type='number' min='0' max='${maxValue}' value='0' id='r-${i}' 
          style="background-color:rgb(64, 64, 64);  
          border:none;color:#fff;padding:4px 6px;border-radius:6px;font-size:20px;
          outline:none;text-align:center;transition:all 0.2s ease;width:110%">
      </div>`;
    motorsList.appendChild(m);
      const r = m.querySelector(`#r-${i}`);
      const v = m.querySelector(`#v-${i}`);
        const led = m.querySelector(`#led-${i}`);
  const input = m.querySelector(`#r-${i}`);
                     
                     input.addEventListener('input', () => {
    const val = parseInt(input.value) || 0;
    if (val > 0) {
      led.style.backgroundColor = 'limegreen';
    } else {
      led.style.backgroundColor = 'rgb(192, 19, 19)';
    }
  });
                     
      r.addEventListener('input', () => { if (v) v.textContent = r.value; });
    }
                     
    document.getElementById('motoron').addEventListener('click', () => {
    for (let i = 1; i <= 6; i++) {
      document.getElementById(`led-${i}`).style.backgroundColor = 'limegreen'; 
      document.getElementById(`r-${i}`).value = maxValue; 
    }
   });


  document.getElementById('motoroff').addEventListener('click', () => {
    for (let i = 1; i <= 6; i++) {
      document.getElementById(`led-${i}`).style.backgroundColor = 'rgb(192, 19, 19)';
      document.getElementById(`r-${i}`).value = 0;
    }
  });
      
  

  const horizontalRange = document.getElementById('horizontal-range');
    const verticalRange = document.getElementById('vertical-range');
    const horizontalValue = document.getElementById('horizontal-value');
    const verticalValue = document.getElementById('vertical-value');

    horizontalRange.addEventListener('input', () => {
      horizontalValue.textContent = horizontalRange.value + '°';
      console.log('Horizontal servo:', horizontalRange.value);
    });

    verticalRange.addEventListener('input', () => {
      verticalValue.textContent = verticalRange.value + '°';
      console.log('Vertical servo:', verticalRange.value);
    });
  


    const joystick = document.getElementById('joystick');
    const stick = document.getElementById('stick');
    const portSelect = document.getElementById('port');
    const portLed = document.getElementById('port-led');
    const portStatus = document.getElementById('port-status');

    if (portSelect && portLed && portStatus) {
      portSelect.addEventListener('change', () => {
        portLed.style.background = '#f59e0b';
        portStatus.textContent = 'Connecting...';
        setTimeout(() => { portLed.style.background = 'var(--success)'; portStatus.textContent = 'Connected'; }, 700);
      });
    }

    let dragging = false;
    if (joystick && stick) {
      joystick.addEventListener('pointerdown', e => { dragging = true; joystick.setPointerCapture(e.pointerId); });
      window.addEventListener('pointerup', () => { dragging = false; stick.style.transform = 'translate(-50%, -50%)'; });
      joystick.addEventListener('pointermove', e => {
        if (!dragging) return;
        const rect = joystick.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        const dx = Math.max(-48, Math.min(48, e.clientX - cx));
        const dy = Math.max(-48, Math.min(48, e.clientY - cy));
        stick.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
      });
    }


    let t = 0; let timerId = null; const timerEl = document.getElementById('timer');
    document.getElementById('start')?.addEventListener('click', () => {
      if (timerId) return;
      timerId = setInterval(() => { t += 0.1; if (timerEl) timerEl.textContent = t.toFixed(1); }, 100);
    });
    document.getElementById('pause')?.addEventListener('click', () => { clearInterval(timerId); timerId = null; });
    document.getElementById('reset')?.addEventListener('click', () => { clearInterval(timerId); timerId = null; t = 0; if (timerEl) timerEl.textContent = '0.0'; });

    document.getElementById('open-camera')?.addEventListener('click', () => {
      const v = document.getElementById('video');
      if (v) {
        v.textContent = '';
        v.style.background = 'linear-gradient(180deg,#00121a,#042231)';
      }
      const err = document.getElementById('error');
      if (err) { err.className = 'error-ok'; err.textContent = 'No Errors'; }
    });

    const temp = document.getElementById('temp');
    const depth = document.getElementById('depth');
    setInterval(() => {
      if (temp) temp.textContent = (20 + Math.round(Math.random() * 8)) + '°C';
      if (depth) depth.textContent = (Math.random() * 3).toFixed(1) + ' m';
    }, 2000);


    window.setROVError = function (msg) {
      const e = document.getElementById('error');
      if (!e) return;
      if (!msg) { e.className = 'error-ok'; e.textContent = 'No Errors'; }
      else { e.className = 'error-box'; e.textContent = msg; }
    };
  });
</script>

    """)
@ui.page('/Ai')
def Ai_page():
   
    custom_html = """
    <!doctype html>
<html lang="ar">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>ROV Control - Prototype</title>
  <style>
    :root{
      --bg:#071126;
      --panel:#0f2b45;
      --accent:#0ea5a4;
      --muted:#9fb0c4;
      --glass: rgba(255,255,255,0.04);
      --success:#27ae60;
      --danger:#e53e3e;
      --card-radius:14px;
      font-family: 'Segoe UI', Tahoma, system-ui, Arial, sans-serif;
    }
    *{box-sizing:border-box}
html, body {
  height: 100%;
  margin: 0;
  background-image: url("/static/background.jpg");
  background-size: cover;      
  background-position: center; 
  background-repeat: no-repeat; 
  color: #dbeafe;}
    .app{max-width:1200px;margin:24px auto;padding:20px;}
body {
  overflow: hidden;
  }
    /* Main layout */
    .grid{display:grid;grid-template-columns: 700px 1fr 300px;gap:100px}
    .panel{background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);background: linear-gradient(180deg, var(--bg) 0%, #0d1b2a 100%); padding:18px;border-radius:var(--card-radius);box-shadow:0 4px 18px rgba(2,6,23,0.6);border:1px solid rgba(255,255,255,0.03);width: 110%;}
    h2{margin:0 0 12px 0;font-weight:600;color:#e6f0ff}

    /* Motors panel */
    .motors{display:flex;flex-direction:column;gap:12px}
    .motor{display:flex;align-items:center;gap:12px;padding:10px;border-radius:10px;background:var(--glass)}
    .led{width:14px;height:14px;border-radius:50%;background:var(--success);box-shadow:0 0 8px rgba(39,174,96,0.35)}
    .motor label{flex:1;font-size:15px;color:#cfe8ff}
    .speed{width:110px;display:flex;gap:8px;align-items:center}
    input[type=range]{accent-color:var(--accent);width:100%}
    .speed-value{width:26px;text-align:center;color:var(--muted)}

    /* Joystick area */
    .left-bottom{display:flex;flex-direction:column;gap:12px;margin-top:10px}
    .joystick-wrap{display:flex;gap:12px;align-items:center}
    .joystick{width:140px;height:140px;border-radius:50%;background:radial-gradient(circle at 30% 30%, rgba(255,255,255,0.02), transparent 30%), rgba(255,255,255,0.01);display:flex;align-items:center;justify-content:center;position:relative}
    .stick{width:44px;height:44px;border-radius:50%;background:linear-gradient(180deg,#0f3b57,#083142);box-shadow:inset 0 2px 6px rgba(255,255,255,0.03),0 6px 20px rgba(2,6,23,0.6);transform:translate(0,0)}
    .port-select{display:flex;flex-direction:column;gap:8px}
    select, button{padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:var(--muted)}
    .port-indicator{display:flex;align-items:center;gap:8px}
    .port-indicator .led{width:12px;height:12px}

    /* center video */
    .video-area{display:flex;flex-direction:column;gap:10px;align-items:center;}
    .video{width:100%;height:360px;background:linear-gradient(180deg,#021323,#000000);border-radius:10px;border:1px solid rgba(255,255,255,0.03);display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.08);font-size:18px;transform: translate(0px,-2px);}
    .controls{width:100%;display:flex;gap:12px;justify-content:center}
    .btn{padding:5px 5px;border-radius:10px;border:none;background:#123548;color:#e8f7ff;cursor:pointer;width: 100%;height: 50px;font-size: 15px;}
    .btn.secondary{background:rgba(255,255,255,0.03);color:var(--muted)}

    /* right column */
    .sensors{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .gauge{padding:12px;border-radius:10px;background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent)}
    .gauge h3{margin:0 0 6px 0;font-size:13px;color:var(--muted)}
    .g-value{font-size:20px;font-weight:700}

    .timer{display:flex;flex-direction:column;gap:8px;align-items:center}
    .timer .time{font-size:28px;font-weight:700;color:#fff}

    /* Error box */
    .error-box{margin-top:8px;padding:12px;border-radius:10px;background:rgba(229,62,62,0.09);border:1px solid rgba(229,62,62,0.12);color:#ffdede}
    .error-ok{background:rgba(39,174,96,0.06);border:1px solid rgba(39,174,96,0.12);color:#d7ffea;height: 25px;}

    /* bottom task bar */
.bottom {
  grid-column: 1 / span 3;
  display: flex;
  flex-direction: column; 
  gap: 12px;
  margin-top: 12px;
}
    .task{flex:1;padding:14px;border-radius:12px;background:rgba(255,255,255,0.02);text-align:center}

    .stop-row{display:flex;gap:12px;align-items:center}
    .stop{flex:1;padding:14px;border-radius:10px;background:rgba(255,255,255,0.03);text-align:center}
    .e-stop{padding:12px 18px;border-radius:12px;background:linear-gradient(180deg,#e74b4b,#c33b3b);color:white;font-weight:700}
  .joystick-wrap {
  display: flex;
  flex-direction: column; 
  align-items: center; 
  gap: 16px; 
  margin-top: 10px;
}

.joystick {
  width: 150px;
  height: 150px;
  background: #0b3b54;
  border-radius: 50%;
  position: relative;
}

.stick {
  width: 50px;
  height: 50px;
  background: #e8f7ff;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.port-select {
  text-align: center;
}

#gauge-imu {
  display: grid;
  grid-template-columns: repeat(3, auto); 
}

#gauge-imu span {
  text-align: center;
}

/* Leakage Sensor Color States */
.leakage .g-value {
  padding: 8px;
  border-radius: 6px;
  background-color: #14532d; 
  transition: background-color 0.3s;
  width: 100%;
  text-align: center;
}

/* Leak Detected */
.leak-detected {
  background-color: #7f1d1d !important;
}

input[type=range] {
  -webkit-appearance: none;
  width: 100%;
  height: 8px;
  border-radius: 5px;
  background: black; 
  cursor: pointer;
  outline: none;
}

input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 15px;
  height: 15px;
  background: #1e40af;
  border-radius: 50%;
  border: 2px solid #1e3a8a;
  cursor: pointer;
  margin-top: -1px; 
  position: relative;
  z-index: 1;
}

input[type=range]::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #1e40af;
  border-radius: 50%;
  border: 2px solid #1e3a8a;
  cursor: pointer;
  position: relative;
  z-index: 1;
}
.panel::-webkit-scrollbar {
  display: none;
}





    /* responsive */
    @media (max-width:980px){.grid{grid-template-columns:1fr;}.bottom{flex-direction:column}}
  </style>
</head>
<body>
  <div class="app" style="transform: translate(-75px,-20px);">
    <div class="grid">
      <!-- LEFT COLUMN -->
      

      <!-- CENTER -->
      <div style="display:flex; flex-direction:column; gap:20px;">

 
    <div class="panel video-area" style="height: 550px;">
      <img src="/video_feed" 
     style="width:100%;height:400px; object-fit:cover; border-radius:10px;">
      <div class="controls" style="display:flex;flex-direction:column;gap:12px">
        <button class="btn" id="open-camera">Take screenshot</button>
        <div style="display: grid; grid-template-columns: repeat(2, auto); gap: 10px;">
          <button class="btn" id="cam1" style="width: 100%;">Camera 1</button>
          <button class="btn" id="cam2" style="width: 100%;">Camera 2</button>  
        </div>
      </div>
    </div>

    <div class="panel" style="width: 770px; height: 230px;">
      <div class="timer panel" style="
          padding:12px;
          border-radius:10px;
          background:rgba(255,255,255,0.01);
          width:100%;
          display: grid;
          grid-template-columns: 1fr 2fr;
          gap: 20px;
          align-items: center;
      ">
        <div class="tasks" style="display:flex;flex-direction:column;gap:10px;">
          <div class="task">Task 1</div>
          <div class="task">Task 2</div>
          <div class="task">Task 3</div>
        </div>

   
        <div>
          <div style="font-size:18px;color:var(--muted); text-align:center;">Timer</div>
          <div class="time" id="timer" style="font-size:26px;margin:10px 0; text-align:center;">0.0</div>
          <div style="display:flex;gap:8px; margin-top:20px;">
            <button class="btn secondary" id="start" style="flex:1;">Start</button>
            <button class="btn secondary" id="pause" style="flex:1;">Pause</button>
            <button class="btn secondary" id="reset" style="flex:1;">Reset</button>
          </div>
        </div>
      </div>
    </div>

  </div>

  
      <div class="panel" style="width: 500px; height: 800px; overflow-y: auto;scrollbar-width: none; -ms-overflow-style: none;">
        <div class="video" id="video1" style="height: 300px;"></div>
        <div class="video" id="video2" style="margin-top: 5px;height: 300px;"></div>
        <div class="video" id="video3" style="margin-top: 5px;height: 300px;"></div>
      </div>

      
    </div>
  </div>
</body>
</html>
    """

    ui.html(custom_html).classes('w-full')

    ui.add_body_html("""
    <script>
window.addEventListener('DOMContentLoaded', () => {
  let t = 0;
  let timerId = null;
  const timerEl = document.getElementById('timer');

  document.getElementById('start').addEventListener('click', () => {
    if (timerId) return;
    timerId = setInterval(() => {
      t += 0.1;
      timerEl.textContent = t.toFixed(1);
    }, 100);
  });

  document.getElementById("cam1").addEventListener("click", function() {
    fetch("/set_camera/0");
});
document.getElementById("cam2").addEventListener("click", function() {
    fetch("/set_camera/1");
});
  document.getElementById('pause').addEventListener('click', () => {
    clearInterval(timerId);
    timerId = null;
  });

  document.getElementById('reset').addEventListener('click', () => {
    clearInterval(timerId);
    timerId = null;
    t = 0;
    timerEl.textContent = '0.0';
  });
                     let currentDiv = 0;
    const divs = ["video1", "video2", "video3"];

    document.getElementById("open-camera").addEventListener("click", async () => {
        const response = await fetch("/screenshot?" + new Date().getTime()); 
        const blob = await response.blob();
        const imgURL = URL.createObjectURL(blob);

        const targetDiv = divs[currentDiv];
        document.getElementById(targetDiv).innerHTML = 
            `<img src="${imgURL}" style="width:100%; height:100%; object-fit:cover; border-radius:10px;">`;

        currentDiv = (currentDiv + 1) % divs.length;
    });
});
                     
</script>

    """)

latest_frame = None
camera_index = 0   

def capture_loop():
    global latest_frame, camera_index
    cap = None
    last_index = -1
    while True:
     
        if camera_index != last_index:
            if cap is not None:
                cap.release()
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            last_index = camera_index

        if cap is None or not cap.isOpened():
            continue

        ok, frame = cap.read()
        if ok:
            latest_frame = frame
        else:
            latest_frame = None

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

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/set_camera/{index}")
def set_camera(index: int):
    global camera_index
    camera_index = index
    return {"status": "ok", "camera_index": camera_index}
@app.get('/screenshot')
def screenshot():
    global latest_frame
    if latest_frame is None:
        return {"error": "Frame not Found"}
    ok, buffer = cv2.imencode('.jpg', latest_frame)
    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg"
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host='0.0.0.0', port=8080, reload=False)
