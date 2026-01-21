import psutil
import socket
import getpass
import time
import shutil
import platform
import subprocess
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Linux Pro Dashboard")

# Global Cache for network calculations
BOOT_TIME = psutil.boot_time()
NET_IO_PREV = psutil.net_io_counters()
NET_TIME_PREV = time.time()

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def get_network_speed():
    global NET_IO_PREV, NET_TIME_PREV
    now = time.time()
    net = psutil.net_io_counters()
    interval = now - NET_TIME_PREV
    
    sent = (net.bytes_sent - NET_IO_PREV.bytes_sent) / interval
    recv = (net.bytes_recv - NET_IO_PREV.bytes_recv) / interval
    
    NET_IO_PREV = net
    NET_TIME_PREV = now
    return {"up": get_size(sent) + "/s", "down": get_size(recv) + "/s"}

def get_network_info():
    """Gets the active interface and IP address."""
    iface_name = "N/A"
    ip_addr = "127.0.0.1"
    for iface, addrs in psutil.net_if_addrs().items():
        if not iface.startswith('lo'):
            iface_name = iface
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_addr = addr.address
                    break
            if ip_addr != "127.0.0.1": break
    return {"interface": iface_name, "ip": ip_addr}

def get_system_logs():
    """Fetches recent system logs using journalctl."""
    try:
        # Get last 8 lines of system logs
        logs = subprocess.check_output(["journalctl", "-n", "8", "--no-pager", "-q"]).decode('utf-8')
        return logs.strip().split('\n')
    except Exception:
        return ["Log access denied. Try running with sudo."]

def get_top_processes():
    procs = []
    for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), 
                   key=lambda x: x.info['cpu_percent'], reverse=True)[:10]:
        procs.append(p.info)
    return procs

@app.get("/api/stats")
def stats():
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    uptime_seconds = int(time.time() - BOOT_TIME)
    net_info = get_network_info()

    return {
        "sys": {
            "hostname": socket.gethostname(),
            "user": getpass.getuser(),
            "os": f"{platform.system()} {platform.release()}",
            "uptime": f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m",
            "load": psutil.getloadavg(),
            "net_info": net_info
        },
        "usage": {
            "cpu": psutil.cpu_percent(interval=None),
            "mem": {"percent": mem.percent, "used": get_size(mem.used), "total": get_size(mem.total)},
            "disk": {"percent": round((disk.used/disk.total)*100, 1), "used": get_size(disk.used), "total": get_size(disk.total)}
        },
        "net_speed": get_network_speed(),
        "procs": get_top_processes(),
        "logs": get_system_logs(),
        "ports": [{"p": c.laddr.port, "n": psutil.Process(c.pid).name() if c.pid else "?"} 
                  for c in psutil.net_connections(kind="inet") if c.status == "LISTEN"][:10]
    }

@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Pulse</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --bg: #030712;
            --card-bg: rgba(31, 41, 55, 0.4);
            --accent: #3b82f6;
            --text: #f3f4f6;
        }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background-color: var(--bg);
            background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, #030712 100%);
            color: var(--text);
            margin: 0; padding: 24px; min-height: 100vh;
        }
        .bento-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-auto-rows: minmax(160px, auto);
            gap: 16px; max-width: 1200px; margin: 0 auto;
        }
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 20px;
            transition: transform 0.2s ease;
        }
        .card:hover { transform: translateY(-2px); border-color: var(--accent); }
        .span-2 { grid-column: span 2; }
        .span-4 { grid-column: span 4; }
        
        .stat-val { font-size: 24px; font-weight: 700; margin-top: 8px; color: var(--accent); }
        .label { font-size: 12px; text-transform: uppercase; opacity: 0.6; letter-spacing: 1px; display: flex; align-items: center; gap: 6px; }
        
        .chart-container { position: relative; height: 120px; width: 120px; margin: 10px auto; }
        .chart-label { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; font-size: 14px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th { text-align: left; opacity: 0.5; padding-bottom: 8px; }
        td { padding: 6px 0; border-top: 1px solid rgba(255,255,255,0.05); }
        .badge { background: #1e293b; padding: 2px 8px; border-radius: 6px; font-family: monospace; }
        
        .log-box { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 12px; font-family: 'Fira Code', monospace; font-size: 11px; color: #94a3b8; overflow-x: auto; border: 1px solid rgba(255,255,255,0.05); }
        .log-line { margin-bottom: 4px; border-left: 2px solid var(--accent); padding-left: 10px; }

        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; max-width: 1200px; margin-inline: auto; }
    </style>
</head>
<body>

<div class="header">
    <div>
        <h1 style="margin:0; font-size: 24px;"><img style="height:24px; width:24px;" src="https://raw.githubusercontent.com/Pings-Lab/Linux-Utilities/main/dashboard/ping.jpg" alt="pingslab"/>Ping's Lab</h1>
        <div id="os-info" style="opacity: 0.6; font-size: 14px;">Loading system...</div>
    </div>
    <div style="text-align: right">
        <div id="uptime" class="badge">--</div>
        <div style="font-size: 12px; margin-top: 4px; opacity: 0.5;">UPTIME</div>
    </div>
</div>

<div class="bento-grid">
    <!-- Row 1: Quick Stats -->
    <div class="card">
        <div class="label"><i data-lucide="user"></i> User</div>
        <div id="username" class="stat-val">--</div>
    </div>
    <div class="card">
        <div class="label"><i data-lucide="wifi"></i> Network Info</div>
        <div id="net-iface" class="stat-val" style="font-size: 18px;">--</div>
        <div id="net-ip" style="font-size: 12px; opacity: 0.6; margin-top: 4px;">0.0.0.0</div>
    </div>
    <div class="card">
        <div class="label"><i data-lucide="download"></i> Download</div>
        <div id="down" class="stat-val">0 KB/s</div>
    </div>
    <div class="card">
        <div class="label"><i data-lucide="upload"></i> Upload</div>
        <div id="up" class="stat-val">0 KB/s</div>
    </div>

    <!-- Row 2: Charts -->
    <div class="card">
        <div class="label">CPU Usage</div>
        <div class="chart-container">
            <canvas id="cpuChart"></canvas>
            <div class="chart-label" id="cpu-text">0%</div>
        </div>
    </div>
    <div class="card">
        <div class="label">Memory</div>
        <div class="chart-container">
            <canvas id="memChart"></canvas>
            <div class="chart-label" id="mem-text">0%</div>
        </div>
        <div id="mem-detail" style="font-size: 10px; text-align: center; opacity: 0.6">-- / --</div>
    </div>
    <div class="card">
        <div class="label">Disk Usage</div>
        <div class="chart-container">
            <canvas id="diskChart"></canvas>
            <div class="chart-label" id="disk-text">0%</div>
        </div>
        <div id="disk-detail" style="font-size: 10px; text-align: center; opacity: 0.6">-- / --</div>
    </div>
    <div class="card">
        <div class="label"><i data-lucide="activity"></i> Load Avg</div>
        <div id="load-avg" class="stat-val" style="font-size: 18px; margin-top: 15px;">--</div>
    </div>

    <!-- Row 3: Lists -->
    <div class="card span-2">
        <div class="label"><i data-lucide="cpu"></i> Top Processes</div>
        <table id="proc-table">
            <thead><tr><th>PID</th><th>Process</th><th>CPU%</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>
    <div class="card span-2">
        <div class="label"><i data-lucide="shield"></i> Listening Ports</div>
        <table id="port-table">
            <thead><tr><th>Port</th><th>Service</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <!-- Row 4: Logs -->
    <div class="card span-4">
        <div class="label"><i data-lucide="terminal"></i> Recent System Logs (journalctl)</div>
        <div id="log-container" class="log-box">
            Loading logs...
        </div>
    </div>
</div>

<script>
    lucide.createIcons();
    
    function createChart(id, color) {
        return new Chart(document.getElementById(id), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [color, 'rgba(255,255,255,0.05)'],
                    borderWidth: 0,
                    borderRadius: 10,
                }]
            },
            options: { cutout: '85%', plugins: { legend: { display: false } }, events: [] }
        });
    }

    const charts = {
        cpu: createChart('cpuChart', '#3b82f6'),
        mem: createChart('memChart', '#a855f7'),
        disk: createChart('diskChart', '#10b981')
    };

    async function update() {
        try {
            const res = await fetch('/api/stats');
            const d = await res.json();

            // Header & Quick Stats
            document.getElementById('os-info').innerText = `${d.sys.os} | ${d.sys.hostname}`;
            document.getElementById('username').innerText = d.sys.user;
            document.getElementById('uptime').innerText = d.sys.uptime;
            
            // Network Info
            document.getElementById('net-iface').innerText = d.sys.net_info.interface;
            document.getElementById('net-ip').innerText = d.sys.net_info.ip;
            
            // Speeds
            document.getElementById('down').innerText = d.net_speed.down;
            document.getElementById('up').innerText = d.net_speed.up;
            document.getElementById('load-avg').innerText = d.sys.load.join(', ');

            // Charts
            const updateChart = (name, val, detailId, detailText) => {
                charts[name].data.datasets[0].data = [val, 100 - val];
                charts[name].update();
                document.getElementById(`${name}-text`).innerText = val + '%';
                if(detailId) document.getElementById(detailId).innerText = detailText;
            };

            updateChart('cpu', d.usage.cpu);
            updateChart('mem', d.usage.mem.percent, 'mem-detail', `${d.usage.mem.used} / ${d.usage.mem.total}`);
            updateChart('disk', d.usage.disk.percent, 'disk-detail', `${d.usage.disk.used} / ${d.usage.disk.total}`);

            // Tables
            document.querySelector('#proc-table tbody').innerHTML = d.procs.map(p => 
                `<tr><td>${p.pid}</td><td>${p.name}</td><td><span class="badge">${p.cpu_percent}%</span></td></tr>`
            ).join('');

            document.querySelector('#port-table tbody').innerHTML = d.ports.map(p => 
                `<tr><td><span class="badge" style="color:var(--accent)">${p.p}</span></td><td>${p.n}</td></tr>`
            ).join('');

            // Logs
            document.getElementById('log-container').innerHTML = d.logs.map(line => 
                `<div class="log-line">${line}</div>`
            ).join('');

        } catch (e) { console.error("Update failed", e); }
    }

    setInterval(update, 2000);
    update();
</script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    # Important: journalctl and net_connections require sudo/root for full output
    uvicorn.run(app, host="0.0.0.0", port=8000)
