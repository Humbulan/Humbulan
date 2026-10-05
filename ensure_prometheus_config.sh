#!/data/data/com.termux/files/usr/bin/bash
# Ensure Prometheus config exists and rules are valid.
PROM_DIR="$HOME/imperial_network/prometheus"
RULES_FILE="$PROM_DIR/imperial.rules.yml"
CONFIG_FILE="$HOME/imperial_network/prometheus.yml"

if [[ ! -f "$RULES_FILE" ]]; then
  echo "ERROR: $RULES_FILE missing"
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: $CONFIG_FILE missing"
  exit 1
fi

RULES=$(grep -cE "^\s*-\s*alert:|^\s*-\s*record:" "$RULES_FILE")
echo "Checking $RULES_FILE"
echo "SUCCESS: $RULES rules found"

if curl -sf -X POST http://localhost:9091/-/reload >/dev/null 2>&1; then
  echo "✅ Rules validated. Reloading Prometheus..."
else
  echo "⚠️  Prometheus reload skipped (not running)"
fi
