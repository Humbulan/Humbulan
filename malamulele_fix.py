#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

LOG_FILE = "/data/data/com.termux/files/home/imperial_network/logs/malamulele.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

DB_CMD = [
    "mariadb",
    "-u", "root",
    "-p" + os.environ.get("MYSQL_ROOT_PASSWORD", ""),
    "-S", "/data/data/com.termux/files/home/mysql_run/mysql.sock",
    "-D", "imperial_nexus",
    "-N",
    "-e"
]

VALIDATE_CMD = "/data/data/com.termux/files/home/imperial_network/validate_generic.sh"

def get_vehicles():
    query = "SELECT vehicle_id, sector, status FROM fleet ORDER BY vehicle_id;"
    result = subprocess.run(DB_CMD + [query], capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        print(f"DB error: {result.stderr}")
        return []
    rows = result.stdout.strip().split('\n')
    vehicles = []
    for row in rows:
        if not row.strip():
            continue
        parts = row.split('\t')
        vid = parts[0].strip() if len(parts) > 0 else 'unknown'
        sector = parts[1].strip() if len(parts) > 1 else 'unknown'
        status = parts[2].strip() if len(parts) > 2 else 'unknown'
        vehicles.append({'id': vid, 'sector': sector, 'status': status})
    return vehicles

def validate_sector(vehicle_id, sector):
    """Call validate_generic.sh with the sector as claim and topic 'allowed_sectors'."""
    # We'll construct a claim like "Vehicle X is in sector Y"
    claim = f"Vehicle {vehicle_id} is in sector '{sector}'"
    subprocess.run([VALIDATE_CMD, "allowed_sectors", claim], capture_output=True)

class MalamuleleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        vehicles = get_vehicles()
        # Validate each vehicle's sector
        for v in vehicles:
            validate_sector(v['id'], v['sector'])

        response = {
            'service': 'Malamulele_Portal',
            'status': 'online',
            'region': 'Limpopo',
            'villages': ['Malamulele Plaza', 'Masingita Crossing', 'Matsila', 'Altein', 'Ka-Mahonisi'],
            'active_users': 157,
            'vehicles': vehicles,
            'timestamp': str(datetime.now())
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())

    def log_message(self, format, *args):
        with open(LOG_FILE, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - {format % args}\n")

if __name__ == "__main__":
    print("🚀 Starting Malamulele Portal with sector validation on port 8100...")
    HTTPServer(('0.0.0.0', 8100), MalamuleleHandler).serve_forever()
