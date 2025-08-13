from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
import sys
from PyQt5.QtCore import QUrl
import os , base64

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROV RoboTech GUI")
        self.resize(800, 600)
        
        self.webview = QWebEngineView()
        self.setCentralWidget(self.webview)
        html_code = """
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
  background-image: url("background.jpg");
  background-size: cover;       
  background-position: center;  
  background-repeat: no-repeat; 
  color: #dbeafe;}
  body {
  overflow: hidden;
}
    .app{max-width:1600px;margin:20px auto;margin-left:200px;padding:20px;}

    /* Main layout */
    .grid{display:grid;grid-template-columns: 320px 1fr 300px;gap:18px}
    .panel{background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);background: linear-gradient(180deg, var(--bg) 0%, #0d1b2a 100%); padding:20px;border-radius:var(--card-radius);box-shadow:0 4px 18px rgba(2,6,23,0.6);border:1px solid rgba(255,255,255,0.03);width:110%;height:108%}
    h2{margin:0 0 12px 0;font-weight:600;color:#e6f0ff}

    /* Motors panel */
    .motors{display:flex;flex-direction:column;gap:12px}
    .motor{display:flex;align-items:center;gap:12px;padding:10px;border-radius:10px;background:var(--glass);transform:translate(0px,10px)}
    .led{width:14px;height:14px;border-radius:50%;background:var(--success);box-shadow:0 0 8px rgba(39,174,96,0.35)}
    .motor label{flex:1;font-size:15px;color:#cfe8ff}
    .speed{width:110px;display:flex;gap:8px;align-items:center}
    input[type=range]{accent-color:var(--accent);width:100%}
    .speed-value{width:26px;text-align:center;color:var(--muted)}

    /* Joystick area */
    .left-bottom{display:flex;flex-direction:column;gap:12px;margin-top:10px}
    .joystick-wrap{display:flex;gap:12px;align-items:center}
    .joystick {
  position: relative; 
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.02), transparent 30%), rgba(255,255,255,0.01);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stick {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(180deg,#0f3b57,#083142);
  box-shadow: inset 0 2px 6px rgba(255,255,255,0.03), 0 6px 20px rgba(2,6,23,0.6);
  transform: translate(-50%, -50%);
}

    select, button{padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:var(--muted)}
    .port-indicator{display:flex;align-items:center;gap:8px}
    .port-indicator .led{width:12px;height:12px}

    /* center video */
    .video-area{display:flex;flex-direction:column;gap:10px;align-items:center;}
    .video{width:100%;height:380px;background:linear-gradient(180deg,#021323,#000000);border-radius:10px;border:1px solid rgba(255,255,255,0.03);display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.08);font-size:18px;transform: translate(0px,-2px);}
    .controls{width:100%;display:flex;gap:12px;justify-content:center}
    .btn{padding:3px 3px;border-radius:10px;border:none;background:#123548;color:#e8f7ff;cursor:pointer;width: 100%;height: 60px;font-size: 18px;}
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
  background-color: #14532d; /* Safe (green) */
  transition: background-color 0.3s;
  width: 100%;
  text-align: center;
}

/* Leak Detected */
.leak-detected {
  background-color: #7f1d1d !important; /* Red alert */
}
.motor {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 10px;
  background: var(--glass);
  margin-top: 10px; /* مسافة فعلية بين الموترات */
  gap: 12px;

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
  width: 20px;
  height: 20px;
  background: #1e40af;
  border-radius: 50%;
  border: 2px solid #1e3a8a;
  cursor: pointer;
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

input[type=number]::-webkit-inner-spin-button,
  input[type=number]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  input[type=number] {
    -moz-appearance: textfield;
  }

    /* responsive */
    @media (max-width:980px){.grid{grid-template-columns:1fr;}.bottom{flex-direction:column}}
  </style>
</head>
<body>
  <div class="app" style="transform: translate(-80px,-20px);">
    <div class="grid">
      <!-- LEFT COLUMN -->
      <div class="panel" style="transform:translate(-40px,0px)">
        <h2>Motors</h2>
        <div class="motors" id="motors-list">
        </div>

        <div class="left-bottom">
          <div class="joystick-wrap" style="transform: translate(0px,200px)">
            <div class="joystick" id="joystick">
              <div class="stick" id="stick"></div>
            </div>
            <div class="port-select">
              <label style="color:var(--muted);font-size:13px;margin-bottom:20px;margin-top:20px">Joystick Port</label>
              <div style="display:flex;gap:8px;align-items:center;transform: translate(-30px,0px)">
                <select id="port">
                  <option>COM1</option>
                  <option>COM2</option>
                  <option selected>COM3</option>
                  <option>COM4</option>
                </select>
                <div class="port-indicator" style="transform: translate(20px,0px)"><div class="led" id="port-led" style="background-color: rgb(192, 19, 19);"></div><div style="color:var(--muted);font-size:13px;transform: translate(8px,0px)" id="port-status">Disconnected</div></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CENTER -->
      <div class="panel video-area">
                <!-- <img src="./Adobe Express - file.png" alt="" width="160px" style="transform: translate(0px,-60px);"> -->
        <h2 >Video</h2>
        <div class="video" id="video" style="transform:translate(0px,10px)">Video feed (placeholder)</div>
        <div class="controls" style="display:flex;flex-direction:column;gap:12px">
    <button class="btn" id="open-camera" style="height:80px;transform:translate(0px,20px)">Open Camera</button>
    <div style="display: grid;
  grid-template-columns: repeat(2, auto); gap: 10px;transform:translate(0px,30px)">
      <button class="btn" style="width: 100%;height:50px">Camera 1</button>
      <button class="btn" style="width: 100%;height:50px">Camera 2</button>
    </div>
    <div class="timer panel" style="padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);width:100%;transform: translate(0px,50px);height:150px">
        <div style="font-size:12px;color:var(--muted)">Timer</div>
        <div class="time" id="timer">0.0</div>
        <div style="display:flex;gap:8px;margin-top:6px">
            <button class="btn secondary" id="start" style="width: 200px;transform:translate(-10px,0px)">Start</button>
            <button class="btn secondary" id="pause"style="width: 200px;">Pause</button>
            <button class="btn secondary" id="reset"style="width: 200px;transform:translate(10px,0px)">Reset</button>
        </div>
    </div>
      <div class="panel" style="padding: 10px; background: rgba(255,255,255,0.02); width: 100%; transform: translate(0px,70px);height:110%">
    <h2 style="margin-bottom: 8px; font-size: 18px;">PID Control</h2>
    <div style="display: flex; flex-direction: column; gap: 6px;">
      <div style="display:flex;align-items:center;gap:8px;">
  <label style="width:18px;color:var(--muted);font-size:16px;">P</label>
  <input type="number" id="pid-p" min="0" max="10" step="0.1" value="1" 
         style="flex:1;
                background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:16px;
                outline:none;
                text-align:center;
                transition:all 0.2s ease;">
</div>

      <div style="display:flex;align-items:center;gap:8px;transform:translate(0px,10px)">
        <label style="width:18px;color:var(--muted);font-size:16px;">I</label>
        <input type="number" id="pid-i" min="0" max="10" step="0.1" value="0" style="flex:1;background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:16px;
                outline:none;
                text-align:center;
                transition:all 0.2s ease;">
      </div>
      <div style="display:flex;align-items:center;gap:8px;transform:translate(0px,20px)">
        <label style="width:18px;color:var(--muted);font-size:16px;">D</label>
        <input type="number" id="pid-d" min="0" max="10" step="0.1" value="0" style="flex:1;background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:16px;
                outline:none;
                text-align:center;
                transition:all 0.2s ease;">
      </div>
      <button class="btn" id="send-pid" style="padding:4px 6px;font-size:18px;height:40px;transform:translate(5px,30px)">Send</button>
            <button class="btn" id="send-pid" style="padding:4px 6px;font-size:18px;height:40px;transform:translate(5px,40px)">Auto</button>
    </div>
  </div>
</div>

      </div>

      <!-- RIGHT COLUMN -->
      <div class="panel" style="transform:translate(100px,0px)">
        <h2>Sensors</h2>
        <div class="sensors">
  <div class="gauge">
    <h3>Temperature</h3>
    <div class="g-value" id="temp">24°C</div>
  </div>

  <div class="gauge">
    <h3>Depth</h3>
    <div class="g-value" id="depth">0.0 m</div>
  </div>

  <div class="gauge" style="width: 170%;">
    <h3>IMU Sensor</h3>
    <div class="g-value" id="gauge-imu">
      <span>Pitch: 0°</span>
      <span>Roll: 0°</span>
      <span>Yaw: 0°</span>
    </div>
  </div>
  <div></div>
  <div class="gauge leakage">
    <h3>Leakage Sensor</h3>
    <div class="g-value" id="leakage-status">Safe</div>
  </div>
</div>



        <div style="margin-top:12px">
          <h2 style="margin-top:0">Error</h2>
          <div id="error" class="error-ok">No Errors</div>
        </div>

        <div style="margin-top:18px" class="stop-row">
          <div class="stop">Stop</div>
          <div class="e-stop">Emergency Stop</div>
        </div>

        <div class="bottom">
        <div class="task">Task 1</div>
        <div class="task"style="transform:translate(0px,10px)">Task 2</div>
        <div class="task"style="transform:translate(0px,20px)">Task 3</div>
      </div>
      </div>

      <!-- bottom tasks -->
      
    </div>
  </div>

  <script>
    // --- Build motors list (6 motors) ---
    const motorsList = document.getElementById('motors-list');
    for(let i=1;i<=6;i++){
      const m = document.createElement('div'); m.className='motor';
      m.innerHTML = `<div class='led' id='led-${i}' style="transform:translate(-5px,0px);"></div><label style="transform:translate(7px,0px)">Motor ${i}</label><div class='speed'><input type='number' min='0' max='255' value='0' id='r-${i}' style="background-color:#0f2b45;
                border:1px solid #1f4b75;
                color:#fff;
                padding:4px 6px;
                border-radius:6px;
                font-size:16px;
                outline:none;
                text-align:center;
                transition:all 0.2s ease;width:110%"></div>`;
      motorsList.appendChild(m);
      // update value display
      const r = m.querySelector(`#r-${i}`);
      const v = m.querySelector(`#v-${i}`);
      r.addEventListener('input', ()=> v.textContent = r.value);
    }

    // joystick simple interaction (visual only)
    const joystick = document.getElementById('joystick');
    const stick = document.getElementById('stick');
    const portSelect = document.getElementById('port');
    const portLed = document.getElementById('port-led');
    const portStatus = document.getElementById('port-status');
    const portSelected = document.getElementById('port-selected');

    portSelect.addEventListener('change', ()=>{
      portSelected.textContent = portSelect.value;
      portLed.style.background = '#f59e0b';
      portStatus.textContent = 'Connecting...';
      setTimeout(()=>{portLed.style.background='var(--success)';portStatus.textContent='Connected'},700);
    });

    let dragging = false;
    joystick.addEventListener('pointerdown', (e)=>{dragging=true;joystick.setPointerCapture(e.pointerId)});
    window.addEventListener('pointerup', (e)=>{dragging=false;stick.style.transform='translate(-22px,-22px)';});
    joystick.addEventListener('pointermove',(e)=>{
      if(!dragging) return;
      const rect = joystick.getBoundingClientRect();
      const cx = rect.left + rect.width/2; const cy = rect.top + rect.height/2;
      const dx = Math.max(-48, Math.min(48, e.clientX - cx));
      const dy = Math.max(-48, Math.min(48, e.clientY - cy));
      stick.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
      // here you could send dx,dy values to backend
    });

    // timer
    let t = 0; let timerId=null; const timerEl = document.getElementById('timer');
    document.getElementById('start').addEventListener('click', ()=>{
      if(timerId) return; timerId = setInterval(()=>{t += 0.1; timerEl.textContent = t.toFixed(1)},100);
    });
    document.getElementById('pause').addEventListener('click', ()=>{clearInterval(timerId); timerId=null});
    document.getElementById('reset').addEventListener('click', ()=>{clearInterval(timerId);timerId=null; t=0; timerEl.textContent='0.0'});

    // open camera (placeholder) and error simulation
    document.getElementById('open-camera').addEventListener('click', ()=>{
      const v = document.getElementById('video');
      v.textContent = '';
      v.style.background = 'linear-gradient(180deg,#00121a,#042231)';
      // in real app you'd start video stream here
      const err = document.getElementById('error'); err.className='error-ok'; err.textContent='No Errors';
    });

    // demo: simulate sensor updates
    const temp = document.getElementById('temp'); const depth = document.getElementById('depth');
    setInterval(()=>{
      const tv = 20 + Math.round(Math.random()*8);
      const dv = (Math.random()*3).toFixed(1);
      temp.textContent = tv + '°C'; depth.textContent = dv + ' m';
    },2000);

    // expose a function to set an error (for backend integration)
    window.setROVError = function(msg){
      const e = document.getElementById('error');
      if(!msg){ e.className='error-ok'; e.textContent='No Errors'; }
      else { e.className='error-box'; e.textContent = msg; }
    }

        document.querySelectorAll('input[type=range]').forEach(slider => {
  const max = slider.max;

  function updateBackground() {
    const val = slider.value;
    const percent = (val / max) * 100;
    slider.style.background = `linear-gradient(to right, #1e40af 0%, #1e40af ${percent}%, black ${percent}%, black 100%)`;
  }

  slider.addEventListener('input', updateBackground);


  updateBackground();
});

    
  </script>
</body>
</html>
        """
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.webview.setHtml(html_code, QUrl.fromLocalFile(base_path + os.sep))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())


