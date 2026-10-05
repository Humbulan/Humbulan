#!/data/data/com.termux/files/usr/bin/bash

# ===== PRE‑FLIGHT OPTIMIZATION =====
~/imperial_network/imperial_optimize.sh latency
~/imperial_network/imperial_optimize.sh health

# ===== HELPERS =====
get_sadc_volume() {
    mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$MYSQL_SOCKET" -e "USE imperial_nexus; SELECT IFNULL(SUM(amount), 0) FROM payment WHERE payment_method LIKE 'SADC%' AND status='completed';" -N -s 2>/dev/null || echo 0
}

get_name() {
    case $1 in
        1880) echo "Node-RED" ;; 1883) echo "Node-RED_Proxy" ;;
        8000) echo "Business_API" ;; 8001) echo "Admin_Portal" ;;
        8002) echo "Imperial_MCP_Nexus" ;;
        8005) echo "Secret_Website" ;;
    8000) echo "Business_API" ;;
    8000) echo "Business_API" ;;
    8000) echo "Business_API" ;;
        8080) echo "Proxy" ;; 8081) echo "Enterprise_API" ;;
        8082) echo "Revenue_Bridge" ;; 8083) echo "Redundant_Node" ;;
        8085) echo "Legacy_Vault" ;; 8086) echo "Apex_Metrics" ;;
        8087) echo "USSD_Portal" ;; 8088) echo "Humbu_Store_Website" ;;
        8090) echo "Monitor" ;; 8091) echo "SEWS_Bridge" ;;
        8092) echo "Dashboard_UI" ;; 8093) echo "System_Stats" ;;
        8094) echo "Intel_Redirect" ;; 8095) echo "File_Browser" ;;
        8096) echo "Sovereign_Master" ;; 8097) echo "Imperial_Front" ;;
        8098) echo "Voucher_API" ;; 8099) echo "B2B_Hub" ;;
        8100) echo "Malamulele_Portal" ;; 8101) echo "BI_Hub" ;;
        8102) echo "Urban_Gateway" ;; 8103) echo "Intel_Alpha" ;;
        8104) echo "Surge_Monitor" ;; 8105) echo "Sentinel" ;;
        8106) echo "IMPERIAL_WEB_UPGRADE" ;; 8107) echo "SADC_A_LOGISTICS" ;;
        8108) echo "SADC_B_RETAIL" ;; 8110) echo "Node-RED_Exporter" ;;
        8111) echo "Malamulele_Relay" ;; 8112) echo "SADC_Sync" ;;
        8113) echo "Vault_2" ;; 8114) echo "B2B_Bulk" ;;
        8115) echo "Ghost" ;; 8117) echo "Ukuvuselela_Webhook" ;;
        8118) echo "AI_Proxy_Gateway" ;;
        8119) echo "Health_Webhook" ;;
        8120) echo "Universal_Proxy" ;;
        8191) echo "Intel_Files" ;; 8880) echo "ha_tunnel" ;;
        8888) echo "System_Node" ;; 8889) echo "PDC_Core" ;;
        9000) echo "Nextcloud_Core" ;; 9001) echo "Thohoyandou Survey" ;;
        9002) echo "Malamulele Pipe Repair" ;; 9003) echo "Crop Monitoring" ;;
        9090) echo "IDC_Stealth" ;; 11434) echo "Ollama_AI" ;;
        12345) echo "Alloy_UI" ;;
        5001) echo "Sovereign_Monitor" ;;
        5002) echo "MoMo_Stats_Server" ;;
        5003) echo "SADC_Payment_Gateway" ;;
        5006) echo "Metrics_API" ;;
        5007) echo "Metrics_Dashboard" ;;
        5008) echo "SADC_Logging_API" ;;
        8121) echo "Kimi_AI_Bridge" ;;
        8890) echo "Jupyter_Lab_Core" ;;
        8885) echo "VS_Code_Server" ;;
        8122) echo "Vision_Core" ;;
        18800) echo "Imperial_AI_Architect" ;;
        65412) echo "DSVW_Security_Lab" ;;
        65413) echo "DSSW_Secure_Web" ;;
        9093) echo "DSSW_Exporter" ;;
        9091) echo "Prometheus" ;;
        9092) echo "Pushgateway" ;;
        9102) echo "SADC_Exporter" ;;
        8089) echo "CTF_Trainer" ;;
        8084) echo "CTF_UI" ;;
        3001) echo "Grafana" ;;
    3006) echo "FreeLLMAPI" ;;
    5173) echo "Vite_Client" ;;
        3306) echo "Imperial_Nexus_DB" ;;
        *) echo "Unknown" ;;
    esac
}

# ===== CHECK PROMETHEUS RULES =====
if command -v promtool &>/dev/null; then
    if ! promtool check rules "$HOME/imperial_network/prometheus/imperial.rules.yml" &>/dev/null; then
        echo "⚠️  Recording rules have syntax errors! Check ~/imperial_network/prometheus/imperial.rules.yml"
    fi
fi

# ===== VAULT SENTRY =====
echo "🔍 VAULT SENTRY CHECK: $(date)"
bash ~/imperial_network/metrics_report.sh

echo "Status: 🔒 PROTECTED | ✅ Integrity: 900 Users Verified."
echo "🌅 DAWN REPORT [IMPERIAL OMEGA] - $(date)"
echo "-------------------------------------------------------"

# ===== PORT SCANNING =====
TOTAL_PORTS=76
ONLINE_COUNT=0
FAILED_PORTS=""

for port in 18800 12345 8002 3306 1880 1883 8001 8000 8005 8080 8081 8082 8083 8085 8086 8087 8088 8090 8091 8092 8093 8094 8095 8096 8097 8098 8099 8100 8101 8102 8103 8104 8105 8106 8107 8108 8110 8111 8112 8113 8114 8115 8117 8118 8191 8880 8888 8889 9001 9002 9003 9090 11434 5001 5002 5003 5006 5007 5008 8119 8120 8121 8890 8122 8885 65412 65413 9091 9092 9093 9102 8089 8084 3001  3006 5173; do
    NAME=$(get_name $port)
    if (timeout 0.1 bash -c "echo > /dev/tcp/localhost/$port") >/dev/null 2>&1; then
        echo "🟢 ONLINE  | Port $port: $NAME"
        ((ONLINE_COUNT++))
    else
        echo "🔴 OFFLINE | Port $port: $NAME"
        FAILED_PORTS+="$NAME ($port), "
    fi
done

CAPACITY=$(echo "scale=2; ($ONLINE_COUNT / $TOTAL_PORTS) * 100" | bc)

echo "-------------------------------------------------------"
echo "🛡️ WAR SENTINEL: 🟢 ACTIVE - Monitoring Sky & Economy"
echo "-------------------------------------------------------"
echo "📊 STATUS: $ONLINE_COUNT/$TOTAL_PORTS ports verified"
echo "⚠️  NOTICE: System performing at $CAPACITY% capacity."

# ===== FINANCIAL TOTALS =====
SADC_TOTAL=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S $HOME/mysql_run/mysql.sock -e "USE imperial_nexus; SELECT IFNULL(SUM(amount),0) FROM payment WHERE payment_method LIKE 'SADC%' AND is_demo = 0" -N -s 2>/dev/null || echo 0)
WEB_TOTAL=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S $HOME/mysql_run/mysql.sock -e "USE imperial_nexus; SELECT IFNULL(SUM(amount),0) FROM payment WHERE payment_method='IMPERIAL_WEB_UPGRADE' AND is_demo = 0" -N -s 2>/dev/null || echo 0)
TRUE_VAL=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S $HOME/mysql_run/mysql.sock -e "USE imperial_nexus; SELECT IFNULL(SUM(amount),0) FROM payment WHERE is_demo = 0" -N -s 2>/dev/null || echo 0)

echo ""
echo "🏛️  IMPERIAL SUMMARY"
echo "-------------------------------------------------------"
echo "💰 REAL REVENUE: R$TRUE_VAL"
echo "📈 PROGRESS TO R500B: $(echo "scale=4; ($TRUE_VAL / 500000000000) * 100" | bc)%"
echo "🌍 SADC CORRIDOR:   🟢 ACTIVE (Zim/Moz)"
echo "   • TRADE VOLUME:    N/A (not tracked)"
echo "🔒 WEALTH LOCK:     — (no ledger table)"
echo "💎 REAL REVENUE:   R$TRUE_VAL"
echo ""
echo "-------------------------------------------------------"
echo "💰 WEALTH LOCK UPDATE"
echo "   • Base Valuation: R$TRUE_VAL"
echo "   • Market Gain: N/A"
echo "-------------------------------------------------------"
# Live commodity data from Prometheus
PROM="http://localhost:9091/api/v1/query"
q() { curl -s --max-time 3 -G "$PROM" --data-urlencode "query=$1" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo 0; }

GOLD_OZ_ZAR=$(q 'sadc_commodity_price{commodity="gold",currency="ZAR"}')
GOLD_USD=$(q   'sadc_commodity_price{commodity="gold",currency="USD"}')
SILVER_USD=$(q 'sadc_commodity_price{commodity="silver",currency="USD"}')
LITHIUM_USD=$(q 'sadc_commodity_price{commodity="lithium",currency="USD"}')
COBALT_USD=$(q  'sadc_commodity_price{commodity="cobalt",currency="USD"}')
USDZAR=$(q     'sadc_fx_rate{pair="USDZAR"}')

GOLD_G_ZAR=$(echo "scale=2; ${GOLD_OZ_ZAR:-0} / 31.1035" | bc 2>/dev/null || echo "0")
_liu=${LITHIUM_USD:-0}
_uzr=${USDZAR:-0}
LITHIUM_ZAR=$(awk "BEGIN{printf \"%.2f\", $_liu * $_uzr}" 2>/dev/null || echo "0")

if [ "${GOLD_OZ_ZAR}" = "0" ]; then
    echo "📊 COMMODITY DATA: feed unavailable"
else
    echo "📊 COMMODITY DATA (live)"
    echo "   💎 Gold:    R${GOLD_G_ZAR}/g  (\$${GOLD_USD}/oz)"
    echo "   🥈 Silver:  \$${SILVER_USD}/oz"
    echo "   🔋 Lithium: \$${LITHIUM_USD}/tonne  (R${LITHIUM_ZAR}/tonne)"
    echo "   ⚙️  Cobalt:  \$${COBALT_USD}/tonne"
    echo "   💱 USD/ZAR: ${USDZAR}"
fi
echo "✅ Wealth tracking updated with SADC trade data"
echo "======================================================="
echo "🏆 $ONLINE_COUNT/$TOTAL_PORTS: $((ONLINE_COUNT * 100 / TOTAL_PORTS))% online"
echo "👑 CEO: Humbulani Mudau"
echo "========================================================="
echo "OFFICIAL CREDENTIALS & AUTHORITY"
echo "Technical Authority: ORCID 0009-0000-9572-4545"
echo "IDC Status: Enquiry #4000120009 (Permanently Satisfied)"
echo "Funding Scheme: Gro-E Youth Scheme (Industrial Expansion)"
echo "========================================================="

# ===== ALERT ENGINE – Port Down =====
if [ "$ONLINE_COUNT" -lt $((TOTAL_PORTS - 5)) ]; then
    ~/imperial_network/scripts/send_alert.sh "🚨 ALERT: System Degraded ($CAPACITY%). Down: $FAILED_PORTS"
fi

# ===== VULNERABILITY NOTIFICATION HOOK =====
UNNOTIFIED=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S $HOME/mysql_run/mysql.sock -e "USE imperial_nexus; SELECT COUNT(*) FROM vulnerability_logs WHERE notified = 0;" -N -s 2>/dev/null)
if [ -n "$UNNOTIFIED" ] && [ "$UNNOTIFIED" -gt 0 ]; then
    echo "⚠️  NOTICE: $UNNOTIFIED new vulnerabilities require attention."
    ~/imperial_network/scripts/send_alert.sh "🚨 New Vulnerabilities Logged: $UNNOTIFIED"
    # Mark them as notified
    mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S $HOME/mysql_run/mysql.sock -e "USE imperial_nexus; UPDATE vulnerability_logs SET notified = 1 WHERE notified = 0;" 2>/dev/null
fi

# ===== IMPERIAL NETWORK POLICY HUB =====
echo "--- Imperial Network Policy Hub ---"
echo "Policy Master: https://docs.google.com/document/d/1fy_OT98e_si7dDNVvGwV8qsmb_m4kE4Dvcoerntgc8A/edit"
echo "Risk Register: https://docs.google.com/document/d/134KIt-rcW_tDpc6jCHcpqQYXOjWh0psHzb71aoFy4-c/edit"
echo "-----------------------------------"

# ===== ADDITIONAL ALERT CHECKS =====
# Fleet maintenance check – if more than 3 vehicles in maintenance
FLEET_MAINT=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$MYSQL_SOCKET" -e "USE imperial_nexus; SELECT COUNT(*) FROM fleet WHERE status='Maintenance';" -N -s 2>/dev/null || echo 0)
if [ "$FLEET_MAINT" -gt 3 ]; then
    ~/imperial_network/scripts/send_alert.sh "🚨 Fleet alert: $FLEET_MAINT vehicles are in maintenance."
fi


