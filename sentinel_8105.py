import os
from flask import Flask
import mysql.connector
import threading
import time
import datetime

app = Flask(__name__)

DATA = {"status": "Sovereign Shield Active", "valuation": "R269.9B", "integrity": "100%", "last_check": ""}

def get_cf_status():
    try:
        conn = mysql.connector.connect(user='root', password=os.environ.get("MYSQL_ROOT_PASSWORD", ""), unix_socket='/data/data/com.termux/files/home/mysql_run/mysql.sock', database='imperial_nexus')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM cloudflare_metrics ORDER BY timestamp DESC LIMIT 1")
        val = cursor.fetchone()
        conn.close()
        return str(val[0]) if val else "N/A"
    except Exception:
        return "Error"

@app.route('/')
def home():
    return f'<html><body style="background:#000; color:#0f0; font-family:monospace; padding:20px;"><h1>🛡️ SENTINEL 8105: ACTIVE</h1><hr><p>STATUS: {DATA["status"]}</p><p>VALUATION: {DATA["valuation"]}</p><p>INTEGRITY: {DATA["integrity"]}</p><p>LAST PULSE: {DATA["last_check"]}</p><p>CLOUDFLARE STATUS: {get_cf_status()}</p></body></html>'

def monitor_loop():
    while True:
        DATA['last_check'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(60)

threading.Thread(target=monitor_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(port=8105, host='0.0.0.0')
