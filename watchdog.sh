#!/data/data/com.termux/files/usr/bin/bash
# Imperial Network Watchdog — runs every 5 min via cron.
# Fires omega_launch.sh only when too many services are offline.

LOG="$HOME/imperial_network/logs/watchdog.log"
PORTS="1880 1883 8000 8001 8080 8081 8082 8083 8085 8086 8087 8088 8090 8091 8092 8093 8094 8095 8096 8097 8098 8099 8100 8101 8102 8103 8104 8105 8106 8107 8108 8110 8111 8112 8113 8114 8115 8117 8118 8121 8122 8191 8880 8888 8889 8890 8119 9001 9002 9003 9090 11434 12345 18789 8002 8005 5001 5002 5003 5006 5007 5008 8885 65412 3306 9091 9102 8089 8084 3001 3006 5173"
THRESHOLD=70
ONLINE=0

for p in $PORTS; do
    (timeout 0.3 bash -c "echo > /dev/tcp/localhost/$p") 2>/dev/null && ((ONLINE++))
done

TS=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$ONLINE" -lt "$THRESHOLD" ]; then
    echo "[$TS] ALERT: $ONLINE services online (< $THRESHOLD) — firing omega_launch" >> "$LOG"
    rm -f "$HOME/imperial_network/omega_launch.lock"
    nohup bash "$HOME/imperial_network/omega_launch.sh" >> "$HOME/imperial_network/logs/boot.log" 2>&1 &
    sleep 30
    nohup bash "$HOME/.termux/boot/backup_archive/start_imperial_ubuntu.sh" >> "$HOME/imperial_network/logs/boot.log" 2>&1 &
else
    # Log heartbeat once an hour instead of every 5 min
    if [ "$(date +%M)" -lt 5 ]; then
        echo "[$TS] OK: $ONLINE services online" >> "$LOG"
        # force Prometheus reload every hour to pick up config drift
        curl -sf -X POST http://localhost:9091/-/reload >/dev/null 2>&1 || true
    fi
fi
