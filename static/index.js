// static/index.js
// IMPORTANT:
// This script relies on the CURRENT HTML structure.
// Do NOT change HTML order without updating traversal logic.

const startBtn = document.getElementById('benchmark');

const google = document.getElementById('google');
const cloud  = document.getElementById('cloud');
const open   = document.getElementById('open');
const quad   = document.getElementById('quad');
const ad     = document.getElementById('ad');

let running = false;
let poll = null;

// Resolver → CURRENT latency element
const values = {
    "8.8.8.8": google,
    "1.1.1.1": cloud,
    "208.67.222.222": open,
    "9.9.9.9": quad,
    "94.140.14.14": ad
};

// ---------------- START / STOP ----------------

startBtn.onclick = async () => {
    if (!running) {
        await fetch("/api/start", { method: "POST" });
        startBtn.innerText = "Stop";
        running = true;
        poll = setInterval(fetchResults, 400);
    } else {
        await fetch("/api/stop", { method: "POST" });
        startBtn.innerText = "Benchmark";
        running = false;
        clearInterval(poll);
        poll = null;
    }
};

// ---------------- FETCH + UPDATE ----------------

async function fetchResults() {
    try {
        const res = await fetch("/api/results");
        if (!res.ok) return;

        const data = await res.json();
        const results = data.results || {};

        Object.entries(results).forEach(([resolver, stats]) => {
            const currentElem = values[resolver];
            if (!currentElem) return;

            // ---- CURRENT & AVERAGE ----
            // <div><h2 id="x">current</h2><h2>average</h2></div>
            const avgElem = currentElem.nextElementSibling;

            // ---- SUCCESS & SCORE ----
            // currentDiv -> labelsDiv -> numbersDiv(success/score)
            const currentDiv = currentElem.parentElement;
            const successScoreDiv =
                currentDiv.nextElementSibling &&
                currentDiv.nextElementSibling.nextElementSibling;

            let successElem = null;
            let scoreElem = null;

            if (successScoreDiv) {
                const h2s = successScoreDiv.querySelectorAll('h2');
                if (h2s.length >= 2) {
                    successElem = h2s[0]; // success
                    scoreElem   = h2s[1]; // score
                }
            }

            // ---- SPEED LABEL BUTTON (Fast) ----
            const box = currentElem.closest('.box');
            const labelBtn = box ? box.querySelector('button') : null;

            // ---- UPDATE DOM ----

            // current latency
            if (stats.current_latency != null) {
                currentElem.innerText = `${stats.current_latency} ms`;
            } else {
                currentElem.innerText = `--`;
            }

            // average latency + color
            if (avgElem && stats.avg_latency != null) {
                avgElem.innerText = `${stats.avg_latency} ms`;

                if (stats.avg_latency < 35) {
                    avgElem.style.color = "green";
                    if (labelBtn) labelBtn.style.background = "green";
                } else if (stats.avg_latency < 100) {
                    avgElem.style.color = "orange";
                    if (labelBtn) labelBtn.style.background = "orange";
                } else {
                    avgElem.style.color = "red";
                    if (labelBtn) labelBtn.style.background = "red";
                }
            }

            // success rate
            if (successElem && stats.success_rate != null) {
                successElem.innerText = `${stats.success_rate}%`;
            }

            // score
            if (scoreElem && stats.score != null) {
                scoreElem.innerText = `${stats.score}`;
            }
        });

    } catch (err) {
        console.warn("Fetch error:", err);
    }
}
