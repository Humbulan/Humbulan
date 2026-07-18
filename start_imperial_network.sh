#!/data/data/com.termux/files/usr/bin/bash
echo "🚀 IMPERIAL NETWORK STARTUP SEQUENCE"
echo "====================================="
cd ~/imperial_network || exit
mkdir -p logs

check_port() {
    timeout 0.5 bash -c "echo > /dev/tcp/localhost/$1" 2>/dev/null && return 0 || return 1
}

echo "Starting Imperial Network Services..."

# 1. Imperial Front Page (8097)
if ! check_port 8097; then
    echo " 👑 Starting Imperial Front Page (8097)..."
    cd ~/humbu_community_nexus/restored_projects/api-tester-frontend || exit
    nohup python3 -m http.server 8097 --bind 127.0.0.1 > ~/imperial_network/logs/imperial-front.log 2>&1 &
    cd ~/imperial_network
fi

# 2. Node-RED (1880, 1883)
if ! check_port 1880; then
    echo " 📡 Starting REAL Node-RED (1880)..."
    pkill -f node-red
    nohup node-red -p 1880 -s ~/.node-red/settings.js > logs/node-red.log 2>&1 &
fi
if ! check_port 1883; then
    echo " 📡 Starting Node-RED Proxy (1883)..."
    nohup python3 ~/imperial_network/node_red_proxy_1883_enhanced.py > logs/node_red_proxy.log 2>&1 &
fi

# 3. Core Business (8000, 8001)
if ! check_port 8000; then
    echo " 💼 Starting Business API (8000)..."
    nohup python3 app.py > logs/flask.log 2>&1 &
fi
if ! check_port 8001; then
    echo " 👑 Starting Admin Portal (8001)..."
    nohup python3 admin_portal_8001_fixed.py > logs/admin_portal.log 2>&1 &
fi

# 4. Proxy Layer (8080, 8081, 8083)
if ! check_port 8080; then
    echo " 🌐 Starting Proxy Layer (8080)..."
    nohup python3 proxy_layer_8080.py > logs/proxy_8080.log 2>&1 &
fi
if ! check_port 8081; then
    echo " 🏢 Starting Enterprise API (8081)..."
    nohup python3 proxy_8081.py > logs/proxy_8081.log 2>&1 &
fi
if ! check_port 8083; then
    echo " 🔄 Starting Redundant Node (8083)..."
    nohup python3 proxy_8083.py > logs/proxy_8083.log 2>&1 &
fi

# 5. Revenue & Vault (8082, 8085, 8086)
if ! check_port 8082; then
    echo " 💰 Starting Revenue Bridge (8082)..."
    nohup python3 revenue_bridge.py > logs/revenue_bridge.log 2>&1 &
fi
if ! check_port 8085; then
    echo " 🔐 Starting Legacy Vault (8085)..."
    nohup python3 legacy_vault_fixed.py > logs/legacy_vault.log 2>&1 &
fi
if ! check_port 8086; then
    echo " 📊 Starting Apex Metrics (8086)..."
    nohup python3 apex_metrics.py > logs/apex_metrics.log 2>&1 &
fi

# 6. Mobile & USSD (8087)
if ! check_port 8087; then
    echo " 📱 Starting USSD Portal (8087)..."
    nohup python3 ussd_fix.py > logs/ussd.log 2>&1 &
fi

# 7. Custom Portal Master (8088)
if ! check_port 8088; then
    echo " 🏪 Starting Imperial Portal Master (8088)..."
    nohup python3 ~/imperial_network/portal_master_8088.py > ~/imperial_network/logs/portal_8088.log 2>&1 &
fi

# 8. Monitoring (8090, 8092)
if ! check_port 8090; then
    echo " 📈 Starting Monitor (8090)..."
    nohup python3 monitor_8090.py > logs/monitor.log 2>&1 &
fi
if ! check_port 8092; then
    echo " 🖥️ Starting Beautiful Dashboard UI (8092)..."
    nohup python3 dashboard_ui_fixed.py > logs/dashboard.log 2>&1 &
fi

# 9. System Stats Server (8093, 8121, 8890)
if ! check_port 8093 && ! check_port 8121 && ! check_port 8890; then
    echo " 📊 Starting System Stats Server (8093, 8121, 8890)..."
    nohup python3 system_stats_server_simple.py > logs/system_stats.log 2>&1 &
fi

# 10. Sovereign Monitor (5001)
if ! check_port 5001; then
    echo " 📊 Starting Sovereign Monitor (5001)..."
    nohup python3 omega_monitor.py > logs/omega_5001.log 2>&1 &
fi

# 11. File browser / cloud manager (8095)
if ! check_port 8095; then
    if [ -f "/data/data/com.termux/files/usr/bin/filebrowser" ]; then
        nohup filebrowser --noauth --port 8095 --address 0.0.0.0 --database /data/data/com.termux/files/home/.config/filebrowser/filebrowser.db --root /data/data/com.termux/files/home/humbu_community_nexus/ > logs/filebrowser.log 2>&1 &
    else
        nohup python3 cloud_manager_8095.py > logs/cloud_manager.log 2>&1 &
    fi
fi

# 12. Intel Files (8191)
if ! check_port 8191; then
    echo " 📁 Starting Intel Files (8191)..."
    nohup python3 intel_files_8191.py > logs/intel_files.log 2>&1 &
fi

# 13. Sovereign & B2B (8096, 8099)
if ! check_port 8096; then
    echo " 👑 Starting Sovereign Master (8096)..."
    nohup python3 sovereign_master_8096.py > logs/sovereign_master.log 2>&1 &
fi
if ! check_port 8099; then
    echo " 🤝 Starting B2B Hub (8099)..."
    nohup python3 b2b_hub_8099.py > logs/b2b_hub.log 2>&1 &
fi

# 14. Regional Portals (8100, 8101, 8102)
if ! check_port 8100; then
    echo " 🏘️ Starting Malamulele Portal (8100)..."
    nohup python3 malamulele_fix.py > logs/malamulele.log 2>&1 &
fi
if ! check_port 8101; then
    echo " 📊 Starting BI Hub (8101)..."
    nohup python3 bi_hub_8101.py > logs/bi_hub.log 2>&1 &
fi
if ! check_port 8102; then
    echo " 🌆 Starting Urban Gateway (8102)..."
    nohup python3 urban_gateway_8102.py > logs/urban_gateway.log 2>&1 &
fi

# 15. Intelligence (8103, 8104, 8105)
if ! check_port 8103; then
    echo " 🧠 Starting Intel Alpha (8103)..."
    nohup python3 intel_alpha_8103.py > logs/intel_alpha.log 2>&1 &
fi
if ! check_port 8104; then
    echo " ⚡ Starting Surge Monitor (8104)..."
    nohup python3 surge_monitor_8104_fixed.py > logs/surge_monitor.log 2>&1 &
fi
if ! check_port 8105; then
    echo " 🛡️ Starting Sentinel (8105)..."
    nohup python3 sentinel_8105.py > logs/sentinel.log 2>&1 &
fi

# 16. IDC Dividend Sectors (8106, 8107, 8108)
if ! check_port 8106; then
    echo " 🌐 Starting IMPERIAL_WEB_UPGRADE (8106)..."
    nohup python3 ~/imperial_network/port_8106.py > logs/port_8106.log 2>&1 &
fi
if ! check_port 8107; then
    echo " 🚚 Starting SADC_A_LOGISTICS (8107)..."
    nohup python3 ~/imperial_network/port_8107.py > logs/port_8107.log 2>&1 &
fi
if ! check_port 8108; then
    echo " 🏪 Starting SADC_B_RETAIL (8108)..."
    nohup python3 ~/imperial_network/port_8108.py > logs/port_8108.log 2>&1 &
fi

# 17. Relay Network (8110, 8111, 8112)
if ! check_port 8110; then
    echo " 🔄 Starting Thohoyandou (8110)..."
    nohup python3 -m http.server 8110 --bind 127.0.0.1 > logs/thohoyandou.log 2>&1 &
fi
if ! check_port 8111; then
    echo " 🔄 Starting Malamulele Relay (8111)..."
    nohup python3 malamulele_relay.py > logs/relay.log 2>&1 &
fi
if ! check_port 8112; then
    echo " 🌍 Starting SADC Sync (8112)..."
    nohup python3 sadc_sync_enhanced.py > logs/sadc_sync.log 2>&1 &
fi

# 18. Secondary Vaults (8113, 8114, 8115)
if ! check_port 8113; then
    echo " 🔐 Starting Vault 2 (8113)..."
    nohup python3 vault_2_8113.py > logs/vault2.log 2>&1 &
fi
if ! check_port 8114; then
    echo " 📦 Starting B2B Bulk (8114)..."
    nohup python3 b2b_bulk_8114.py > logs/b2b_bulk.log 2>&1 &
fi
if ! check_port 8115; then
    echo " 👻 Starting Ghost (8115)..."
    nohup python3 ghost_8115.py > logs/ghost.log 2>&1 &
fi

# 19. Voucher API (8098)
if ! check_port 8098; then
    echo " 🎫 Starting Voucher API (8098)..."
    nohup python3 voucher_api.py > logs/voucher_api.log 2>&1 &
fi

# 20. Contact handler (8109)
if ! check_port 8109; then
    echo " 📩 Starting Contact Handler (8109)..."
    cd ~/imperial_network || exit
    nohup python3 contact_handler.py > logs/contact_handler.log 2>&1 &
fi

# 21. Ukuvuselela Webhook (8117)
if ! check_port 8117; then
    echo " 🔗 Starting Ukuvuselela Webhook (8117)..."
    cd ~/imperial_network || exit
    nohup python3 standalone_webhook_8117.py > logs/ukuvo_webhook.log 2>&1 &
fi

# 22. SEWS Bridge (8091)
if ! check_port 8091; then
    echo " 🌉 Starting SEWS Bridge (8091)..."
    nohup python3 sews_bridge_8091.py > logs/sews_bridge.log 2>&1 &
fi

# 23. Sky Watcher (8094)
if ! check_port 8094; then
    echo " 🛰️ Starting Sky Watcher (8094)..."
    nohup python3 sky_watcher_8094_fixed.py > logs/sky_watcher.log 2>&1 &
fi

# 24. Brain & Core (8888, 8889, 8880)
if ! check_port 8888; then
    echo " 🧠 Starting System Node (8888)..."
    nohup python3 system_node_8888.py > logs/brain_8888.log 2>&1 &
fi
if ! check_port 8889; then
    echo " 💾 Starting PDC Core (8889)..."
    nohup python3 pdc_backup_8889.py > logs/brain_backup_8889.log 2>&1 &
fi
if ! check_port 8880; then
    echo " 🚇 Starting HA Tunnel (8880)..."
    nohup python3 ~/imperial_network/port_8880.py > logs/ha_tunnel.log 2>&1 &
fi

# 25. Health Webhook & Stealth (8119, 9090)
if ! check_port 8119; then
    echo " ⚡ Starting Health Webhook Server (8119)..."
    nohup python3 health_webhook.py > logs/health_webhook.log 2>&1 &
fi
if ! check_port 9090; then
    echo " 👻 Starting IDC Stealth (9090)..."
    nohup python3 idc_stealth_9090.py > logs/stealth_9090.log 2>&1 &
fi

# 26. Community Tasks (9001, 9002, 9003)
if ! check_port 9001; then
    echo " 📋 Starting Thohoyandou Survey (9001)..."
    nohup python3 ~/imperial_network/port_9001.py > logs/port_9001.log 2>&1 &
fi
if ! check_port 9002; then
    echo " 📋 Starting Malamulele Pipe Repair (9002)..."
    nohup python3 ~/imperial_network/port_9002.py > logs/port_9002.log 2>&1 &
fi
if ! check_port 9003; then
    echo " 📋 Starting Crop Monitoring (9003)..."
    nohup python3 ~/imperial_network/port_9003.py > logs/port_9003.log 2>&1 &
fi

# 27. AI Engine (11434)
if ! check_port 11434; then
    echo " 🤖 Starting Ollama AI (11434)..."
    nohup ollama serve > logs/ollama.log 2>&1 &
fi

# 28. Kimi AI Bridge (8121) fallback
if ! check_port 8121; then
    echo " 🧠 Starting Kimi AI Bridge (8121) fallback..."
    nohup python3 ~/imperial_network/kimi_bridge.py > logs/kimi_8121.log 2>&1 &
fi

# 29. Financial gateways (background)
echo " 💳 Starting financial gateways..."
nohup python3 ~/imperial_network/momo_stats_server.py > logs/momo.log 2>&1 &
nohup python3 ~/imperial_network/sadc_payment_gateway.py > logs/sadc_payment.log 2>&1 &
nohup python3 ~/imperial_network/ussd_dawn_report.py > logs/ussd_dawn.log 2>&1 &

# 30. Imperial Architect Bridge (18800 -> 8118)
if command -v socat >/dev/null 2>&1; then
    fuser -k 18800/tcp >/dev/null 2>&1
    nohup socat TCP-LISTEN:18800,fork,reuseaddr TCP:127.0.0.1:8118 > /dev/null 2>&1 &
    echo "✅ Imperial Architect Bridge Active [18800 -> 8118]"
fi
    echo "Updating system sectors in database..."
mariadb -u root -pRootStrongPass123! -S $HOME/mysql_run/mysql.sock -e "USE imperial_nexus; UPDATE system_sectors SET status='online', last_seen=NOW() WHERE port IN (1880,1883,8000,8001,8080,8081,8082,8083,8085,8086,8087,8088,8090,8091,8092,8093,3306,8121,8890,8094,8095,8096,8097,8098,8099,8100,8101,8102,8103,8104,8105,8106,8107,8108,8110,8111,8112,8113,8114,8115,8117,8191,8880,8888,8889,8119,9001,9002,9003,9090,11434,5000,5001);"
    ONLINE=$(sqlite3 instance/imperial.db "SELECT COUNT(*) FROM system_sectors WHERE status='online';" 2>/dev/null || echo "0")
    TOTAL=$(sqlite3 instance/imperial.db "SELECT COUNT(*) FROM system_sectors;" 2>/dev/null || echo "0")
    echo "====================================="

echo "====================================="
echo "📊 Run 'dawn-report-truthful' to see full status"
echo ""
echo "🌐 ACCESS YOUR NETWORK:"
echo " • Admin Portal: http://localhost:8001"
echo " • Beautiful Dashboard: http://localhost:8092"
echo " • Node-RED Dashboard: http://localhost:1883"
echo " • System Monitor: http://localhost:8090"
echo " • Brain Command: http://localhost:8888"
echo " • Stealth Node: http://localhost:9090"
echo ""
echo "👑 CEO: Humbulani Mudau"


# MariaDB Imperial Nexus (3306)
if ! check_port 3306; then
    echo " 🗄️ Starting MariaDB Imperial Nexus (3306)..."
    pkill -9 -f mariadbd 2>/dev/null
    pkill -9 -f mysqld 2>/dev/null
    rm -f /data/data/com.termux/files/home/mysql_run/mysql.sock
    mkdir -p /data/data/com.termux/files/home/mysql_run
    nohup mariadbd-safe --datadir=/data/data/com.termux/files/usr/var/lib/mysql --socket=/data/data/com.termux/files/home/mysql_run/mysql.sock --port=3306 --bind-address=127.0.0.1 > ~/imperial_network/logs/mariadb.log 2>&1 &
    for i in {1..15}; do
        if [ -S /data/data/com.termux/files/home/mysql_run/mysql.sock ]; then
            echo " ✅ MariaDB Imperial Nexus Active [Port 3306]"
            break
        fi
        sleep 1
    done
    if [ ! -S /data/data/com.termux/files/home/mysql_run/mysql.sock ]; then
        echo " ❌ MariaDB failed to start. Check ~/imperial_network/logs/mariadb.log"
    fi
    echo " ✅ MariaDB Imperial Nexus already running [Port 3306]"
fi
