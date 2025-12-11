let polling = null;

document.getElementById("startBtn").onclick = async () => {
    await fetch("/api/start", { method: "POST" });
    document.getElementById("statusBox").innerText = "Status: running";

    if (!polling) {
        polling = setInterval(fetchResults, 300);
    }
};

document.getElementById("stopBtn").onclick = async () => {
    await fetch("/api/stop", { method: "POST" });
    document.getElementById("statusBox").innerText = "Status: stopped";

    if (polling) {
        clearInterval(polling);
        polling = null;
    }
};

async function fetchResults() {
    let res = await fetch("/api/results", { method: "GET" });
    let data = await res.json();

    let out = "";
    for (const [resolver, latency] of Object.entries(data.results)) {
        out += `<div class="row">
                    <span>${resolver}</span>
                    <span>${latency ? latency + " ms" : "..."}</span>
                </div>`;
    }

    document.getElementById("results").innerHTML = out;
}
