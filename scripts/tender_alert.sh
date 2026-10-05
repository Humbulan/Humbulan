#!/data/data/com.termux/files/usr/bin/bash
# Daily Vhembe-area tender alert (Thohoyandou radius)
source ~/imperial_network/.env

SOCK="$HOME/mysql_run/mysql.sock"
DB="imperial_nexus"

ROWS=$(mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$SOCK" -N -s -e "
  USE $DB;
  SELECT CONCAT('• ', tender_number, ' — ', LEFT(title,70), '  (closes ', closing_date, ')')
  FROM tender_monitor
  WHERE province='Limpopo'
    AND is_demo = 0
    AND status IN ('active','planned')
    AND closing_date >= CURDATE()
    AND municipality IN ('Thulamela','Makhado','Musina','Collins Chabane','Vhembe')
  ORDER BY closing_date ASC
  LIMIT 20;
")

if [ -z "$ROWS" ]; then
  echo "[$(date)] No Vhembe-area tenders active"
  exit 0
fi

COUNT=$(echo "$ROWS" | wc -l)
MSG="🏗️ *VIEMBE TENDERS* — $(date +'%d %b %Y')
$COUNT tenders near Thohoyandou

$ROWS

Full list: monitor.humbu.store/tenders"

curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$(printf '{"text":%s}' "$(printf '%s' "$MSG" | jq -Rs .)")"

echo "[$(date)] Sent $COUNT Vhembe tenders to Slack"
