from fastapi.responses import HTMLResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>📊 Cache Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            margin: 20px;
        }
        h1, h2 {
            color: #333;
        }
        .section {
            margin-bottom: 40px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 6px 8px;
        }
        th {
            background-color: #eee;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #fafafa;
        }
        code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
        }
    </style>
</head>
<body>

    <h1>📊 Cache Monitoring Dashboard</h1>

    <div class="section">
        <h2>📈 Cache Metrics</h2>
        <p><strong>Evictions:</strong> <span id="evictions">-</span></p>
        <p><strong>Hit Rate:</strong> <span id="hitRate">-</span></p>
        <p><strong>Avg Hit Latency:</strong> <span id="avgHitLatency">-</span> sec</p>
        <p><strong>Avg Miss Latency:</strong> <span id="avgMissLatency">-</span> sec</p>
    </div>

    <div class="section">
        <h2>📦 Current Cache Entries</h2>
        <table id="cacheTable">
            <thead>
                <tr>
                    <th>Key</th>
                    <th>Access Count</th>
                    <th>Last Access</th>
                    <th>Type</th>
                    <th>Cost</th>
                    <th>Size</th>
                    <th>Avg Latency</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <div class="section">
        <h2>🗑️ Recent Evicted Entries</h2>
        <table id="evictedTable">
            <thead>
                <tr>
                    <th>Key</th>
                    <th>Type</th>
                    <th>Access Count</th>
                    <th>Compute Cost</th>
                    <th>Size</th>
                    <th>Last Access</th>
                    <th>Evicted At</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <script>
        async function fetchData() {
            try {
                const response = await fetch("/cache/stats");
                const data = await response.json();

                // Movie Cache Metrics
                document.getElementById("evictions").textContent = data.movie_cache.eviction_count;
                document.getElementById("hitRate").textContent = (data.movie_cache.hit_rate * 100).toFixed(2) + "%";
                document.getElementById("avgHitLatency").textContent = data.movie_cache.avg_hit_latency.toFixed(4);
                document.getElementById("avgMissLatency").textContent = data.movie_cache.avg_miss_latency.toFixed(4);

                // Cache Table
                const tbody = document.querySelector("#cacheTable tbody");
                tbody.innerHTML = "";
                for (const [key, entry] of Object.entries(data.movie_cache.entries)) {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td><code>${key}</code></td>
                        <td>${entry.access_count}</td>
                        <td>${new Date(entry.last_access * 1000).toLocaleTimeString()}</td>
                        <td>${entry.type}</td>
                        <td>${entry.compute_cost.toFixed(2)}</td>
                        <td>${entry.size.toFixed(2)}</td>
                        <td>${entry.avg_latency.toFixed(4)}</td>
                    `;
                    tbody.appendChild(row);
                }

                // Evicted Table
                const evictedTbody = document.querySelector("#evictedTable tbody");
                evictedTbody.innerHTML = "";
                for (const e of data.movie_cache.recent_evictions || []) {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td><code>${e.key}</code></td>
                        <td>${e.type}</td>
                        <td>${e.access_count}</td>
                        <td>${e.compute_cost.toFixed(2)}</td>
                        <td>${e.size.toFixed(2)}</td>
                        <td>${new Date(e.last_access * 1000).toLocaleTimeString()}</td>
                        <td>${new Date(e.evicted_at * 1000).toLocaleTimeString()}</td>
                    `;
                    evictedTbody.appendChild(row);
                }

            } catch (err) {
                console.error("Failed to load cache stats:", err);
            }
        }

        fetchData();
        setInterval(fetchData, 3000); // Refresh every 3 seconds
    </script>

</body>
</html>

    """
    return HTMLResponse(content=html)
