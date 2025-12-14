# backend/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import threading
import statistics
from collections import deque

from backend.realtime_bench import quick_dns  # ← NEW optimized DNS engine

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# static mount
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

# -------------------------------------------------------------------------
# BENCHMARK STATE
# -------------------------------------------------------------------------

state = {"running": False, "results": {}}

HISTORY_MAX = 200
histories = {}
success_counts = {}
sample_counts = {}

DEFAULT_RESOLVERS = [
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9",
    "208.67.222.222",
    "94.140.14.14"
]

DEFAULT_DOMAIN = "example.com"   # ← MUCH FASTER AND MATCHES CLI

def ensure(resolvers):
    for r in resolvers:
        histories.setdefault(r, deque(maxlen=HISTORY_MAX))
        success_counts.setdefault(r, 0)
        sample_counts.setdefault(r, 0)

def compute_score(avg_latency, success_rate):
    if avg_latency is None:
        latency_component = 0
    else:
        clamped = max(0, min(200, avg_latency))
        latency_component = (1 - (clamped / 200)) * 100

    score = (0.6 * success_rate) + (0.4 * latency_component)
    return int(max(0, min(100, score)))

# -------------------------------------------------------------------------
# MAIN DNS LOOP (Optimized for speed)
# -------------------------------------------------------------------------

async def dns_loop(resolvers, domain):
    ensure(resolvers)

    while state["running"]:
        # run optimized parallel DNS checks (3 attempts each)
        results = await asyncio.gather(*[quick_dns(r, domain) for r in resolvers])

        # update tracking data
        for res in results:
            r = res["resolver"]
            lat = res["avg_latency"]
            succ = res.get("success", 0)

            sample_counts[r] += 1
            if succ > 0:
                success_counts[r] += 1

            if lat is not None:
                histories[r].append(lat)

        # aggregate results
        aggregated = {}
        for r in resolvers:
            hist = list(histories[r])
            samples = sample_counts[r]
            succs = success_counts[r]

            current = hist[-1] if hist else None
            avg = round(statistics.mean(hist), 2) if hist else None
            success_rate = round((succs / samples) * 100, 2) if samples > 0 else 0.0
            score = compute_score(avg, success_rate)

            aggregated[r] = {
                "current_latency": current,
                "avg_latency": avg,
                "success_rate": success_rate,
                "score": score,
                # rank added below
            }

        # Ranking by average latency
        sorted_keys = sorted(
            aggregated.keys(),
            key=lambda x: (
                aggregated[x]["avg_latency"] is None,
                aggregated[x]["avg_latency"] if aggregated[x]["avg_latency"] is not None else 1e9
            )
        )

        for i, r in enumerate(sorted_keys, start=1):
            aggregated[r]["rank"] = i

        # update public state
        state["results"] = aggregated

        # VERY fast loop for real-time GUI updates (matches CLI speed)
        await asyncio.sleep(0.05)

# -------------------------------------------------------------------------
# API ROUTES
# -------------------------------------------------------------------------

@app.post("/api/start")
async def start():
    if not state["running"]:
        state["running"] = True
        threading.Thread(
            target=lambda: asyncio.run(
                dns_loop(DEFAULT_RESOLVERS, DEFAULT_DOMAIN)
            ),
            daemon=True
        ).start()

    return {"status": "started"}

@app.post("/api/stop")
async def stop():
    state["running"] = False
    histories = {}
    success_counts = {}
    sample_counts = {}

    return {"status": "stopped"}

@app.get("/api/results")
async def results():
    return state
