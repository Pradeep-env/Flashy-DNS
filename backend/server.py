from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import asyncio
import threading

from backend.benchmark import run_dns_test

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files under /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve GUI index.html at root
@app.get("/")
def serve_gui():
    return FileResponse("static/index.html")

# Shared state
state = {"running": False, "results": {}}

async def dns_loop(resolvers, domain):
    while state["running"]:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(None, run_dns_test, r, domain, 1)
            for r in resolvers
        ]
        results = await asyncio.gather(*futures)
        state["results"] = {
            r["resolver"]: r["avg_latency"] for r in results
        }
        await asyncio.sleep(0.2)

@app.post("/api/start")
async def start_benchmark():
    if not state["running"]:
        state["running"] = True
        threading.Thread(
            target=lambda: asyncio.run(
                dns_loop(["1.1.1.1", "8.8.8.8", "9.9.9.9"], "google.com")
            ),
            daemon=True
        ).start()
    return {"status": "started"}

@app.post("/api/stop")
async def stop_benchmark():
    state["running"] = False
    return {"status": "stopped"}

@app.get("/api/results")
async def get_results():
    return state
