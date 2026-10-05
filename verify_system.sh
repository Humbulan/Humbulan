#!/bin/bash
# IMPERIAL SYSTEM VERIFIER
# Tests all critical components and prints a status report

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 IMPERIAL SYSTEM VERIFICATION${NC}"
echo "====================================="
echo "Date: $(date)"
echo

# 1. MariaDB
echo -n "📊 MariaDB: "
if mariadb -h 127.0.0.1 -e "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✅ Connected (TCP/IP)${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# 2. Port status (key ports)
declare -a PORTS=(
    8000 8001 8080 8090 8118 8117 9091 3001 1880 1883 8888 9090 5006 5007 5008 65412 8885 8105 8002 8005
)
ONLINE=0
OFFLINE=0
echo -n "🔌 Ports online: "
for p in "${PORTS[@]}"; do
    if timeout 1 bash -c "echo > /dev/tcp/localhost/$p" 2>/dev/null; then
        ((ONLINE++))
    else
        ((OFFLINE++))
    fi
done
echo -e "${GREEN}${ONLINE}${NC} / ${#PORTS[@]} (${OFFLINE} offline)"

# 3. Prometheus
echo -n "📈 Prometheus: "
if curl -s http://localhost:9091/-/healthy | grep -q "Prometheus" 2>/dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

# 4. Grafana
echo -n "📊 Grafana: "
if curl -s -u admin:admin http://localhost:3001/api/health 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}✅ Accessible (admin/admin)${NC}"
else
    echo -e "${RED}❌ Not accessible${NC}"
fi

# 5. Webhook (port 8117)
echo -n "🔔 Webhook 8117: "
if curl -s http://localhost:8117/metrics | head -1 | grep -q "HELP" 2>/dev/null; then
    echo -e "${GREEN}✅ Responding${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

# 6. Node-RED
echo -n "⚡ Node-RED: "
if timeout 1 bash -c "echo > /dev/tcp/localhost/1880" 2>/dev/null; then
    echo -e "${GREEN}✅ Port open${NC}"
    # Check if flows endpoint returns (ignore error)
    curl -s http://localhost:1880/flows > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "   ${GREEN}✅ Flows endpoint accessible${NC}"
    else
        echo -e "   ${YELLOW}⚠️ Flows endpoint not JSON (non-critical)${NC}"
    fi
else
    echo -e "${RED}❌ Not reachable${NC}"
fi

# 7. Community Safety Feed
echo -n "🚨 Community Incidents: "
feed=$(curl -s http://localhost:8000/community-safety-feed 2>/dev/null)
if [ $? -eq 0 ] && echo "$feed" | jq -e .incidents >/dev/null 2>&1; then
    count=$(echo "$feed" | jq '.incidents | length')
    echo -e "${GREEN}✅ ${count} incidents${NC}"
else
    echo -e "${RED}❌ Feed not available${NC}"
fi

# 8. Database tables (quick counts)
echo -n "🗄️  Database tables: "
counts=$(mariadb -h 127.0.0.1 -e "USE imperial_nexus; SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM payment;" 2>/dev/null)
if [ $? -eq 0 ]; then
    users=$(echo "$counts" | sed -n '2p')
    payments=$(echo "$counts" | sed -n '4p')
    echo -e "${GREEN}✅ users=${users:-0}, payments=${payments:-0}${NC}"
else
    echo -e "${RED}❌ Query failed${NC}"
fi

# 9. WhatsApp sender (test if script exists)
echo -n "📱 WhatsApp sender: "
if [ -f ~/imperial_network/send_whatsapp.sh ]; then
    echo -e "${GREEN}✅ Script present${NC}"
else
    echo -e "${RED}❌ Script missing${NC}"
fi

# 10. Environment variables (key ones)
echo -n "🌐 Environment: "
if [ -n "$DB_PASSWORD" ] && [ -n "$MYSQL_HOST" ]; then
    echo -e "${GREEN}✅ DB_PASSWORD & MYSQL_HOST set${NC}"
else
    echo -e "${YELLOW}⚠️ Not all vars set (may be fine)${NC}"
fi

echo
echo "====================================="
echo -e "${YELLOW}✅ Verification complete.${NC}"
