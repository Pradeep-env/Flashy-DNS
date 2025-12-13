# ⚡ Flashy DNS

Flashy DNS is a **lightweight, self-hosted DNS benchmarking tool** with both **CLI** and **GUI** modes.  
It focuses on **real-time latency visibility**, not raw QPS bragging.

If you want to *see* how DNS resolvers behave over time instead of staring at static numbers, this tool is for you.

---

## ✨ What Flashy DNS Is (and Isn’t)

### ✔ What it is
- Real-time DNS latency benchmarking
- CLI mode for terminal lovers
- GUI dashboard for live visual comparison
- Async, parallel resolver testing
- Designed for **accuracy + transparency**, not hype

### ✖ What it isn’t
- Not a dnsperf replacement
- Not a stress / load testing tool
- Not about millions of queries per second

Flashy DNS answers a different question:

> **“Which resolver feels faster and more stable for me, right now?”**

---

## 🧠 How Flashy DNS Measures Latency

This is important.

Flashy DNS measures **real DNS resolution latency**, not socket connect time.

### Measurement model
- Each resolver is queried in parallel
- Each update uses **multiple attempts** (default: 3) to smooth noise
- Latency is calculated as:
  - **Current latency** → latest successful query
  - **Average latency** → rolling mean of recent samples
- Failed queries do **not poison averages**

### Why numbers may differ from dnsperf
- dnsperf focuses on **throughput (QPS)**
- Flashy DNS focuses on **interactive latency**
- Flashy DNS runs continuously with pauses, not tight fire-hose loops

This makes Flashy DNS better suited for:
- Choosing a daily DNS resolver
- Comparing stability over time
- Visual monitoring

---

## 🚀 Features

### CLI
- Live dashboard mode (`--live`)
- Clean terminal output
- Colored latency indicators
- Multi-resolver benchmarking
- Async execution

### GUI
- Start / Stop benchmarking with one button
- Live updates (current, average, success rate, score)
- Resolver ranking
- Clean, minimal UI
- No React, no build step, no nonsense

---

## 📦 Project Structure

Flashy-DNS/
│
├── backend/
│ ├── benchmark.py # Core DNS benchmarking logic
│ ├── realtime_bench.py # Optimized realtime engine (GUI)
│ ├── flashy_dns.py # CLI entrypoint
│ ├── server.py # FastAPI backend
│ └── requirements.txt
│
├── static/
│ ├── index.html # GUI
│ ├── index.js # GUI logic
│ └── style.css
│
├── LICENSE
└── README.md
