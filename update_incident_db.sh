#!/bin/bash
# Fetch incidents from feed and insert into MariaDB
FEED_URL="http://localhost:8000/community-safety-feed"
DB_OPTS="-S $HOME/mysql_run/mysql.sock imperial_nexus"

incidents=$(curl -s "$FEED_URL" | jq -c '.incidents[]')
if [ -z "$incidents" ]; then
    echo "No incidents received"
    exit 0
fi

echo "$incidents" | while read -r incident; do
    incident_type=$(echo "$incident" | jq -r '.incident_type')
    location_id=$(echo "$incident" | jq -r '.location_id')
    severity=$(echo "$incident" | jq -r '.severity_level')
    verified=$(echo "$incident" | jq -r '.is_verified')
    action=$(echo "$incident" | jq -r '.action_taken')
    created=$(echo "$incident" | jq -r '.created_at')
    mariadb $DB_OPTS -e "INSERT IGNORE INTO community_incidents (incident_type, location_id, severity_level, is_verified, action_taken, created_at) VALUES ('$incident_type', $location_id, $severity, $verified, '$action', '$created');"
done
