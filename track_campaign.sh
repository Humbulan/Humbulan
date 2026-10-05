#!/bin/bash
# Override sqlite3 to use MariaDB instead

sqlite3() {

    local db="$1"

    local query="$2"

    mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$HOME/mysql_run/mysql.sock" -e "USE imperial_nexus; $query" | tail -1

}

export -f sqlite3

# 📊 IMPERIAL CAMPAIGN TRACKER

echo "📊 IMPERIAL REFERRAL CAMPAIGN TRACKER"
echo "======================================"
echo ""

CURRENT=$(sqlite3 instance/imperial.db "SELECT COUNT(*) FROM users;")
TARGET=1000
NEEDED=$((TARGET - CURRENT))
START=900
PROGRESS=$(( (CURRENT - START) * 100 / NEEDED ))

echo "🎯 TARGET: 1,000 SOVEREIGNS"
echo "   • Start: 900"
echo "   • Current: $CURRENT"
echo "   • Needed: $NEEDED"
echo "   • Progress: $PROGRESS%"
echo ""

if [ $NEEDED -eq 0 ]; then
    echo "🏆 TARGET ACHIEVED! 1,000 SOVEREIGNS!"
else
    echo "🚀 CAMPAIGN ACTIVE - $NEEDED more to go"
    echo ""
    echo "📋 LAST 10 REGISTRATIONS:"
    sqlite3 instance/imperial.db "SELECT created_at, username, village FROM users ORDER BY id DESC LIMIT 10;"
fi
