#!/data/data/com.termux/files/usr/bin/bash
# Runs every minute. Writes real system state to imperial_metrics.

SOCK="$HOME/mysql_run/mysql.sock"
DB="imperial_nexus"
PROOTS=$(ps -ef 2>/dev/null | grep -c "[p]root")

# Shell-derived metrics
PYTHONS=$(pgrep -f python3 | wc -l)
DISK_PCT=$(df /data | tail -1 | awk '{print $5}' | tr -d '%')
MEM_MB=$(free -m 2>/dev/null | awk '/Mem:/ {print $3}' || echo 0)

# DB-derived metrics
REAL_TX=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" -N -s -e \
  "USE $DB; SELECT COUNT(*) FROM payment WHERE is_demo=0" 2>/dev/null || echo 0)
REAL_REV=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" -N -s -e \
  "USE $DB; SELECT IFNULL(SUM(amount),0) FROM payment WHERE is_demo=0" 2>/dev/null || echo 0)
INC_24H=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" -N -s -e \
  "USE $DB; SELECT COUNT(*) FROM community_incidents WHERE created_at > NOW() - INTERVAL 24 HOUR" 2>/dev/null || echo 0)
FLEET_ACT=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" -N -s -e \
  "USE $DB; SELECT COUNT(*) FROM fleet WHERE status='active'" 2>/dev/null || echo 0)
PROJ_ACT=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" -N -s -e \
  "USE $DB; SELECT COUNT(*) FROM project_finance" 2>/dev/null || echo 0)

PORTS_LIST="18800 12345 8002 3306 1880 1883 8000 8001 8005 8080 8081 8082 8083 8085 8086 8087 8088 8090 8091 8092 8093 8094 8095 8096 8097 8098 8099 8100 8101 8102 8103 8104 8105 8106 8107 8108 8110 8111 8112 8113 8114 8115 8117 8118 8119 8120 8121 8122 8191 8880 8885 8888 8889 8890 9001 9002 9003 9090 9091 9102 11434 65412 3001 3006 5001 5002 5003 5006 5007 5008 5173 8084 8089"
PORTS_UP=0
for p in $PORTS_LIST; do
  (timeout 0.3 bash -c "echo > /dev/tcp/localhost/$p") 2>/dev/null && PORTS_UP=$((PORTS_UP+1))
done
# Write each into imperial_metrics (upsert)
write() {
  mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" "$DB" <<SQL
INSERT INTO imperial_metrics (metric_name, metric_value, recorded_at)
VALUES ('$1', $2, NOW())
ON DUPLICATE KEY UPDATE metric_value = VALUES(metric_value), recorded_at = NOW();
SQL
}

write "ops_python_processes" "$PYTHONS"
write "ops_proot_containers" "$PROOTS"
write "ops_disk_used_pct"    "$DISK_PCT"
write "ops_memory_used_mb"   "$MEM_MB"
write "ops_ports_online"     "$PORTS_UP"
write "biz_real_transactions" "$REAL_TX"
write "biz_real_revenue"     "$REAL_REV"
write "biz_incidents_24h"    "$INC_24H"
write "biz_fleet_active"     "$FLEET_ACT"
write "biz_projects_total"   "$PROJ_ACT"
