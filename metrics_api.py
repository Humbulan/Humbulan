#!/usr/bin/env python3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import mysql.connector
import os

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # --- Existing JSON endpoint ---
        if self.path == "/api/metrics":
            try:
                conn = mysql.connector.connect(
                    user='root',
                    password=os.environ.get("MYSQL_ROOT_PASSWORD", ""),
                    host='127.0.0.1',
                    unix_socket='/data/data/com.termux/files/home/mysql_run/mysql.sock',
                    database='imperial_nexus'
                )
                cursor = conn.cursor(dictionary=True)

                # 1. Existing imperial_metrics (if any)
                cursor.execute("SELECT metric_name, metric_value FROM imperial_metrics ORDER BY recorded_at DESC LIMIT 20")
                rows = cursor.fetchall()
                metrics = {row['metric_name']: row['metric_value'] for row in rows}

                # 2. Add SADC metrics (latest per metric_name)
                cursor.execute("""
                    SELECT metric_name, metric_value, unit
                    FROM sadc_metrics
                    WHERE (metric_name, logged_at) IN (
                        SELECT metric_name, MAX(logged_at)
                        FROM sadc_metrics
                        GROUP BY metric_name
                    )
                """)
                sadc_rows = cursor.fetchall()
                for row in sadc_rows:
                    key = f"SADC_{row['metric_name']}"
                    val = f"{row['metric_value']} {row['unit']}"
                    metrics[key] = val

                conn.close()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(metrics).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'{{"error":"{str(e)}"}}'.encode())

        # --- NEW: Prometheus /metrics endpoint ---
        elif self.path == "/metrics":
            try:
                conn = mysql.connector.connect(
                    user='root',
                    password=os.environ.get("MYSQL_ROOT_PASSWORD", ""),
                    host='127.0.0.1',
                    unix_socket='/data/data/com.termux/files/home/mysql_run/mysql.sock',
                    database='imperial_nexus'
                )
                cursor = conn.cursor()
                cursor.execute("SELECT service_name, response_time FROM system_sectors WHERE response_time IS NOT NULL")
                rows = cursor.fetchall()
                lines = []
                for service, latency in rows:
                    if latency is not None:
                        lines.append(f'response_time_seconds{{service="{service}"}} {latency}')
                conn.close()

                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                self.wfile.write('\n'.join(lines).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'# ERROR: {e}'.encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 5006), MetricsHandler)
    print("Metrics API running on port 5006 (JSON: /api/metrics, Prometheus: /metrics)")
    server.serve_forever()
