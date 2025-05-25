from fastapi.responses import HTMLResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Cache Dashboard</title>
    <style>
        body { font-family: Arial; margin: 2rem; background: #f9f9f9; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #eee; }
        .section { margin-bottom: 3rem; }
        .timestamp { color: #777; font-size: 0.9em; }
        .stats { margin-bottom: 1rem; }
    </style>
</head>
<body>
    <h1>📊 Cache Metrics Dashboard</h1>

    <div class="section">
        <h2>🎬 Movie Cache</h2>
        <div class="stats">
            Evictions: <span id="movieEvictions">0</span> |
            Hit Rate: <span id="movieHitRate">0%</span> |
            Avg Hit Latency: <span id="movieAvgHitLatency">0</span> ms |
            Avg Miss Latency: <span id="movieAvgMissLatency">0</span> ms
        </div>
        <table id="movieCache">
            <thead><tr><th>Key</th><th>Hits</th><th>Cost</th><th>Size</th><th>Last Access</th><th>Avg Latency (ms)</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <div class="section">
        <h2>🧠 Derived Cache</h2>
        <div class="stats">
            Evictions: <span id="derivedEvictions">0</span> |
            Hit Rate: <span id="derivedHitRate">0%</span> |
            Avg Hit Latency: <span id="derivedAvgHitLatency">0</span> ms |
            Avg Miss Latency: <span id="derivedAvgMissLatency">0</span> ms
        </div>
        <table id="derivedCache">
            <thead><tr><th>Key</th><th>Hits</th><th>Cost</th><th>Size</th><th>Last Access</th><th>Avg Latency (ms)</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <div class="timestamp" id="lastUpdate">⏱️ Loading...</div>

    <script>
        async function fetchData() {
            const res = await fetch("/cache/stats");
            const data = await res.json();

            function renderTable(id, cacheData) {
                const tbody = document.querySelector(`#${id} tbody`);
                tbody.innerHTML = "";
                for (const [key, meta] of Object.entries(cacheData.entries || {})) {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${key}</td>
                        <td>${meta.access_count}</td>
                        <td>${meta.compute_cost.toFixed(2)}</td>
                        <td>${meta.size.toFixed(2)}</td>
                        <td>${new Date(meta.last_access * 1000).toLocaleTimeString()}</td>
                        <td>${(meta.avg_latency * 1000).toFixed(3)}</td>
                    `;
                    tbody.appendChild(row);
                }
            }

            function renderStats(prefix, cacheData) {
                document.getElementById(prefix + "Evictions").innerText = cacheData.eviction_count;
                document.getElementById(prefix + "HitRate").innerText = (cacheData.hit_rate * 100).toFixed(2) + "%";
                document.getElementById(prefix + "AvgHitLatency").innerText = (cacheData.avg_hit_latency * 1000).toFixed(3);
                document.getElementById(prefix + "AvgMissLatency").innerText = (cacheData.avg_miss_latency * 1000).toFixed(3);
            }

            renderTable("movieCache", data.movie_cache);
            renderTable("derivedCache", data.derived_cache);

            renderStats("movie", data.movie_cache);
            renderStats("derived", data.derived_cache);

            document.getElementById("lastUpdate").innerText = "⏱️ Updated: " + new Date().toLocaleTimeString();
        }

        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
