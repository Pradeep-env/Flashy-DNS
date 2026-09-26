import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.core.benchmark import test_resolver_once
from src.core.switcher import get_current_dns
from src.daemon.scheduler import DNSAutoManager

daemon = DNSAutoManager(interval_seconds=300)

benchmark_state = {
    "running": False,
    "domain": "example.com",
    "resolvers": [
        "1.1.1.1",
        "8.8.8.8",
        "9.9.9.9",
        "208.67.222.222",
        "94.140.14.14",
    ],
    "results": {},
}
benchmark_task: Optional[asyncio.Task] = None


async def live_benchmark_loop():
    while benchmark_state["running"]:
        resolvers = benchmark_state["resolvers"]
        domain = benchmark_state["domain"]

        tasks = [test_resolver_once(r, domain=domain) for r in resolvers]
        res_list = await asyncio.gather(*tasks)

        for res in res_list:
            r = res["resolver"]
            lat = res["latency"]
            succ = 1 if res["success"] else 0

            entry = benchmark_state["results"].setdefault(
                r, {"samples": 0, "success": 0, "history": []}
            )
            entry["samples"] += 1
            entry["success"] += succ
            if lat is not None:
                entry["history"].append(lat)
                if len(entry["history"]) > 100:
                    entry["history"].pop(0)

        await asyncio.sleep(0.5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    daemon.stop()
    if benchmark_task and not benchmark_task.done():
        benchmark_task.cancel()


app = FastAPI(title="Flashy-DNS", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/web/static", html=True), name="static")


@app.get("/")
def index():
    return FileResponse("src/web/static/index.html")


class BenchmarkConfigRequest(BaseModel):
    domain: Optional[str] = "example.com"
    resolvers: Optional[List[str]] = None


@app.post("/api/benchmark/start")
async def start_benchmark(cfg: Optional[BenchmarkConfigRequest] = None):
    global benchmark_task
    if cfg:
        if cfg.domain:
            benchmark_state["domain"] = cfg.domain
        if cfg.resolvers:
            benchmark_state["resolvers"] = cfg.resolvers

    if not benchmark_state["running"]:
        benchmark_state["running"] = True
        benchmark_state["results"] = {}
        benchmark_task = asyncio.create_task(live_benchmark_loop())

    return {"status": "started"}


@app.post("/api/benchmark/stop")
async def stop_benchmark():
    global benchmark_task
    benchmark_state["running"] = False
    if benchmark_task and not benchmark_task.done():
        benchmark_task.cancel()
    benchmark_state["results"] = {}
    return {"status": "stopped"}


@app.get("/api/benchmark/results")
async def get_benchmark_results():
    formatted = {}
    for r, data in benchmark_state["results"].items():
        hist = data["history"]
        samples = data["samples"]
        succ = data["success"]

        current = hist[-1] if hist else None
        avg = round(sum(hist) / len(hist), 2) if hist else None
        rate = round((succ / samples) * 100, 2) if samples > 0 else 0.0

        clamped = max(0, min(200, avg if avg is not None else 200))
        lat_comp = (1 - (clamped / 200)) * 100
        score = int(round((0.6 * rate) + (0.4 * lat_comp)))

        formatted[r] = {
            "current_latency": current,
            "avg_latency": avg,
            "success_rate": rate,
            "score": score,
        }

    sorted_keys = sorted(
        formatted.keys(),
        key=lambda x: (
            formatted[x]["avg_latency"] is None,
            formatted[x]["avg_latency"] if formatted[x]["avg_latency"] is not None else 1e9,
        ),
    )
    for rank, r in enumerate(sorted_keys, start=1):
        formatted[r]["rank"] = rank

    return {
        "running": benchmark_state["running"],
        "system_dns": get_current_dns(),
        "results": formatted,
    }



class DaemonToggleRequest(BaseModel):
    enabled: bool
    interval_seconds: Optional[int] = 300
    candidates: Optional[List[str]] = None


@app.get("/api/daemon/status")
async def daemon_status():
    return daemon.get_status()


@app.post("/api/daemon/toggle")
async def daemon_toggle(req: DaemonToggleRequest):
    if req.interval_seconds:
        daemon.interval = req.interval_seconds
    if req.candidates:
        daemon.candidates = req.candidates

    if req.enabled:
        daemon.start()
    else:
        daemon.stop()

    return daemon.get_status()


@app.post("/api/daemon/trigger")
async def daemon_trigger_now():
    res = await daemon.evaluate_and_switch()
    return res
