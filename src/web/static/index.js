let pollTimer = null;
let isBenchmarking = false;

const $ = (id) => document.getElementById(id);

async function refreshDaemon() {
  try {
    const res = await fetch("/api/daemon/status");
    const data = await res.json();
    
    $("daemon-toggle").checked = data.enabled;
    $("daemon-status-text").className = data.enabled ? "status-online" : "status-offline";
    $("daemon-status-text").textContent = data.enabled ? "Active" : "Offline";
    $("daemon-primary").textContent = data.current_primary || "None";
  } catch (err) {
    console.error("Failed to fetch daemon state", err);
  }
}

async function refreshHostDNS() {
  try {
    const res = await fetch("/api/benchmark/results");
    const data = await res.json();
    if (data.system_dns && data.system_dns.length > 0) {
      $("host-dns-display").textContent = data.system_dns.join(", ");
    }
  } catch (err) {
    console.error("Failed to check system DNS", err);
  }
}

async function renderTable() {
  try {
    const res = await fetch("/api/benchmark/results");
    const data = await res.json();
    const tbody = $("results-body");

    if (data.system_dns && data.system_dns.length > 0) {
      $("host-dns-display").textContent = data.system_dns.join(", ");
    }

    const items = Object.entries(data.results || {});
    if (items.length === 0) return;

    items.sort((a, b) => a[1].rank - b[1].rank);

    tbody.innerHTML = items.map(([ip, stat]) => {
      let latClass = "lat-slow";
      if (stat.avg_latency !== null && stat.avg_latency < 35) latClass = "lat-fast";
      else if (stat.avg_latency !== null && stat.avg_latency < 80) latClass = "lat-med";

      return `
        <tr>
          <td><span class="badge-rank">#${stat.rank}</span></td>
          <td><strong>${ip}</strong></td>
          <td class="${latClass}">${stat.current_latency !== null ? stat.current_latency + " ms" : "ERR"}</td>
          <td class="${latClass}">${stat.avg_latency !== null ? stat.avg_latency + " ms" : "ERR"}</td>
          <td>${stat.success_rate}%</td>
          <td><strong>${stat.score}</strong>/100</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Benchmark poll error", err);
  }
}

async function toggleBenchmark() {
  const btn = $("btn-toggle-bench");
  if (!isBenchmarking) {
    const domain = $("target-domain").value.trim() || "example.com";
    const resolvers = $("resolvers-input").value.split(",").map((s) => s.trim()).filter(Boolean);

    await fetch("/api/benchmark/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain, resolvers }),
    });

    isBenchmarking = true;
    btn.textContent = "Stop Benchmark";
    btn.className = "btn btn-danger";
    pollTimer = setInterval(renderTable, 500);
  } else {
    await fetch("/api/benchmark/stop", { method: "POST" });
    isBenchmarking = false;
    btn.textContent = "Start Benchmark";
    btn.className = "btn btn-primary";
    clearInterval(pollTimer);
  }
}

$("daemon-toggle").addEventListener("change", async (e) => {
  const enabled = e.target.checked;
  await fetch("/api/daemon/toggle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  refreshDaemon();
});

$("btn-force-daemon").addEventListener("click", async () => {
  const btn = $("btn-force-daemon");
  btn.disabled = true;
  btn.textContent = "Evaluating...";
  try {
    const res = await fetch("/api/daemon/trigger", { method: "POST" });
    const data = await res.json();
    alert(`Trigger Result: ${data.status} (${data.reason || data.message || "Done"})`);
  } finally {
    btn.disabled = false;
    btn.textContent = "Evaluate & Switch Now";
    refreshDaemon();
    refreshHostDNS();
  }
});

$("btn-toggle-bench").addEventListener("click", toggleBenchmark);

// Init
refreshDaemon();
refreshHostDNS();
