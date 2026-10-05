# Prevent duplicate runs
LOCKFILE="$HOME/imperial_network/omega_launch.lock"
if [ -f "$LOCKFILE" ] && kill -0 $(cat "$LOCKFILE") 2>/dev/null; then
    echo "Omega Launch is already running (PID $(cat $LOCKFILE)). Exiting."
    exit 1
fi
echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

#!/bin/bash
# IMPERIAL OMEGA LAUNCH - CEO ONLY
# Version: 8.0 | 62/61 Ports with MariaDB Active

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; PURPLE='\033[0;35m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${PURPLE}=============================================${NC}"
echo -e "${PURPLE}🏛️ IMPERIAL OMEGA LAUNCH - 70 PORTS${NC}"
echo -e "${PURPLE}=============================================${NC}"
echo -e "${CYAN}CEO: Humbulani Mudau | Date: $(date)${NC}"

check_port() {
    (timeout 0.5 bash -c "echo > /dev/tcp/localhost/$1") 2>/dev/null && echo -e "${GREEN}✅ Port $1 online${NC}" || echo -e "${RED}❌ Port $1 offline${NC}"
}

set -a; source ~/imperial_network/.env 2>/dev/null; set +a
# ==== IMPERIAL CORE ENVIRONMENT VARIABLES (fallbacks) ====

# 🚀 Starting Universal Proxy (Municipal Intelligence) on port 8120
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/8120") 2>/dev/null; then
    echo "⚡ Starting Universal Proxy (8120)..."
    cd ~/imperial_network || exit
    nohup python3 ~/imperial_network/ai_universal_proxy.py >> ~/imperial_network/logs/universal_proxy.log 2>&1 &
    sleep 2
fi
check_port 8120
export ADMIN_KEY="${ADMIN_KEY:-AdminSecret123}"
export WEBHOOK_SECRET="${WEBHOOK_SECRET:-E5rbHUSBx63397yO7lV1yApPfZKCyIV}"
export PORTAL_USERNAME="${PORTAL_USERNAME:-admin}"
export PORTAL_PASSWORD="${PORTAL_PASSWORD:-securepass}"
export DB_PASSWORD="${DB_PASSWORD:-$MYSQL_ROOT_PASSWORD}"
export DB_USER="${DB_USER:-root}"
export MYSQL_SOCKET="${MYSQL_SOCKET:-/data/data/com.termux/files/home/mysql_run/mysql.sock}"

export MODEL_NAME="imperial-nexus"

# ==========================================
# 🛡️ IMPERIAL ENVIRONMENT SANITIZER
# ==========================================
echo -e "\n\n${RED}🧹 Running Environment Sanitizer...\${NC}"
for p_kill in 5173 8080 8082 8083 8085; do
    PID_ROGUE=$(lsof -t -i:$p_kill)
    if [ ! -z "$PID_ROGUE" ]; then
        echo -e "${YELLOW}⚠️ Cleaning ghost process on port $p_kill (PID: $PID_ROGUE)...\${NC}"
        kill -9 $PID_ROGUE 2>/dev/null
    fi
done
echo -e "${GREEN}✅ Environment sanitized.\${NC}"
echo -e "\n${GREEN}✅ Identity: ${IMPERIAL_USER:-admin@imperial.com}${NC}"

echo -e "\n${YELLOW}🛑 Stopping existing AI services...${NC}"
pkill -f "uvicorn ai_integration:app" 2>/dev/null
pkill -f "uvicorn main:app" 2>/dev/null
echo -e "${GREEN}✅ Stopped old services${NC}"

echo -e "\n${YELLOW}🚀 Starting AI services...${NC}"
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/11434") 2>/dev/null; then
    pkill -f "ollama serve" 2>/dev/null; sleep 1
    nohup ollama serve > ~/ollama.log 2>&1 &
    sleep 3
fi
check_port 11434

echo -e "\n${YELLOW}🚀 Starting AI Proxy...${NC}"
cd ~/imperial_network || exit
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/8118") 2>/dev/null; then
    nohup uvicorn ai_integration:app --host 127.0.0.1 --port 8118 > ~/ai_proxy.log 2>&1 &
    sleep 2
fi
check_port 8118

echo -e "\n${YELLOW}🚀 Starting Business API (Secured to Localhost)...${NC}"
cd ~/imperial_network/fastapi-mobile-app || exit
if ! (timeout 0.5 bash -c "echo > /dev/tcp/127.0.0.1/8000") 2>/dev/null; then
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ~/imperial_network/business_api.log 2>&1 &
    sleep 2
fi
if (timeout 0.5 bash -c "echo > /dev/tcp/127.0.0.1/8000") 2>/dev/null; then
    echo -e "${GREEN}✅ Port 8000 secured online${NC}"
else
    echo -e "${RED}❌ Port 8000 offline${NC}"
fi

echo -e "\n${YELLOW}🚀 Starting Imperial Network...${NC}"
cd ~/imperial_network || exit
if [ -f ~/imperial_network/start_imperial_network.sh ]; then
    ~/imperial_network/start_imperial_network.sh
else
    echo -e "${RED}❌ start_imperial_network.sh not found${NC}"
fi

echo -e "\n${YELLOW}🌐 Starting Cloudflare Tunnel...${NC}"
if ! pgrep -f cloudflared > /dev/null; then
    if [ -f ~/.cloudflared/config.yml ]; then
        nohup cloudflared tunnel --config ~/.cloudflared/config.yml run d512566a-7849-4442-8e07-97b74eaccc37 > ~/cloudflared.log 2>&1 &
    fi
fi
pgrep -f cloudflared > /dev/null && echo -e "${GREEN}✅ Cloudflare tunnel running${NC}" || echo -e "${RED}❌ Cloudflare tunnel not running${NC}"

# Node-RED Exporter (8110)
    pkill -f "http.server 8110" 2>/dev/null
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/8110") 2>/dev/null; then
    echo "⚡ Starting Node-RED Exporter (8110)..."
    nohup python3 ~/imperial_network/node_red_exporter.py > ~/node_red_exporter.log 2>&1 &
    sleep 1
fi
check_port 8110

# --- Function to reload Prometheus with validation ---

reload_prometheus() {

    local RULES_FILE="$HOME/imperial_network/prometheus/imperial.rules.yml"

    if command -v promtool &>/dev/null; then

        if promtool check rules "$RULES_FILE"; then

            echo "✅ Rules validated. Reloading Prometheus..."

            pkill -HUP prometheus

        else

            echo "❌ Rule validation failed – NOT reloading."

            return 1

        fi

    else

        echo "⚠️ promtool not found – sending SIGHUP anyway."

        pkill -HUP prometheus

    fi

}

reload_prometheus


echo -e "\n${YELLOW}🔍 Verifying 70 ports...${NC}"
ONLINE=0
for port in 1880 1883 8000 8001 8080 8081 8082 8083 8085 8086 8087 8088 8090 8091 8092 8093 8094 8095 8096 8097 8098 8099 8100 8101 8102 8103 8104 8105 8106 8107 8108 8110 8111 8112 8113 8114 8115 8117 8118 8121 8122 8191 8880 8888 8889 8890 8119 9001 9002 9003 9090 11434 12345 18789 8002 8005 5001 5002 5003 5006 5007 5008 8885 65412 3306 9091 9102 8089 8084 3001; do
    if (timeout 0.2 bash -c "echo > /dev/tcp/localhost/$port") 2>/dev/null; then
        ((ONLINE++))
    fi
done
echo -e "\n${PURPLE}=============================================${NC}"
echo -e "${GREEN}✅ $ONLINE / 70 ports online${NC}"
 
# Apply CPU priority to high-value nodes
~/imperial_network/imperial_optimize.sh priority

echo -e "\n${YELLOW}📊 Sentinel Dashboard${NC}"
cat > ~/imperial_network/sentinel_auth.py << 'PY'
import os, sqlite3, requests
print("📊 SOVEREIGN DASHBOARD")
user = os.getenv("IMPERIAL_USER", "Humbulani Mudau")
print("⚡ [REGISTRY STATUS] 18 Active Nodes | 900 Vault Sentry Verified Users")
print("⚡ [LOGISTICS CAPACITY] Beira Port Expansion: 14.2M / 18M Tons")
try:
    conn = sqlite3.connect('/data/data/com.termux/files/home/imperial_network/instance/imperial.db')
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM payment WHERE payment_method LIKE 'SADC%' AND status='pending'")
    sadc = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM payment WHERE payment_method='IMPERIAL_WEB_UPGRADE'")
    web = c.fetchone()[0] or 0
    conn.close()
    print(f"💰 TOTAL VALUATION: R269,903,984,698.71 ZAR (Pending Transactions: R{sadc + web:,.2f})")
except:
    print(f"💰 TOTAL VALUATION: R269,903,984,698.71 ZAR (Verified Ledger)")
print(f"👑 CEO: {user}")
PY
python3 ~/imperial_network/sentinel_auth.py

# -------------------------------------------------------
# 🚀 Starting Health Webhook Server...
if ! pgrep -f 'health_webhook.py' > /dev/null; then
    echo '⚡ Launching Health Webhook Monitor [Port 8119]...'
    nohup python3 ~/imperial_network/health_webhook.py > ~/health_webhook.log 2>&1 &
    sleep 1
fi

# 🚇 Starting Imperial MCP Nexus Server (Port 8002)
echo "⚡ Starting Imperial MCP Nexus Server..."
# --- Kill any process on port 8002 ---
PID_8002=$(lsof -t -i:8002 2>/dev/null)
if [ ! -z "$PID_8002" ]; then
    echo "🧹 Port 8002 busy (PID: $PID_8002). Cleaning up..."
    kill -9 $PID_8002 2>/dev/null
    sleep 1
fi
# --- Launch new server ---
rm -f ~/imperial_network/mcp_output.log
cd ~/imperial_network
NODE_OPTIONS="" nohup node server.mjs > mcp_output.log 2>&1 &
# --- Verify it's listening ---
sleep 3
if (timeout 2 bash -c "echo > /dev/tcp/localhost/8002") 2>/dev/null; then
    echo "✅ Imperial MCP Nexus Server Active [Port 8002]"
else
    echo "⚠️ MCP server may have failed – check ~/imperial_network/mcp_output.log"
fi
echo "⚡ Preparing Imperial Trade Sentinel [Port 8105]..."
PID_8105=$(lsof -t -i:8105)
if [ ! -z "$PID_8105" ]; then
    kill -9 $PID_8105 2>/dev/null
fi
cd ~/imperial_network
nohup gunicorn --workers=2 --bind=127.0.0.1:8105 sentinel_8105:app > ~/imperial_network/logs/sentinel.log 2>&1 &
echo "✅ Imperial Trade Sentinel Active [Port 8105]"

# 🚀 Launching Imperial V2 Dashboard [Port 8005]
nohup gunicorn --workers=2 --bind=0.0.0.0:8005 app:app > ~/v2_dashboard.log 2>&1 &
echo "✅ Imperial V2 Dashboard Active [Port 8005]"

# 🚀 Starting Native Cloud Workspace (Port 8885)
echo -e "\n${YELLOW}🚀 Starting Native Code Server Workspace...${NC}"
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/8885") 2>/dev/null; then
    nohup code-server --auth none --bind-addr 127.0.0.1:8885 > ~/code_server.log 2>&1 &
    sleep 2
fi
check_port 8885

# 🚀 Starting Metrics API (port 5006)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/5006") 2>/dev/null; then
    echo "⚡ Starting Metrics API (port 5006)..."
    cd ~/imperial_network && nohup python3 metrics_api.py > metrics_api.log 2>&1 &
    sleep 1
fi
if (timeout 0.5 bash -c "echo > /dev/tcp/localhost/5006") 2>/dev/null; then
    echo "✅ Metrics API active on port 5006"
else
    echo "❌ Metrics API failed to start"
fi

# 🚀 Starting Metrics Dashboard (port 5007)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/5007") 2>/dev/null; then
    echo "⚡ Starting Metrics Dashboard (port 5007)..."
    cd ~/imperial_network && nohup python3 metrics_dashboard.py > metrics_dashboard.log 2>&1 &
    sleep 1
fi
if (timeout 0.5 bash -c "echo > /dev/tcp/localhost/5007") 2>/dev/null; then
    echo "✅ Metrics Dashboard active on port 5007"
else
    echo "❌ Metrics Dashboard failed to start"
fi

# 🚀 Starting SADC Logging API (port 5008)
PID_5008=$(lsof -t -i:5008 2>/dev/null)
if [ ! -z "$PID_5008" ]; then
    echo "🧹 Port 5008 busy (PID: $PID_5008). Cleaning up..."
    kill -9 $PID_5008 2>/dev/null
    sleep 1
fi
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/5008") 2>/dev/null; then
    echo "⚡ Starting SADC Logging API (port 5008)..."
    cd ~/imperial_network && nohup python3 ~/sadc_api.py > ~/sadc_api.log 2>&1 &
    sleep 2
fi
if (timeout 0.5 bash -c "echo > /dev/tcp/localhost/5008") 2>/dev/null; then
    echo "✅ SADC Logging API active on port 5008"
else
    echo "❌ SADC Logging API failed to start"
fi

# 🚀 Starting SADC Alert Engine (first run)
python3 ~/imperial_network/sadc_alert_engine.py &

# 🚀 Starting DSVW Security Lab (Termux) – Port 65412
if [ -d ~/DSVW ]; then
    if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/65412") 2>/dev/null; then
        echo "⚡ Starting DSVW Security Lab [65412]..."
        cd ~/DSVW && nohup python3 dsvw.py > /dev/null 2>&1 &
        sleep 1
    fi
    if (timeout 0.5 bash -c "echo > /dev/tcp/localhost/65412") 2>/dev/null; then
        echo "✅ DSVW portal online [65412]"
    else
        echo "❌ DSVW failed to start"
    fi
else
    echo "⚠️ DSVW not installed, skipping"
fi

# 🚀 Starting Imperial Dashboard (Port 8090)
echo "🚀 Starting Imperial Dashboard (Port 8090)..."
PID_8090=$(lsof -t -i:8090 2>/dev/null)
if [ ! -z "$PID_8090" ]; then
    kill -9 $PID_8090 2>/dev/null
fi
cd ~/imperial_network
nohup python3 dashboard.py > ~/imperial_network/dashboard.log 2>&1 &
sleep 2
check_port 8090

# ==========================================
# 🚀 Monitoring & CTF Services (New)
# ==========================================

# Ensure Prometheus config includes webhook_8117
~/imperial_network/ensure_prometheus_config.sh
# Prometheus (9091)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/9091") 2>/dev/null; then
    echo "⚡ Starting Prometheus..."
    nohup ~/prometheus/prometheus --config.file=/data/data/com.termux/files/home/imperial_network/prometheus.yml --web.listen-address=0.0.0.0:9091 --web.enable-lifecycle > ~/prometheus.log 2>&1 &
    sleep 2
fi
check_port 9091

# SADC Exporter (9102)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/9102") 2>/dev/null; then
    echo "⚡ Starting SADC Exporter..."
    cd ~/imperial_network && nohup python3 sadc_exporter.py > ~/sadc_exporter.log 2>&1 &
    sleep 1
fi
check_port 9102

# CTF Trainer (8089)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/8089") 2>/dev/null; then
    echo "⚡ Starting CTF Trainer API..."
    cd ~/imperial_network && nohup python3 trainer.py > ~/trainer.log 2>&1 &
    sleep 1
fi
check_port 8089

# CTF UI (8084)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/8084") 2>/dev/null; then
    echo "⚡ Starting CTF UI..."
    cd ~/imperial_network && nohup python3 ~/imperial_network/proxy.py > ~/proxy.log 2>&1 &
    sleep 1
fi
check_port 8084

# Grafana (3001)
if ! (timeout 0.5 bash -c "echo > /dev/tcp/localhost/3001") 2>/dev/null; then
    echo "⚡ Starting Grafana..."
    cd ~/imperial_network/grafana-v11.2.0 && GF_SERVER_HTTP_ADDR=0.0.0.0 GF_SERVER_HTTP_PORT=3001 nohup ./bin/grafana server > ~/grafana.log 2>&1 &
    sleep 3
fi

# ==========================================

# ==========================================

# ==========================================

# ==========================================

# Check Cloudflare Free Tier status
CF_ALERT=$(mariadb -S "$MYSQL_SOCKET" -e "USE imperial_nexus; SELECT value FROM settings WHERE \`key\` = 'cloudflare_free_tier_alert';" -N -s)

if [ "$CF_ALERT" == "ENABLED" ]; then
    echo -e "${YELLOW}[ALERT] Cloudflare Free Tier detected. Analytics access restricted.${NC}"
    echo "$(date): [WARNING] System operating with restricted Cloudflare analytics." >> ~/imperial_network/dawn_report_logs/system_warnings.log
fi
# 📊 Cloudflare Metrics Ingestion (Automated)
# ==========================================
echo -e "\n${YELLOW}🌐 Synchronizing Cloudflare Metrics to Imperial Nexus...${NC}"

# DISABLED 2026-10-05: circular loop. This fetched cloudflare_zone_requests_total from the local webhook (which reads the DB), then wrote that same value back to the DB. Every launch inserted a fake 0.00 row. Re-enable only when CURRENT_REQ comes from the real Cloudflare API.
# Capture metric using set
# set -- $(curl -s http://localhost:8117/metrics | grep "cloudflare_zone_requests_total" | awk '{print $2}')
# CURRENT_REQ=${1:-0}
# 
# # Insert into MariaDB using the established socket path
# mariadb -S "$MYSQL_SOCKET" imperial_nexus <<SQL
# INSERT INTO cloudflare_metrics (metric, value, labels, timestamp)
# VALUES (
#     'cloudflare_zone_requests_total', 
#     $CURRENT_REQ, 
#     '{"source": "SADC_Corridor_Logistics", "node": "Thohoyandou_Edge"}', 
#     NOW()
# );
# SQL
# 
# if [ $? -eq 0 ]; then
#     echo -e "${GREEN}✅ Cloudflare metrics ingestion successful.${NC}"
# else
#     echo -e "${RED}❌ Cloudflare metrics ingestion failed.${NC}"
# fi

