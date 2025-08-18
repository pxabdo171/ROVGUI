from fastapi import Request
from nicegui import ui, app
import os

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
 


    .icon-container img {width: 60px;height: 60px;border-radius: 50%;object-fit: cover;padding: 6px;background: radial-gradient(circle, #0f2b45 70%, #123548 100%);border: 2px solid #0ea5a4;animation: pulseGlow 2s infinite ease-in-out;transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease}
    .icon-container img:hover {transform: scale(1.2) rotate(5deg);box-shadow: 0 0 25px rgba(14, 165, 164, 0.9), 0 0 40px rgba(14, 165, 164, 0.6);border-color: #1ff5f2}

    @keyframes pulseGlow {0%, 100% {box-shadow: 0 0 10px rgba(14, 165, 164, 0.5)} 50% {box-shadow: 0 0 25px rgba(14, 165, 164, 0.9)}}

    /* responsive */
    @media (max-width:980px){
      .grid{grid-template-columns:1fr}
      .bottom{flex-direction:column}
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
          <div class="joystick-wrap" style="transform:translate(0px,100px);">
            <div class="joystick" id="joystick">
              <div class="stick" id="stick"></div>
            </div>
            <div class="port-select">
              <label style="color:var(--muted);font-size:17px">Joystick Port</label>
              <div style="display:flex;gap:8px;align-items:center;transform:translate(0px,10px);">
                <select id="port">
                  <option>COM1</option>
                  <option>COM2</option>
                  <option selected>COM3</option>
                  <option>COM4</option>
                </select>
                <div class="port-indicator"><div class="led" id="port-led" style="background-color: rgb(192, 19, 19);"></div><div style="color:var(--muted);font-size:17px" id="port-status">Disconnected</div></div>
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
            <h2 style="margin-bottom:8px;font-size:20px;">PID Control</h2>
            <div style="display:flex;flex-direction:column;gap:10px;transform:translate(0px,-10px)">
             <div style="display:flex;align-items:center;gap:5px;">
  <label style="width:18px;color:var(--muted);font-size:18px;">PID</label>
  <input type="number" id="pid-p" min="0" max="10" step="0.1" value="1"
       style="background-color:#0f2b45;border:1px solid #1f4b75;color:#fff;
              padding:4px 6px;border-radius:6px;font-size:18px;outline:none;
              text-align:center;width:90%;flex:0 0 auto;transform:translate(42px,0px)">
</div>

              <div style="display:flex;align-items:center;gap:8px;">
  <label style="width:18px;color:var(--muted);font-size:18px;">P</label>
  <input type="number" id="pid-p" min="0" max="10" step="0.1" value="1" 
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
              <div style="display:flex;gap:10px;justify-content:center">
                <button class="btn" id="send-pid" style="width:160px;font-size:20px;">Send</button>
                <button class="btn" id="auto-pid" style="width:160px;font-size:20px;">Auto</button>
              </div>
            </div>
          </div>
        </div>

        <div class="icon-container" style="transform: translate(0px,40px)">
          <img src="/static/artificial-intelligence.png">
          <img src="/static/pilot%20(1).png">
          <img src="/static/pilot.png">
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
          <button class="stop" style="font-size: 20px;">Stop</button>
          <button class="e-stop" style="font-size: 20px;">Emergency Stop</button>
        </div>

        <div class="bottom">
          <button class="task" style="font-size: 20px;">Task 1</button>
          <button class="task" style="font-size: 20px;">Task 2</button>
          <button class="task" style="font-size: 20px;">Task 3</button>
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

if __name__ == '__main__':
    ui.run(host='0.0.0.0', port=8080, reload=False)
