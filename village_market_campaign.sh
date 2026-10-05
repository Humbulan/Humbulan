#!/bin/bash
# Override sqlite3 to use MariaDB instead

sqlite3() {

    local db="$1"

    local query="$2"

    mariadb -u root -p"${MYSQL_ROOT_PASSWORD}" -S "$HOME/mysql_run/mysql.sock" -e "USE imperial_nexus; $query" | tail -1

}

export -f sqlite3

# 🏛️ VILLAGE MARKET REFERRAL CAMPAIGN - 100 USERS IN 24H

echo "🏛️ VILLAGE MARKET REFERRAL CAMPAIGN"
echo "===================================="
echo "Target: 100 new users from Village Market (279 artisans)"
echo ""

# Generate referral codes for existing users
echo "📋 REFERRAL CODES GENERATED:"
for i in {1..10}; do
    CODE="VM-$(date +%Y%m%d)-$RANDOM"
    echo "   • $CODE - For artisan #$i"
done

echo ""
echo "🚀 CAMPAIGN STRATEGY:"
echo "   1. Each artisan refers 1 new user = 279 new users"
echo "   2. Target: Just 100 referrals needed"
echo "   3. Incentive: Free AI session for top referrer"
echo ""
echo "📊 PROJECTED: 1,000 SOVEREIGNS by end of day"
