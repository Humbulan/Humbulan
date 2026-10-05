#!/bin/bash
BACKUP_DIR="$HOME/humbu_community_nexus/backups/database"
mkdir -p "$BACKUP_DIR"
# Dump ALL databases (use the password from your cron environment)
mariadb-dump -u root -p"${MYSQL_ROOT_PASSWORD}" --all-databases > "$BACKUP_DIR/full_backup_$(date +%Y%m%d_%H%M%S).sql"
# Keep only the last 7 days to avoid filling storage
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
echo "DB backup completed: $(date)" >> "$BACKUP_DIR/backup.log"
