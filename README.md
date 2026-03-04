# Bot Status Dashboard

Real-time monitoring dashboard for your Polymarket and Binance trading bots.

## Features

- Auto-refreshing web UI (every 30 seconds)
- Shows balance, positions, P&L for both bots
- Simple push-based updates from bots
- Deploy to Railway (free)

## How It Works

1. Bots POST their status to `/api/update` after each run
2. Dashboard stores latest status in memory
3. Web page polls `/api/status` and renders tables

## Setup

### Deploy to Railway

1. Create new project from GitHub: `ClawKazmu/bot-status-dashboard`
2. Set environment variable `DASHBOARD_UPDATE_TOKEN` to a secret string
3. Deploy
4. Note the URL (e.g., `https://bot-status-dashboard.up.railway.app`)

### Configure Bots

In each bot's script, add at the end of `main()`:

```python
import requests
DASHBOARD_URL = "https://bot-status-dashboard.up.railway.app/api/update"
TOKEN = os.getenv("DASHBOARD_UPDATE_TOKEN", "your-secret-token")

# Build status payload (example for Polymarket)
payload = {
    "source": "polymarket",
    "data": {
        "balance_usdt": account['balance_usdt'],
        "positions": account['positions'],
        # Add any other fields you want to monitor
    }
}

try:
    requests.post(DASHBOARD_URL, json=payload, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
except Exception as e:
    print(f"Failed to send dashboard update: {e}")
```

Do similarly for Binance with `source: "binance"`.

## Endpoints

- `GET /` — Dashboard UI
- `GET /api/status` — JSON of latest bot statuses
- `POST /api/update` — Push new status (requires `Authorization: Bearer <token>`)

## Example curl

```bash
curl -X POST https://your-dashboard.up.railway.app/api/update \
  -H "Authorization: Bearer YOUR_SECRET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"polymarket","data":{"balance_usdt":15.5,"positions":[{"name":"Test","shares":100,"entry_price":0.05,"cost":5}]}'
```

## Security

- The `/api/update` endpoint requires a Bearer token set in `DASHBOARD_UPDATE_TOKEN`
- The `/api/status` endpoint is public (anyone can view status)
- If you need to restrict viewing, add auth later.

## License

MIT
