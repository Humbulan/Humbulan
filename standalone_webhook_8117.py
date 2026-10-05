#!/usr/bin/env python3
"""
Webhook with Prometheus metrics – names match Imperial dashboard.
Now also proxies Cloudflare metrics with caching.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import datetime
import os
import json
import urllib.request
import subprocess
import threading
import time

# Global cache for Cloudflare metrics
cf_cache = {
    'data': '',
    'timestamp': 0,
    'ttl': 60  # seconds
}

def refresh_cloudflare_metrics():
    """Read Cloudflare metrics from MariaDB (no external URL)."""
    global cf_cache
    try:
        pwd = os.environ.get("MYSQL_ROOT_PASSWORD", "")
        if not pwd:
            try:
                with open(os.path.expanduser("~/.bashrc")) as f:
                    for line in f:
                        if "MYSQL_ROOT_PASSWORD" in line and line.startswith("export"):
                            pwd = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception:
                pass
        sock = os.path.expanduser("~/mysql_run/mysql.sock")
        cmd = ["mariadb", "-u", "root", "-S", sock]
        if pwd:
            cmd.append("-p" + pwd)
        cmd.extend([
            "imperial_nexus", "-N", "-s", "-e",
            "SELECT metric, value, labels FROM cloudflare_metrics "
            "WHERE timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR) "
            "ORDER BY timestamp DESC",
        ])
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            cf_cache["data"] = "# ERROR reading DB: %s\n" % res.stderr.strip()
            cf_cache["timestamp"] = time.time()
            return

        lines = []
        seen = set()
        for row in res.stdout.strip().split("\n"):
            if not row.strip():
                continue
            parts = row.split("\t")
            if len(parts) < 3:
                continue
            metric, value, labels_json = parts[0], parts[1], parts[2]
            key = (metric, labels_json)
            if key in seen:
                continue
            seen.add(key)
            try:
                labels = json.loads(labels_json) if labels_json and labels_json != "NULL" else {}
            except Exception:
                labels = {}
            label_str = ",".join('%s="%s"' % (k, v) for k, v in labels.items())
            if label_str:
                lines.append("%s{%s} %s" % (metric, label_str, value))
            else:
                lines.append("%s %s" % (metric, value))

        if not lines:
            cf_cache["data"] = "# no recent cloudflare metrics in DB\n"
        else:
            cf_cache["data"] = "\n".join(lines) + "\n"
        cf_cache["timestamp"] = time.time()
    except Exception as e:
        cf_cache["data"] = "# ERROR: %s\n" % e
        cf_cache["timestamp"] = time.time()

# Run the refresh in a background thread
def background_refresh():
    while True:
        refresh_cloudflare_metrics()
        time.sleep(cf_cache['ttl'])

thread = threading.Thread(target=background_refresh, daemon=True)
thread.start()

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()

            # Core metrics – named to match dashboard queries
            metrics = (
                '# HELP imperial_valuation Total portfolio valuation\n'
                '# TYPE imperial_valuation gauge\n'
                'imperial_valuation 269911162347.394526875\n'
                '# HELP imperial_wealth_gain Market gain\n'
                '# TYPE imperial_wealth_gain gauge\n'
                'imperial_wealth_gain 238050000\n'
                '# HELP imperial_gold_price Gold price in R/g\n'
                '# TYPE imperial_gold_price gauge\n'
                'imperial_gold_price 2746\n'
                '# HELP imperial_energy_flow Energy price in $/MWh\n'
                '# TYPE imperial_energy_flow gauge\n'
                'imperial_energy_flow 9.2\n'
                '# HELP imperial_grid_status Gauteng power grid status\n'
                '# TYPE imperial_grid_status gauge\n'
                'imperial_grid_status 1\n'
                '# HELP imperial_progress Progress to R500B\n'
                '# TYPE imperial_progress gauge\n'
                'imperial_progress 53.98\n'
                '# HELP imperial_lithium_flow Lithium price\n'
                '# TYPE imperial_lithium_flow gauge\n'
                'imperial_lithium_flow 275\n'
                '# HELP imperial_beira_status Port of Beira capacity\n'
                '# TYPE imperial_beira_status gauge\n'
                'imperial_beira_status 14.2\n'
                '# HELP imperial_port_status Overall port status\n'
                '# TYPE imperial_port_status gauge\n'
                'imperial_port_status 1\n'
            )

            # Response times (keep as is)
            mock_times = {
                'IMPERIAL_WEB_UPGRADE': 0.23,
                'SADC_A_LOGISTICS': 0.45,
                'SADC_B_RETAIL': 0.38,
                'Node-RED': 0.12,
                'Prometheus': 0.08,
                'Metrics_API': 0.31,
            }
            for service, value in mock_times.items():
                metrics += f'response_time_seconds{{service="{service}"}} {value}\n'

            # Append cached Cloudflare metrics
            metrics += cf_cache['data']

            self.wfile.write(metrics.encode())
            self.log_to_file('GET', self.path)
            return

        # Original GET behaviour (health check)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Ukuvuselela Webhook Active')
        self.log_to_file('GET', self.path)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received"}).encode())
        self.log_to_file('POST', self.path, body)

    def log_to_file(self, method, path, body=''):
        log_line = f"{datetime.datetime.now().isoformat()} {method} {path}"
        if body:
            log_line += f" body: {body[:200]}"
        with open('/data/data/com.termux/files/home/imperial_network/logs/ukuvo_webhook.log', 'a') as f:
            f.write(log_line + '\n')

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8117), WebhookHandler)
    print("Webhook listening on port 8117")
    server.serve_forever()
