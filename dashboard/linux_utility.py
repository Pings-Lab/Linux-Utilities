"""
FastAPI-based Mini System Dashboard for Linux (Ubuntu & others)
---------------------------------------------------------------
Features:
- Modern Bento-style UI (HTML + CSS)
- Hostname, Username
- Live network speed (WiFi/Ethernet)
- Pie charts for CPU, Memory, Disk usage
- List of open ports with owning process
- Extra: system uptime & load average

Run:
  pip install fastapi uvicorn psutil jinja2
  sudo python dashboard.py   (sudo needed for open ports)

Open browser:
  http://127.0.0.1:8000
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import psutil
import socket
import getpass
import time
import shutil
import subprocess

app = FastAPI(title="Linux Mini Dashboard")

BOOT_TIME = psutil.boot_time()
NET_IO_PREV = psutil.net_io_counters()
NET_TIME_PREV = time.time()

# ---------------- SYSTEM DATA ---------------- #

def get_network_speed():
    global NET_IO_PREV, NET_TIME_PREV
    now = time.time()
    net = psutil.net_io_counters()
    interval = now - NET_TIME_PREV

    sent = (net.bytes_sent - NET_IO_PREV.bytes_sent) / interval
    recv = (net.bytes_recv - NET_IO_PREV.bytes_recv) / interval

    NET_IO_PREV = net
    NET_TIME_PREV = now

    return {
        "upload_kbps": round(sent / 1024, 2),
        "download_kbps": round(recv / 1024, 2)
    }


def get_open_ports():
    ports = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == psutil.CONN_LISTEN:
            try:
                proc = psutil.Process(conn.pid).name() if conn.pid else "-"
            except Exception:
                proc = "unknown"
            ports.append({
                "port": conn.laddr.port,
                "process": proc
            })
    return ports


# ---------------- API ---------------- #

@app.get("/api/stats")
def stats():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    return JSONResponse({
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "cpu": cpu,
        "memory": mem.percent,
        "disk": round((disk.used / disk.total) * 100, 2),
        "network": get_network_speed(),
        "uptime": int(time.time() - BOOT_TIME),
        "load": psutil.getloadavg(),
        "ports": get_open_ports()
    })


# ---------------- UI ---------------- #

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Linux Mini Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {
  font-family: system-ui;
  background: #0f172a;
  color: #e5e7eb;
  margin: 0; padding: 20px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}
.card {
  background: #020617;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,.4);
}
.header {
  display: flex;
  justify-content: space-between;
}
canvas { max-width: 200px; margin: auto; }
</style>
</head>
<body>

<div class="header card">
  <div>
    <h2 id="host"></h2>
    <p id="user"></p>
  </div>
  <div>
    <p>⬇ <span id="down"></span> KB/s</p>
    <p>⬆ <span id="up"></span> KB/s</p>
  </div>
</div>

<div class="grid">
  <div class="card"><canvas id="cpu"></canvas></div>
  <div class="card"><canvas id="mem"></canvas></div>
  <div class="card"><canvas id="disk"></canvas></div>
</div>

<div class="card">
  <h3>Open Ports</h3>
  <ul id="ports"></ul>
</div>

<script>
let charts = {};

function donut(id, label) {
  return new Chart(document.getElementById(id), {
    type: 'doughnut',
    data: { labels: [label, 'Free'], datasets: [{ data: [0,100] }] },
    options: { plugins: { legend: { display: false } } }
  });
}

charts.cpu = donut('cpu','CPU');
charts.mem = donut('mem','Memory');
charts.disk = donut('disk','Disk');

async function update() {
  let r = await fetch('/api/stats');
  let d = await r.json();

  document.getElementById('host').innerText = d.hostname;
  document.getElementById('user').innerText = d.username;
  document.getElementById('down').innerText = d.network.download_kbps;
  document.getElementById('up').innerText = d.network.upload_kbps;

  charts.cpu.data.datasets[0].data = [d.cpu, 100-d.cpu];
  charts.mem.data.datasets[0].data = [d.memory, 100-d.memory];
  charts.disk.data.datasets[0].data = [d.disk, 100-d.disk];

  Object.values(charts).forEach(c => c.update());

  let ports = document.getElementById('ports');
  ports.innerHTML = '';
  d.ports.forEach(p => {
    ports.innerHTML += `<li>${p.port} — ${p.process}</li>`;
  });
}

setInterval(update, 1000);
update();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
