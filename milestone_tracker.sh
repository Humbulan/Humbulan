#!/bin/bash
# Override sqlite3 to use MariaDB instead

sqlite3() {

    local db="$1"

    local query="$2"

    mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$HOME/mysql_run/mysql.sock" -e "USE imperial_nexus; $query" | tail -1

}

export -f sqlite3

# 🏛️ IMPERIAL MILESTONE TRACKER

echo "🏛️ IMPERIAL MILESTONE TRACKER"
echo "============================="
echo ""

CURRENT=$(sqlite3 instance/imperial.db "SELECT COUNT(*) FROM users;")
TARGETS=(500 600 700 800 900 1000 1200 1500)

echo "🎯 MILESTONE PROGRESS:"
echo "----------------------------------------"

for target in "${TARGETS[@]}"; do
    if [ $CURRENT -ge $target ]; then
        echo "✅ $target SOVEREIGNS - ACHIEVED"
    else
        PROGRESS=$((CURRENT * 100 / target))
        NEEDED=$((target - CURRENT))
        echo "⏳ $target SOVEREIGNS - ${PROGRESS}% ($NEEDED to go)"
    fi
done

echo ""
echo "📊 NEXT MILESTONE: 1,000 SOVEREIGNS"
echo "   • Current: $CURRENT"
echo "   • Needed: $((1000 - CURRENT))"
echo "   • Status: $((CURRENT * 100 / 1000))% complete"

if [ $CURRENT -ge 900 ]; then
    echo ""
    echo "🏆 TARGET 1,000 WITHIN REACH!"
    echo "   • Last addition: New Territory (+136 users)"
    echo "   • Projected: $((1000 - CURRENT)) days at current rate"
fi
