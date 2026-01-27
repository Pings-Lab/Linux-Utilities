# System Pulse – Linux Utility Dashboard

System Pulse is a lightweight Linux utility dashboard built with **FastAPI** that provides real-time visibility into system health using a clean, modern bento-style UI. It is designed to encourage creativity, learning-by-doing, and continuous skill development while working with Linux systems.

---

## ✨ Features

- **System Overview**
  - Hostname, username, OS information
  - System uptime and load average

- **Wi-Fi Live Monitoring**
  - Real-time download and upload speeds

- **Resource Usage**
  - CPU usage
  - Memory usage (used / total)
  - Disk usage (used / total)

- **Process & Network Insights**
  - Top CPU-consuming processes
  - Listening ports with associated services

- **Recent System Logs**
  - Displays the latest system logs using `journalctl`
  - Useful for quick diagnostics and monitoring

---

## 🧱 Tech Stack

- **Backend:** FastAPI, psutil
- **Frontend:** HTML, CSS, JavaScript
- **Charts:** Chart.js
- **Icons:** Lucide Icons
- **Platform:** Linux (Ubuntu and other distributions)

---

## 🚀 Getting Started

### Prerequisites

- Linux system
- Python 3.9+
- `sudo` access (required for ports and system logs)

---

### Installation


1. uv installation (not necessary if you already have)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. clone the repo
```repo
git clone git@github.com:Pings-Lab/Linux-Utilities.git
cd Linux-Utilities
```

3. if you don't want whole repo
```bash
git clone --depth 1 --filter=blob:none --sparse \
https://github.com/Pings-Lab/Linux-Utilities.git \
&& cd Linux-Utilities \
&& git sparse-checkout set dashboard

```
4. setup uv and run
```bash
cd dashboard/
uv sync
sudo $(uv run which python) linux_utility.py
```

5. if you don't have sudo access
```bash
uv run python linux_utility.py
``` 

## 👤 Users Section

### 1. Can I contribute to the project?

You are most welcome.
Not only for this repo, any repo under this organization is open for use and modification

1. Clone the repo
2. Make your changes
3. Create a pull request

### 2. Can I join the Ping's lab organization?

We welcome you with open arms.
Use the Organization website or email to contact us.

- Website: [link](https://pings-lab.github.io)
- Email: thepingslab@gmail.com

