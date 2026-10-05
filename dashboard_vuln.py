#!/usr/bin/env python3
import os
import http.server
import socketserver
import pymysql
from urllib.parse import urlparse, parse_qs

DB_SOCKET = "/data/data/com.termux/files/home/mysql_run/mysql.sock"
DB_USER = "root"
DB_PASS = os.environ.get("MYSQL_ROOT_PASSWORD", "")
DB_NAME = "imperial_nexus"

def get_recent_vulns(limit=20):
    conn = pymysql.connect(unix_socket=DB_SOCKET, user=DB_USER, password=DB_PASS, database=DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, vulnerability_type, severity, target_port, logged_at, notified FROM vulnerability_logs ORDER BY logged_at DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

class ReuseTCPServer(ReuseTCPServer):
    allow_reuse_address = True
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/vuln"):
            rows = get_recent_vulns(50)
            html = "<html><head><title>Vulnerability Dashboard</title>"
            html += "<style>body { font-family: sans-serif; } table { border-collapse: collapse; } td, th { border: 1px solid #ccc; padding: 8px; }</style></head>"
            html += "<body><h1>Recent Vulnerabilities</h1><table><tr><th>ID</th><th>Type</th><th>Severity</th><th>Port</th><th>Logged</th><th>Notified</th></tr>"
            for r in rows:
                html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{'Yes' if r[5] else 'No'}</td></tr>"
            html += "</table></body></html>"
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8130
    with ReuseTCPServer(("", PORT), MyHandler) as httpd:
        print(f"Dashboard running at http://127.0.0.1:{PORT}/vuln")
        httpd.serve_forever()
