import subprocess
import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

# Set explicit path to adb executable
ADB_PATH = r"C:\platform-tools\adb.exe"

app = FastAPI()

# --- 1. Real-time Android Screen Streamer ---
def generate_mobile_stream():
    while True:
        try:
            # Capture real-time JPEG from Android via ADB
            process = subprocess.Popen(
                [ADB_PATH, "exec-out", "screencap", "-p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            frame_data = process.stdout.read()
            if frame_data and len(frame_data) > 1000:
                yield (b'--frame\r\n'
                       b'Content-Type: image/png\r\n\r\n' + frame_data + b'\r\n')
        except Exception as e:
            pass
        time.sleep(0.05)

@app.get("/mobile-feed")
def mobile_feed():
    return StreamingResponse(
        generate_mobile_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# --- 2. Android Control Endpoints ---
@app.post("/api/tap")
async def handle_tap(request: Request):
    data = await request.json()
    x, y = data.get("x"), data.get("y")
    subprocess.run([ADB_PATH, "shell", "input", "tap", str(x), str(y)])
    return {"status": "ok"}

@app.post("/api/swipe")
async def handle_swipe(request: Request):
    data = await request.json()
    x1, y1 = data.get("x1"), data.get("y1")
    x2, y2 = data.get("x2"), data.get("y2")
    duration = data.get("duration", 300)
    subprocess.run([ADB_PATH, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
    return {"status": "ok"}

@app.post("/api/key")
async def handle_key(request: Request):
    data = await request.json()
    keycode = data.get("keycode")
    subprocess.run([ADB_PATH, "shell", "input", "keyevent", str(keycode)])
    return {"status": "ok"}

@app.post("/api/text")
async def handle_text(request: Request):
    data = await request.json()
    text = data.get("text", "")
    escaped_text = text.replace(" ", "%s")
    subprocess.run([ADB_PATH, "shell", "input", "text", escaped_text])
    return {"status": "ok"}

# --- 3. Interactive Web Dashboard ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Custom Phone Remote</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: #0f172a; color: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        
        .viewer-pane { flex: 1; display: flex; justify-content: center; align-items: center; background: #020617; padding: 10px; position: relative; }
        #screen { max-height: 95vh; max-width: 100%; border-radius: 12px; border: 2px solid #38bdf8; cursor: pointer; display: block; object-fit: contain; }
        
        .controls-pane { width: 320px; background: #1e293b; padding: 20px; display: flex; flex-direction: column; gap: 15px; border-left: 1px solid #334155; }
        h2 { font-size: 14px; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; }
        
        .btn-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
        .btn { padding: 12px; font-size: 13px; font-weight: bold; background: #334155; color: #fff; border: none; border-radius: 6px; cursor: pointer; transition: 0.1s; }
        .btn:hover { background: #475569; }
        .btn:active { background: #0284c7; }
        
        .input-box { display: flex; flex-direction: column; gap: 8px; }
        input[type="text"] { padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; outline: none; }
        .send-btn { padding: 10px; background: #0284c7; border: none; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; }
        
        .tip { font-size: 12px; color: #94a3b8; line-height: 1.4; }
    </style>
</head>
<body>
    <div class="viewer-pane">
        <img id="screen" src="/mobile-feed" alt="Connecting to Phone Screen..." />
    </div>

    <div class="controls-pane">
        <h2>Android Navigation</h2>
        <div class="btn-grid">
            <button class="btn" onclick="sendKey(4)">◀ Back</button>
            <button class="btn" onclick="sendKey(3)">● Home</button>
            <button class="btn" onclick="sendKey(187)">■ Apps</button>
        </div>

        <h2>Volume & Power</h2>
        <div class="btn-grid">
            <button class="btn" onclick="sendKey(24)">Vol +</button>
            <button class="btn" onclick="sendKey(25)">Vol -</button>
            <button class="btn" onclick="sendKey(26)">Power</button>
        </div>

        <h2>Type to Phone</h2>
        <div class="input-box">
            <input type="text" id="phoneTextInput" placeholder="Type text here..." onkeydown="if(event.key==='Enter') sendText()" />
            <button class="send-btn" onclick="sendText()">Send Text</button>
        </div>

        <p class="tip">
            • <b>Click</b> anywhere on the screen to tap apps.<br>
            • <b>Click & drag</b> to swipe or scroll pages.<br>
        </p>
    </div>

    <script>
        const screenImg = document.getElementById('screen');
        let startX = 0, startY = 0, isDragging = false;

        function getPhoneCoords(e) {
            const rect = screenImg.getBoundingClientRect();
            const normX = (e.clientX - rect.left) / rect.width;
            const normY = (e.clientY - rect.top) / rect.height;
            return {
                x: Math.round(normX * 1080),
                y: Math.round(normY * 2400)
            };
        }

        screenImg.addEventListener('mousedown', (e) => {
            isDragging = true;
            const coords = getPhoneCoords(e);
            startX = coords.x;
            startY = coords.y;
        });

        screenImg.addEventListener('mouseup', (e) => {
            if (!isDragging) return;
            isDragging = false;
            const coords = getPhoneCoords(e);
            
            const distance = Math.hypot(coords.x - startX, coords.y - startY);
            if (distance < 20) {
                fetch('/api/tap', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ x: coords.x, y: coords.y })
                });
            } else {
                fetch('/api/swipe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ x1: startX, y1: startY, x2: coords.x, y2: coords.y, duration: 300 })
                });
            }
        });

        function sendKey(keycode) {
            fetch('/api/key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keycode })
            });
        }

        function sendText() {
            const input = document.getElementById('phoneTextInput');
            if (!input.value) return;
            fetch('/api/text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: input.value })
            });
            input.value = '';
        }
    </script>
</body>
</html>
"""

@app.get("/")
def home():
    return HTMLResponse(content=HTML_INTERFACE)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)