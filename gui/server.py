from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import threading
import time

from ../backend.benchmark import run_dns_test

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Shared benchmark state
state = {
    "running": False,
    "results": {}
}

async def dns_loop(resolvers, domain):
    while state["running"]:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(None, run_dns_test, r, domain, 1)
            for r in resolvers
        ]
        results = await asyncio.gather(*futures)

        state["results"] = {r["resolver"]: r["avg_latency"] for r in results}

        await asyncio.sleep(0.2)  # UI update frequency


@app.post("/start")
async def start_benchmark():
    if not state["running"]:
        state["running"] = True
        threading.Thread(
            target=lambda: asyncio.run(dns_loop(
                ["1.1.1.1", "8.8.8.8", "9.9.9.9"], "google.com"
            )),
            daemon=True
        ).start()
    return {"status": "started"}

@app.post("/stop")
async def stop_benchmark():
    state["running"] = False
    return {"status": "stopped"}

@app.get("/results")
async def get_results():
    return {
        "running": state["running"],
        "results": state["results"]
    }
