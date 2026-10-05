#!/usr/bin/env python3
import os
import json, re, subprocess, requests, pymysql
from http.server import BaseHTTPRequestHandler, HTTPServer
from bs4 import BeautifulSoup
from googlesearch import search as gsearch

DB_CONFIG = {
    'user': 'root',
    'password': os.environ.get("MYSQL_ROOT_PASSWORD", ""),
    'unix_socket': '/data/data/com.termux/files/home/mysql_run/mysql.sock',
    'database': 'imperial_nexus',
}
LLM_URL = "http://localhost:8118/ai/proxy"
BRIEFING_SCRIPT = "/data/data/com.termux/files/home/imperial_network/scripts/municipal_briefing.sh"

def run_briefing():
    try:
        result = subprocess.run([BRIEFING_SCRIPT], capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else f"Briefing error: {result.stderr}"
    except Exception as e:
        return f"Briefing error: {e}"

def sql_query(sql):
    try:
        conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                return "No data."
            headers = [desc[0] for desc in cur.description]
            lines = [" | ".join(headers)] + [" | ".join(str(c) for c in row) for row in rows]
            return "\n".join(lines)
        conn.close()
    except Exception as e:
        return f"SQL error: {e}"

def web_search(query, num_results=3):
    try:
        results = list(gsearch(query, num_results=num_results, sleep_interval=1))
        snippets = [f"• {url}" for url in results[:num_results]]
        if snippets:
            return "\n".join(snippets)
    except Exception as e:
        print(f"Google error: {e}")
    # DuckDuckGo fallback
    try:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.select('.result')
        snippets = []
        for res in results[:num_results]:
            title = res.select_one('.result__a')
            snippet = res.select_one('.result__snippet')
            if title and snippet:
                snippets.append(f"{title.get_text(strip=True)}: {snippet.get_text(strip=True)}")
            elif title:
                snippets.append(title.get_text(strip=True))
        return "\n".join(snippets) if snippets else "No results."
    except Exception as e:
        return f"Search error: {e}"

def get_known_projects():
    """Return a list of project names from the DB."""
    result = sql_query("SELECT DISTINCT project_name FROM municipal_governance_risks;")
    if result and result != "No data.":
        lines = result.split('\n')
        if len(lines) > 1:
            return [line.strip() for line in lines[1:]]  # skip header
    return []

class ToolHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
            req = json.loads(body)
        except:
            self.send_error(400, "Invalid JSON")
            return

        prompt = req.get('prompt', '').strip()
        if not prompt:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"response": "No prompt provided."}).encode())
            return

        # ---- 1) Check if prompt asks for a specific project ----
        projects = get_known_projects()
        matched_project = None
        for proj in projects:
            if proj.lower() in prompt.lower():
                matched_project = proj
                break
        if matched_project:
            db_result = sql_query(f"SELECT project_name, sector, ward, status, risk_level, description FROM municipal_governance_risks WHERE project_name = '{matched_project}';")
            answer = f"🔍 Project Query: '{matched_project}'\n\n{db_result}"
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"response": answer}).encode())
            return

        # ---- 2) Otherwise, run the full briefing ----
        output = run_briefing()
        answer = f"📊 Imperial Nexus – Municipal Intelligence Report\n\n{output}"
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"response": answer}).encode())

if __name__ == "__main__":
    port = 8120
    print(f"🚀 Imperial Nexus Core – Project‑aware on port {port}")
    HTTPServer(('0.0.0.0', port), ToolHandler).serve_forever()
