#!/data/data/com.termux/files/usr/bin/bash
PROM_URL="http://localhost:9091/api/v1/query"
DB_OPTS="-S $HOME/mysql_run/mysql.sock imperial_nexus"

# List of metrics to fetch (some have labels)
METRICS=(
    "cloudflare_accounts"
    "cloudflare_zones"
    "cloudflare_zones_filtered"
    "cloudflare_zones_processed"
    "cloudflare_zones_skipped_free_tier"
    "cloudflare_worker_requests_total"
    "cloudflare_worker_errors_total"
    "cloudflare_worker_cpu_time_seconds"
)

for metric in "${METRICS[@]}"; do
    # Fetch result
    result=$(curl -s "$PROM_URL?query=$metric" | jq -c '.data.result')
    if [[ "$result" == "[]" ]] || [[ -z "$result" ]]; then
        echo "No data for $metric"
        continue
    fi

    # For each result item (handles multiple series)
    echo "$result" | jq -c '.[]' | while read -r item; do
        # Extract value and labels
        value=$(echo "$item" | jq -r '.value[1] // ""')
        labels=$(echo "$item" | jq -c '.metric')
        if [[ -n "$value" && "$value" != "null" ]]; then
            mariadb $DB_OPTS -e "INSERT INTO cloudflare_metrics (metric, value, labels, timestamp) VALUES ('$metric', $value, '$labels', NOW());"
            echo "Inserted $metric = $value (labels: $labels)"
        fi
    done
done
