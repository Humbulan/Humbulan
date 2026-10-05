#!/usr/bin/env python3
import os
import mysql.connector
from datetime import datetime, timedelta

def summarize():
    conn = mysql.connector.connect(
        user='root',
        password=os.environ.get("MYSQL_ROOT_PASSWORD", ""),
        host='127.0.0.1',
        unix_socket='/data/data/com.termux/files/home/mysql_run/mysql.sock',
        database='imperial_nexus'
    )
    cursor = conn.cursor()
    today = datetime.now().date()
    
    # Aggregate per metric_name for today
    cursor.execute("""
        INSERT INTO sadc_daily_summary (summary_date, metric_name, avg_value, max_value, min_value, total_count)
        SELECT 
            DATE(logged_at) AS summary_date,
            metric_name,
            AVG(metric_value) AS avg_value,
            MAX(metric_value) AS max_value,
            MIN(metric_value) AS min_value,
            COUNT(*) AS total_count
        FROM sadc_metrics
        WHERE DATE(logged_at) = %s
        GROUP BY metric_name
        ON DUPLICATE KEY UPDATE
            avg_value = VALUES(avg_value),
            max_value = VALUES(max_value),
            min_value = VALUES(min_value),
            total_count = VALUES(total_count)
    """, (today,))
    
    conn.commit()
    conn.close()
    print(f"Daily summary for {today} updated.")

if __name__ == "__main__":
    summarize()
