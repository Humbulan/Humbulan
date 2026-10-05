#!/data/data/com.termux/files/usr/bin/bash
# Imperial Network Optimizer – High‑Value Node Prioritisation & Telemetry

DB_OPTS="-S $HOME/mysql_run/mysql.sock"
HIGH_VALUE_PORTS="8106 8107 8108"
LOG_FILE="$HOME/imperial_network/logs/optimizer.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

prioritise_services() {
    log "Applying CPU priority adjustments..."
    for port in $HIGH_VALUE_PORTS; do
        service=$(mariadb $DB_OPTS -N -e "USE imperial_nexus; SELECT service_name FROM system_sectors WHERE port=$port;" 2>/dev/null)
        if [[ -n "$service" ]]; then
            pids=$(pgrep -f "$service" 2>/dev/null)
            if [[ -n "$pids" ]]; then
                for pid in $pids; do
                    renice -n -5 -p "$pid" 2>/dev/null && log "  ✅ $service (pid $pid) niceness set to -5"
                done
            else
                log "  ⚠️ No running process found for $service"
            fi
        fi
    done

    mariadb $DB_OPTS -N -e "USE imperial_nexus; SELECT service_name FROM system_sectors WHERE wealth_value = 0 AND status='online';" 2>/dev/null | while read -r util; do
        pids=$(pgrep -f "$util" 2>/dev/null)
        for pid in $pids; do
            renice -n 10 -p "$pid" 2>/dev/null && log "  🔽 $util (pid $pid) niceness set to 10"
        done
    done
}

update_latency() {
    log "Updating response_time telemetry..."
    HIGH_PORTS=$(mariadb $DB_OPTS -N -e "USE imperial_nexus; SELECT port FROM system_sectors WHERE wealth_value > 0 AND status=online;" 2>/dev/null | tr "\n" " ")
    for port in $HIGH_PORTS; do
        service=$(mariadb $DB_OPTS -N -e "USE imperial_nexus; SELECT service_name FROM system_sectors WHERE port=$port;" 2>/dev/null)
        LATENCY=$(curl -s -o /dev/null -w "%{time_total}" --max-time 3 "http://localhost:$port" 2>/dev/null)
        if [[ -n "$LATENCY" && "$LATENCY" != "0.000" && "$LATENCY" != "0" ]]; then
            mariadb $DB_OPTS -e "USE imperial_nexus; UPDATE system_sectors SET response_time = $LATENCY WHERE port = $port;" 2>/dev/null
            log "  ✅ $service (port $port) latency = ${LATENCY}s"
        else
            log "  ⚠️ $service (port $port) did not respond (latency=$LATENCY)"
        fi
    done
}

check_high_value_health() {
    log "Checking high‑value node health..."
    for port in $HIGH_VALUE_PORTS; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" | grep -q "^[2-3]"; then
            log "  ✅ Port $port is healthy"
        else
            log "  🔴 Port $port is UNRESPONSIVE! Trigger alert."
            ~/imperial_network/scripts/notify.sh "ALERT: High-value node on port $port is down!" 2>/dev/null
        fi
    done
}

case "$1" in
    priority)  prioritise_services ;;
    latency)   update_latency ;;
    health)    check_high_value_health ;;
    all)       prioritise_services; update_latency; check_high_value_health ;;
    *)         echo "Usage: $0 {priority|latency|health|all}"; exit 1 ;;
esac
log "Optimizer run completed."
