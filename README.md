```markdown
# ⚡ Flashy DNS

Flashy DNS is a lightweight, self-hosted DNS benchmarking tool with both CLI and GUI modes.  
It focuses on real-time latency visibility and resolver stability rather than raw QPS numbers.

Flashy DNS answers one simple question:

Which DNS resolver actually feels faster and more reliable right now?

---

## What Flashy DNS Is and Isn’t

Flashy DNS **is**:
- A real-time DNS latency benchmarking tool
- A CLI tool with live terminal dashboard
- A GUI tool for visual comparison of resolvers
- Async and parallel by design
- Focused on accuracy, transparency, and usability

Flashy DNS **is not**:
- A dnsperf replacement
- A DNS stress or load testing tool
- A QPS competition tool

If you need maximum throughput testing, use dnsperf.  
If you want to understand real resolver behavior over time, use Flashy DNS.

---

## How Latency Is Measured

Flashy DNS measures actual DNS resolution latency, not socket connect time.

Measurement model:
- Resolvers are queried in parallel
- Each update uses multiple attempts (default: 3) to smooth jitter
- Failed queries do not affect averages
- Latency metrics are computed continuously

Metrics explained:
- Current latency: latest successful DNS query
- Average latency: rolling mean of recent successful samples
- Success rate: percentage of successful resolutions
- Score: combined metric based on success rate and latency
- Rank: resolver ordering by average latency (lower is better)

Why results may differ from dnsperf:
- dnsperf measures throughput (QPS)
- Flashy DNS measures interactive latency
- Flashy DNS runs continuously with short pauses
- GUI introduces minimal async overhead by design

Relative ranking remains consistent, which is what matters for resolver choice.

---

## Features

CLI:
- Live dashboard mode
- Colored latency indicators
- Parallel async execution
- Multiple resolvers support
- Clean terminal output

GUI:
- One-button Start / Stop benchmarking
- Real-time updates
- Current, average, success rate, score, rank
- Lightweight frontend (no React, no build tools)
- FastAPI backend
- Fully self-hosted

---

## Project Structure

```

Flashy-DNS/
│
├── backend/
│   ├── benchmark.py        # Core DNS benchmarking logic
│   ├── realtime_bench.py   # Optimized realtime engine for GUI
│   ├── flashy_dns.py       # CLI entrypoint
│   ├── server.py           # FastAPI backend
│   └── requirements.txt
│
├── static/
│   ├── index.html          # GUI layout
│   ├── index.js            # GUI logic
│   └── style.css
│
├── LICENSE
└── README.md

````

---

## Installation

Install dependencies:

```bash
pip install -r backend/requirements.txt
````

Python 3.9+ recommended.

---

## CLI Usage

Basic benchmark:

```bash
python backend/flashy_dns.py -r 1.1.1.1 8.8.8.8 9.9.9.9
```

Live dashboard mode:

```bash
python backend/flashy_dns.py -r 1.1.1.1 8.8.8.8 9.9.9.9 --live
```

Options:

* `-r / --resolvers`  DNS resolver IPs
* `-d / --domain`     Domain to query (default: example.com)
* `-t / --attempts`   Number of attempts
* `--live`            Enable live terminal dashboard

---

## GUI Usage

Start the backend from the project root:

```bash
uvicorn backend.server:app --reload --reload-dir static
```

Open in browser:

```
http://127.0.0.1:8000
```

GUI behavior:

* Click Benchmark to start
* Click again to stop
* Data updates live
* No configuration required

---

## About Scores and Ranking

Success rate:

* Percentage of successful DNS resolutions

Score (0–100):

* 60% weight: success rate
* 40% weight: average latency
* Designed to reward stability over spikes

Rank:

* Based on average latency
* Lower latency ranks higher

Scores are meant for comparison, not absolute judgment.

---

## Accuracy Notes

* GUI latency may be slightly higher than CLI (10–20ms)
* This is expected due to async scheduling and UI updates
* Both modes use the same DNS resolution logic
* Relative ordering remains consistent

Use CLI for minimal overhead measurements.
Use GUI for understanding behavior over time.

---

## Validation

Flashy DNS has been validated against:

* dnsperf
* dig
* repeated manual DNS resolution tests

Results align in relative ranking, which is the primary goal.

---

## Development Philosophy

* Simple over clever
* Observable over abstract
* Honest numbers over impressive numbers
* Lightweight over complex
* Async where it helps, not everywhere

---

## Contributing

Contributions are welcome.

Guidelines:

* Benchmark logic changes should be discussed
* UI changes must not affect measurement accuracy
* Keep dependencies minimal
* Avoid heavy frontend frameworks

Open an issue before major changes.

---

## License

MIT License.

Use it, fork it, learn from it, improve it.

---

## Roadmap (Not Promises)

* Optional WebSocket mode
* Median / p95 latency views
* Exportable benchmark reports
* Resolver auto-recommendation
* UI polish and theming

---

## Final Note

Flashy DNS is built for people who like to understand systems, not just consume numbers.

If you enjoy tools that show what’s actually happening under the hood, you’ll feel at home here.

⚡

```

---

If you want next, I can do the same **single-file style** for:
- `CONTRIBUTING.md`
- `COLLAB.md`
- a clean `CHANGELOG.md`
- a v0.1.0 release checklist

Just say which one.
```
