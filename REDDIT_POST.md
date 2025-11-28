# Tesla Sync - Complete Tesla Powerwall + Amber Electric Integration for Australia

**TL;DR:** Open-source tool that automatically syncs Amber Electric's real-time pricing to your Tesla Powerwall every 5 minutes, maximizes AEMO spike revenue, prevents negative feed-in losses, and provides comprehensive energy monitoring. Works standalone via Docker OR as a native Home Assistant integration.

---

## What It Does

If you have a Tesla Powerwall and Amber Electric in Australia, this integration optimizes your battery automatically:

- **Automatic TOU Sync** - Updates your Powerwall with Amber's dynamic pricing every 5 minutes
- **AEMO Spike Detection** - Automatically exports during wholesale price spikes ($300+/MWh) to maximize revenue
- **Solar Curtailment** - Prevents exporting during negative pricing periods (saves you from paying to export)
- **Real-time Monitoring** - Dashboard showing live prices, battery status, and energy flow
- **Price Forecasting** - 30-minute price forecast visualization
- **Custom TOU Schedules** - Works with ANY retailer, not just Amber

---

## Two Ways to Deploy

### Option 1: Docker (Standalone Web Dashboard)
Full-featured web interface with comprehensive monitoring and controls.

### Option 2: Home Assistant Integration (HACS)
Native HA integration with sensors, switches, and services for automation.

**Both options provide the same core functionality - choose based on your preference!**

---

## Core Features (Both Versions)

### 1. Automatic TOU Tariff Syncing
- Updates Tesla Powerwall every 5 minutes with latest Amber pricing
- Converts Amber's 5-minute intervals into 30-minute Tesla periods (averaging for accuracy)
- Uses WebSocket for real-time prices with REST API fallback
- Rolling 24-hour window ensures Tesla always has lookahead data
- Smart period alignment (Amber uses end-time labels, Tesla uses start-time)

### 2. AEMO Wholesale Price Spike Detection
**Perfect for VPP customers (GLOBIRD, AGL, ENGIE) where Tesla batteries aren't natively supported.**

- Monitors AEMO NEM wholesale prices every minute
- Configurable threshold (e.g., $300/MWh)
- When spike detected:
  - Saves current tariff and operation mode
  - Switches Powerwall to autonomous mode (TOU)
  - Uploads spike tariff with very high sell rates
  - Battery exports to grid during spike
- When spike ends:
  - Restores original tariff
  - **Automatically restores your previous operation mode** (self-consumption/autonomous/backup)
- Works seamlessly regardless of your normal Powerwall settings

### 3. Solar Curtailment (Negative Price Protection)
- Monitors feed-in prices every minute
- When export price ≤ 0¢/kWh:
  - Sets Powerwall export to "never" (prevents paying to export)
  - Includes Tesla API bug workaround (toggle to force apply)
- When export price > 0¢/kWh:
  - Restores export to "battery_ok" (normal operation)
- Opt-in feature (disabled by default)

### 4. Real-Time Energy Monitoring
- Solar generation (W/kW)
- Battery charge/discharge (W/kW)
- Grid import/export (W/kW)
- Home consumption (W/kW)
- Battery state of charge (%)
- All metrics updated every 30 seconds

### 5. Price Monitoring & Forecasting
- Current 5-minute import/export prices
- Renewable energy percentage
- 30-minute price forecast (next 6 intervals)
- Color-coded price indicators (green/yellow/orange/red)
- Max daily price tracking
- Historical 7-day price charts

---

## Docker-Only Features

### Dashboard Web Interface
- **Connection Status** - Real-time Amber & Tesla API health
- **AEMO Price Monitor** - Live wholesale prices with spike status
- **Amber Live Pricing** - Current 5-min interval with forecast dots
- **Tesla Powerwall Status** - Battery %, power flows, firmware version
- **24-Hour TOU Schedule** - Rolling tariff view with current period highlighted
- **Price History Charts** - 7-day historical data
- **Energy Usage Tracking** - Solar/Grid/Battery/Load with daily totals
- **Energy Summaries** - Period-based summaries (day/week/month/year)

### Advanced Configuration
- **API Settings** - Configure Amber, Teslemetry, or Tesla Fleet API
- **Demand Charge Tracking** - Peak/shoulder/off-peak capacity charges
- **Timezone Support** - All Australian timezones with auto-detection
- **TOU Profile Manager** - Save/restore favorite tariff configurations
- **Custom TOU Creation** - Build tariffs for any provider
- **Logs Viewer** - Filterable application logs with download

### Background Automation
- **Automatic TOU Sync** - Every 5 minutes (aligned with Amber updates)
- **Price History Collection** - Every 5 minutes for all active users
- **Energy Usage Logging** - Every minute (Teslemetry 1/min rate limit)
- **AEMO Monitoring** - Every minute for responsive spike detection
- **Solar Curtailment Check** - Every minute

### Data Persistence
- **Price Records Database** - Every Amber price update stored
- **Energy Records Database** - 30-second granular power tracking
- **Saved TOU Profiles** - Backup/restore tariff configurations
- **User Management** - Secure single-user account system

---

## Home Assistant Features

### Native Integration
- **HACS Installation** - One-click install and updates
- **Config Flow** - Guided setup with auto-discovery
- **Automatic Discovery** - Finds your Tesla sites via Teslemetry

### Sensors (Real-time)
- `sensor.current_electricity_price` - Current Amber import price ($/kWh)
- `sensor.solar_power` - Solar generation (kW)
- `sensor.grid_power` - Grid import/export (kW, positive = import)
- `sensor.battery_power` - Battery charge/discharge (kW, positive = discharge)
- `sensor.home_load` - Home consumption (kW)
- `sensor.battery_level` - Battery state of charge (%)
- Additional price attributes: spike status, wholesale price, network price

### Demand Charge Sensors (if enabled)
- `sensor.in_demand_charge_period` - Currently in peak demand window
- `sensor.peak_demand_this_cycle` - Peak kW this billing cycle
- `sensor.estimated_demand_charge_cost` - Estimated capacity charge ($)
- `sensor.daily_supply_charge_cost_this_month` - Daily supply charges accumulated ($)
- `sensor.monthly_supply_charge` - Fixed monthly charge ($)
- `sensor.total_estimated_monthly_cost` - Total bill estimate ($)

### Switches
- `switch.auto_sync_tou_schedule` - Enable/disable automatic 5-min syncing
- State attributes: last sync time, sync status

### Services
```yaml
# Manual TOU sync (uses wait-with-timeout pattern)
service: tesla_amber_sync.sync_tou_schedule

# Refresh sensor data immediately
service: tesla_amber_sync.sync_now
```

### Automatic Background Sync
- Runs every 5 minutes automatically when switch is ON
- No automations required (but you can create advanced ones)
- WebSocket-first with REST fallback
- Prevents duplicate syncs within same 5-min period

### Example Automations (Optional)
```yaml
# Force sync on extreme price spike
automation:
  - alias: "Force TOU Sync on Price Spike"
    trigger:
      - platform: state
        entity_id: sensor.current_electricity_price
    condition:
      - condition: numeric_state
        entity_id: sensor.current_electricity_price
        above: 0.30
    action:
      - service: tesla_amber_sync.sync_tou_schedule
```

---

## Tesla API Options (Both Versions)

### Option 1: Teslemetry (Recommended - $3/month)
**Pros:**
- Simple API key setup (2 minutes)
- Works with localhost (no public domain needed)
- Reliable proxy service
- Works identically in Docker and Home Assistant

**Setup:**
1. Sign up at https://teslemetry.com
2. Connect Tesla account
3. Copy API key
4. Enter during setup

### Option 2: Tesla Fleet API (FREE)
**Pros:**
- Completely free
- Direct Tesla API access via OAuth
- Automatic token refresh

**Cons:**
- OAuth app registration required
- More complex setup

**Docker Setup:**
- Configure via Settings page web GUI
- Enter Client ID and Client Secret
- Credentials encrypted and stored

**Home Assistant Setup:**
1. Install official "Tesla Fleet" integration
2. Complete OAuth flow
3. Leave Teslemetry token blank during Tesla Sync setup
4. Auto-detects and uses Tesla Fleet tokens

---

## Key Technical Details

### Intelligent Price Conversion
1. **Smart Period Mapping** - Auto-aligns Amber's end-time labels with Tesla's start-time format
2. **5-Minute Averaging** - Six 5-min intervals averaged per 30-min Tesla period
3. **Rolling 24-Hour Window** - Past periods use tomorrow's forecast, future periods use today's
4. **Timezone Auto-Detection** - Works in all Australian states (QLD/NSW/VIC/SA/TAS/WA/NT)
5. **Precision Matching** - 4 decimal places with trailing zero removal

### WebSocket + REST Hybrid Approach
1. WebSocket provides real-time Amber price updates
2. At :00 of each 5-min period, waits up to 60s for WebSocket
3. If WebSocket delivers data → Use real-time prices immediately
4. If timeout (60s) → Fallback to REST API
5. Only ONE sync per 5-minute period (prevents duplicates)

### Security
- All API tokens encrypted at rest (Fernet encryption)
- Passwords hashed with Werkzeug
- CSRF protection via Flask-WTF
- OAuth2 state parameter validation
- Private keys never exposed

---

## Screenshots

### Docker Web Dashboard
- API Configuration: https://i.imgur.com/Lrk87Ti.png
- AEMO Wholesale Monitor: https://i.imgur.com/dTksjzx.png
- Amber Live Pricing: https://i.imgur.com/TurU9f1.jpeg
- Tesla Powerwall Status: https://i.imgur.com/ZxU4bgw.png
- 24H TOU Schedule: https://i.imgur.com/PgkfMwH.png
- Price History: https://i.imgur.com/1fCrMsW.png
- Energy Usage: https://i.imgur.com/1BEp6s7.png
- Energy Summaries: https://i.imgur.com/dskv5Os.png

**Full Gallery:** https://imgur.com/a/TdzIgYT

---

## Installation

### Docker (Standalone)

**Using Docker Hub (Easiest):**
```bash
# Download compose file
curl -O https://raw.githubusercontent.com/bolagnaise/tesla-sync/main/docker/docker-compose.hub.yml

# Create data directory
mkdir -p ./data

# Start container
docker-compose -f docker-compose.hub.yml up -d

# Access dashboard
open http://localhost:5001
```

**Using Docker Run:**
```bash
mkdir -p $(pwd)/data

docker run -d \
  --name tesla-sync \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key-here \
  --restart unless-stopped \
  bolagnaise/tesla-sync:latest
```

### Home Assistant (HACS)

1. **Install via HACS**
   - Open HACS → Three dots → Custom repositories
   - Add: `https://github.com/bolagnaise/tesla-sync`
   - Category: Integration
   - Download and restart HA

2. **Add Integration**
   - Settings → Devices & Services → Add Integration
   - Search "Tesla Sync"

3. **Configure**
   - Enter Amber API token (get from https://app.amber.com.au/developers)
   - Enter Teslemetry token OR leave blank to use Tesla Fleet
   - Select Tesla energy site
   - Enable auto-sync (recommended)

---

## Use Cases

### 1. Amber Electric Customers
- Automatic TOU updates with real-time pricing
- Solar curtailment during negative pricing
- Price spike protection

### 2. VPP Customers (GLOBIRD, AGL, ENGIE)
- AEMO spike detection for wholesale export
- Automatic mode switching during spikes
- Restore to normal operation after spike

### 3. Any Australian Retailer
- Create custom TOU schedules
- Manual tariff management
- Demand charge tracking

### 4. Home Automation Enthusiasts
- Native Home Assistant integration
- Real-time energy sensors for dashboards
- Advanced automation possibilities

---

## Tech Stack

### Docker Version
- **Backend:** Flask (Python)
- **Server:** Gunicorn (4 workers)
- **Database:** SQLite (PostgreSQL supported)
- **Scheduler:** APScheduler
- **Frontend:** HTML/CSS/JavaScript, Chart.js
- **Docker:** Multi-arch (amd64/arm64)

### Home Assistant Version
- **Integration:** Native HA custom component
- **Coordinators:** Amber Price, Tesla Energy, Demand Charge
- **WebSocket:** Real-time Amber price streaming
- **Platforms:** Sensor, Switch
- **Services:** TOU sync, Data refresh

---

## Links

- **GitHub:** https://github.com/bolagnaise/tesla-sync
- **Docker Hub:** https://hub.docker.com/r/bolagnaise/tesla-sync
- **Documentation:** See README.md
- **Issues/Support:** https://github.com/bolagnaise/tesla-sync/issues

---

## Why I Built This

Tesla's Powerwall is great, but manually updating TOU schedules with Amber's constantly changing prices is tedious. Tesla doesn't natively support dynamic pricing retailers in Australia, and AEMO spike opportunities are impossible to catch manually.

This tool automates everything - from price syncing to spike detection to negative price protection - while providing comprehensive monitoring whether you prefer Docker or Home Assistant.

---

## Contributing

Open source and contributions welcome! MIT License.

**Support development:** https://paypal.me/benboller

---

**Questions? Drop them below!**

Compatible with: Tesla Powerwall, Amber Electric, any Australian electricity retailer (with custom TOU), all Australian states and timezones.
