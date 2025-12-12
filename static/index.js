const start=document.getElementById('benchmark');
const google = document.getElementById('google');
const cloud = document.getElementById('cloud');
const ad = document.getElementById('ad');
const quad = document.getElementById('quad');
const open = document.getElementById('open');

var bench=0;

var values={"8.8.8.8": google, "1.1.1.1": cloud, "9.9.9.9": quad, "208.67.222.222": open, "94.140.14.14": ad}

start.onclick=()=>{
if(bench===0)
{
start.innerHTML="Stop";
bench=1;
dnsstart();
poll=setInterval(fetchResults, 300);
}
else{
start.innerHTML="Benchmark";
bench=0;
dnsstop();
clearInterval(poll);
}
}


let polling = null;

async function dnsstart () {
    await fetch("/api/start", { method: "POST" });
    document.getElementById("statusBox").innerText = "Status: running";

    if (!polling) {
        polling = setInterval(fetchResults, 300);
    }
};

async function dnsstop () {
    await fetch("/api/stop", { method: "POST" });
    document.getElementById("statusBox").innerText = "Status: stopped";

    if (polling) {
        clearInterval(polling);
        polling = null;
    }
};

async function fetchResults() {
    let res = await fetch("/api/results", { method: "GET" });
    if (!res.ok) {
        console.warn("Failed to fetch results:", res.status);
        return;
    }
    let data = await res.json();

    let out = "";
    for (const [resolver, latency] of Object.entries(data.results || {})) {
           values[resolver].innerHTML=latency+"ms";
    }

    document.getElementById("results").innerHTML = out;
}
