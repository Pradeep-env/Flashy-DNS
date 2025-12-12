// static/index.js
// This script assumes your HTML structure is unchanged.
// It uses the <h2 id="..."> elements for current latency and updates average, success and score
// by DOM traversal relative to those elements.

const startBtn = document.getElementById('benchmark');
const google = document.getElementById('google');
const cloud = document.getElementById('cloud');
const open = document.getElementById('open');
const quad = document.getElementById('quad');
const ad = document.getElementById('ad');

let running = false;
let poll = null;

// map resolver IP -> element that holds CURRENT latency (id in HTML)
const values = {
    "8.8.8.8": google,
    "1.1.1.1": cloud,
    "208.67.222.222": open,
    "9.9.9.9": quad,
    "94.140.14.14": ad
};

startBtn.onclick = async () => {
    if (!running) {
        // start
        await fetch("/api/start", { method: "POST" });
        startBtn.innerText = "Stop";
        running = true;
        poll = setInterval(fetchResults, 400);
    } else {
        // stop
        await fetch("/api/stop", { method: "POST" });
        startBtn.innerText = "Benchmark";
        running = false;
        if (poll) {
            clearInterval(poll);
            poll = null;
        }
    }
};

async function fetchResults() {
    try {
        const res = await fetch("/api/results");
        if (!res.ok) return;
        const data = await res.json();
        const results = data.results || {};

        Object.entries(results).forEach(([resolver, stats]) => {
            const currentElem = values[resolver];
            if (!currentElem) return; // unknown resolver in UI

            // current and average are in the same parent div: <div><h2 id="x">cur</h2><h2>avg</h2></div>
            const avgElem = currentElem.nextElementSibling;

            // success/score are in the second numbers div after current's parent div:
            // currentDiv -> labelsDiv (success labels) -> numbersDiv (success/score)
            const currentDiv = currentElem.parentElement;
            const successScoreContainer = currentDiv.nextElementSibling && currentDiv.nextElementSibling.nextElementSibling;
            let successElem = null, scoreElem = null;
            if (successScoreContainer) {
                const h2s = successScoreContainer.querySelectorAll('h2');
                if (h2s && h2s.length >= 2) {
                    successElem = h2s[0];
                    scoreElem = h2s[1];
                }
            }

            // update DOM safely
            if (stats.current_latency != null) {
                currentElem.innerText = `${stats.current_latency} ms`;
            } else {
                currentElem.innerText = `--`;
            }

            if (stats.avg_latency != null && avgElem) {
                avgElem.innerText = `${stats.avg_latency} ms`;
            }

            if (successElem && typeof stats.success_rate !== "undefined") {
                successElem.innerText = `${stats.success_rate}%`;
            }

            if (scoreElem && typeof stats.score !== "undefined") {
                scoreElem.innerText = `${stats.score}`;
            }

            // optional: you could color the top left small button inside each box by rank,
            // but since HTML doesn't expose that element id, keep layout untouched.
        });

    } catch (e) {
        console.warn("Error fetching results:", e);
    }
}
