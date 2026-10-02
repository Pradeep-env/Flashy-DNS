# ⚡ Flashy DNS

Flashy DNS is a lightweight, self-hosted DNS benchmarking tool and Linux auto-switching daemon with both CLI and GUI modes.  
It focuses on real-time latency visibility, resolver stability, and effortless zero-downtime DNS optimization rather than raw QPS numbers.

Flashy DNS answers one simple question:

> Which DNS resolver actually feels faster and more reliable right now?

---

## What Flashy DNS Is and Isn’t

Flashy DNS **is**:
- A real-time DNS latency benchmarking tool
- A CLI tool with live interactive terminal reporting
- A modern dark-mode GUI dashboard for visual resolver comparisons
- An automated Linux background daemon that hot-swaps system resolvers when faster candidates appear
- Async and parallel by design using `dnspython` and `FastAPI`

Flashy DNS **is not**:
- A `dnsperf` replacement
- A DNS stress or high-volume load-testing suite
- A QPS competition tool

If you need maximum query throughput testing, use `dnsperf`.  
If you want to understand real resolver behavior over time and auto-tune your system DNS, use Flashy DNS.

---

## How Latency Is Measured

Flashy DNS measures actual end-to-end DNS resolution latency, not simple socket connect time.

### Measurement Model
- Resolvers are queried concurrently using asynchronous DNS lookups.
- Failed queries register timeouts without distorting latency averages.
- Rolling stats continuously calculate mean response times.

### Metrics Explained
- **Current Latency**: Latency of the latest completed DNS resolution.
- **Average Latency**: Rolling mean of recent successful query samples.
- **Reliability (Success Rate)**: Percentage of successful resolutions vs attempts.
- **Health Score**: Composite metric weighting reliability (60%) and latency performance (40%).
- **Rank**: Resolver priority ordered by lowest average latency.

---

## Features

### CLI Mode
- Terminal-native live reporting dashboard
- Real-time colored latency thresholds
- Fully non-blocking asynchronous execution
- Support for arbitrary resolver sets and query targets
- No Docker required; zero system modifications by default

### GUI & Daemon Mode
- Real-time visual metrics table
- Integrated **5-Minute Auto-Switch Daemon**:
  - Automatically evaluates candidate resolvers in the background.
  - Applies system-level DNS changes via `systemd-resolved` or `/etc/resolv.conf`.
  - Built-in 20% hysteresis margin to prevent flapping between near-identical resolvers.
- Instant "Evaluate & Switch Now" override trigger.
- Lightweight CSS/Vanilla JS interface.


---

## Running the CLI (Manual Setup)

Run Flashy DNS directly on your host using Python 3.10+:

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/Pradeep-env/Flashy-DNS.git
cd Flashy-DNS

python -m venv .venv
source .venv/bin/activate
pip install -e .

```

### 2. Run Benchmark

For summary mode:

```bash
flashy-dns -r 1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222
```

Live terminal dashboard:

```bash
flashy-dns -r 1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222 --live
```

CLI Options:

* `-r / --resolvers`  DNS resolver IPs to benchmark (space-separated)
* `-d / --domain`     Target domain to resolve (default: example.com)
* `-t / --attempts`   Number of query samples per resolver (default: 5)
* `--live`            Launch interactive multi-line terminal dashboard
* `--daemon`          Run as a continuous foreground auto-switch daemon
* `--switch-now`      Run evaluation once and switch system DNS immediately if faster
* `--attempts`        Check interval in seconds (daemon mode only, default: 300), only combined with daemon.


## Running the GUI & Daemon (Docker / Compose)

Deploy the Web UI and Auto-Switching daemon isolated inside a container.

Host networking (network_mode: host) and NET_ADMIN privileges allow the container to benchmark host interfaces and optionally update system resolvers.

### 1. Start the Container

```bash
docker compose -f container/compose.yml up -d --build
```
(Podman users can substitute podman compose -f container/compose.yml up -d --build)

### 2. Access Dashboard

```bash
http://localhost:8000
```

### 3. Manage the Container

view logs:

```bash
docker compose -f container/compose.yml logs -f
```

stop container:

```bash
docker compose -f container/compose.yml stop
```

start container:

```bash
docker compose -f container/compose.yml start
```

remove container:

```bash
docker compose -f container/compose.yml down -v
```

## Score Calculation

Resolvers receive a score from 0 to 100 calculated as:

$$\text{Score} = (0.6 \times \text{Success Rate}) + (0.4 \times \text{Latency Factor})$$

Where:
- Success Rate: Resolved percentage over total attempts.
- Latency Factor: Scaled performance window favoring sub-30ms response times.

## Development Philosophy

* Simple over clever: Minimal moving parts, readable Python.
* Observable over abstract: Direct measurements over synthetic models.
* Lightweight over complex: No frontend framework overhead; pure HTML/CSS/JS.
* Safe automation: Auto-switching requires significant performance gains (hysteresis) to prevent route thrashing.

## Contributing

Contributions are welcome.

* Keep dependencies minimal and targeted.
* Ensure UI updates never block the async benchmark event loop.
* Test compatibility with both systemd-resolved and standard /etc/resolv.conf setups.