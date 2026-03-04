"""Bot Status Dashboard - Real-time monitoring for Polymarket and Binance traders."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
import json
from typing import Dict, Any

app = FastAPI(title="Bot Status Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# In-memory storage (lost on restart, but fine for demo)
bot_status = {
    "polymarket": None,
    "binance": None,
    "last_updated": None
}

# Simple auth token for update endpoint
UPDATE_TOKEN = os.getenv("DASHBOARD_UPDATE_TOKEN", "change-me-secret-token")

@app.post("/api/update")
async def update_status(request: Request):
    """Receive status update from bots. Expects JSON: {"source": "polymarket"|"binance", "data": {...}}"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ")[1] != UPDATE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    source = payload.get("source")
    data = payload.get("data")

    if source not in ["polymarket", "binance"]:
        raise HTTPException(status_code=400, detail="Invalid source")

    bot_status[source] = data
    bot_status["last_updated"] = datetime.utcnow().isoformat()

    return {"status": "ok"}

@app.get("/api/status")
async def get_status():
    """Return current bot status."""
    return bot_status

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Simple dashboard page."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Status Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f5f5f5; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .last-updated { color: #666; font-size: 0.9em; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { margin-top: 0; color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
        th { background: #f0f0f0; font-weight: bold; }
        .no-data { color: #999; font-style: italic; }
        .metric { margin: 10px 0; }
        .metric-label { font-weight: bold; }
        .positive { color: green; }
        .negative { color: red; }
        meta { refresh: 30; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Bot Status Dashboard</h1>
        <div class="last-updated" id="last-updated">Loading...</div>
    </div>
    <div class="grid">
        <div class="card" id="polymarket-card">
            <h2>Polymarket Trader</h2>
            <div id="polymarket-content">Loading...</div>
        </div>
        <div class="card" id="binance-card">
            <h2>Binance AI Trader</h2>
            <div id="binance-content">Loading...</div>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                document.getElementById('last-updated').textContent = 'Last updated: ' + (data.last_updated || 'Never');

                // Polymarket
                const pm = data.polymarket;
                const pmDiv = document.getElementById('polymarket-content');
                if (pm) {
                    pmDiv.innerHTML = `
                        <div class="metric"><span class="metric-label">Balance:</span> $${pm.balance_usdt.toFixed(2)}</div>
                        <h3>Positions (${pm.positions.length})</h3>
                        ${pm.positions.length === 0 ? '<p class="no-data">No open positions</p>' : `
                        <table>
                            <tr><th>Market</th><th>Entry</th><th>Shares</th><th>Cost</th></tr>
                            ${pm.positions.map(p => `
                                <tr>
                                    <td>${p.name}</td>
                                    <td>$${p.entry_price.toFixed(4)}</td>
                                    <td>${p.shares.toFixed(2)}</td>
                                    <td>$${p.cost.toFixed(2)}</td>
                                </tr>
                            `).join('')}
                        </table>
                        `}
                    `;
                } else {
                    pmDiv.innerHTML = '<p class="no-data">No data received yet</p>';
                }

                // Binance
                const bn = data.binance;
                const bnDiv = document.getElementById('binance-content');
                if (bn) {
                    const total = parseFloat(bn.cash) + (bn.positions ? bn.positions.reduce((sum, p) => sum + parseFloat(p.current_price || p.entry_price) * parseFloat(p.shares), 0) : 0);
                    const pnl = parseFloat(bn.total_pnl || 0);
                    const pnlClass = pnl >= 0 ? 'positive' : 'negative';
                    bnDiv.innerHTML = `
                        <div class="metric"><span class="metric-label">Cash:</span> $${parseFloat(bn.cash).toFixed(2)}</div>
                        <div class="metric"><span class="metric-label">Total P&L:</span> <span class="${pnlClass}">$${pnl.toFixed(2)}</span></div>
                        <h3>Positions (${bn.positions ? bn.positions.length : 0})</h3>
                        ${!bn.positions || bn.positions.length === 0 ? '<p class="no-data">No open positions</p>' : `
                        <table>
                            <tr><th>Symbol</th><th>Entry</th><th>Current</th><th>Shares</th><th>PnL %</th></tr>
                            ${bn.positions.map(p => {
                                const cur = parseFloat(p.current_price);
                                const entry = parseFloat(p.entry_price);
                                const pnlPct = ((cur - entry) / entry * 100).toFixed(2);
                                const pnlClass = pnlPct >= 0 ? 'positive' : 'negative';
                                return `
                                <tr>
                                    <td>${p.symbol}</td>
                                    <td>$${entry.toFixed(4)}</td>
                                    <td>$${cur.toFixed(4)}</td>
                                    <td>${parseFloat(p.shares).toFixed(2)}</td>
                                    <td class="${pnlClass}">${pnlPct}%</td>
                                </tr>
                                `;
                            }).join('')}
                        </table>
                        `}
                    `;
                } else {
                    bnDiv.innerHTML = '<p class="no-data">No data received yet</p>';
                }

            } catch (e) {
                console.error('Fetch error:', e);
            }
        }

        // Initial fetch + refresh every 30s
        fetchStatus();
        setInterval(fetchStatus, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
