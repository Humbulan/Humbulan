import mysql.connector
import subprocess
import sys
import os
import os as _os
def _mysql_password():
    pwd = _os.environ.get("MYSQL_ROOT_PASSWORD", "")
    if pwd:
        return pwd
    try:
        with open(_os.path.expanduser("~/.my.cnf")) as f:
            for line in f:
                if line.startswith("password="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def check_and_notify():
    try:
        conn = mysql.connector.connect(
            user='root',
            password=_mysql_password(),
            host='127.0.0.1',
            unix_socket='/data/data/com.termux/files/home/mysql_run/mysql.sock',
            database='imperial_nexus'
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sadc_metrics WHERE notified = 0 AND metric_value > 1000")
        new_metrics = cursor.fetchall()

        for row in new_metrics:
            msg = f"⚡ SADC ALERT: {row['metric_name']} reported {row['metric_value']} {row['unit']} in {row['region']}"
            # Print to stdout (captured in log file)
            print(msg)
            # Call your existing notification service
            subprocess.run([
                "/data/data/com.termux/files/usr/bin/python3",
                "/data/data/com.termux/files/home/imperial_network/notification_service_final.py",
                msg
            ], check=False)
            # Mark as notified
            cursor.execute("UPDATE sadc_metrics SET notified = 1 WHERE id = %s", (row['id'],))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERROR in alert engine: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_and_notify()
