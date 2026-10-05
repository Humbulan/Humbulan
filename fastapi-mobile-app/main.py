import os
import mysql.connector

def get_db_connection():

    return mysql.connector.connect(

        user="root",

        password=_mysql_password(),

        unix_socket="/data/data/com.termux/files/home/mysql_run/mysql.sock",

        database="imperial_nexus"

    )
from collections import defaultdict
import uuid
import threading
import time
import subprocess
from fastapi import FastAPI, HTTPException, Header, Depends, Depends, Depends, Depends, Depends, Depends, Depends, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse

app = FastAPI()

def mysql_query(sql):
    cmd = [
        "mariadb",
        "-u", "root",
        "-p" + _mysql_password(),
        "-S", "/data/data/com.termux/files/home/mysql_run/mysql.sock",
        "imperial_nexus",
        "-e", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    return result.stdout

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/admin/usage")
async def admin_usage(admin_key: str = Header(None, alias="X-Admin-Key"), payment_id: str = "unknown", fields: str = "basic"):
    if admin_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Never store raw keys — store a short fingerprint
    key_fingerprint = hashlib.sha256(admin_key.encode()).hexdigest()[:12] if admin_key else "none"

    # Sanitize free-text (mysql_query runs `mariadb -e`, no bound params)
    def _clean(s):
        return "".join(ch for ch in str(s) if ch.isalnum() or ch in "_-.")[:64]

    safe_payment_id = _clean(payment_id)
    safe_fields = _clean(fields)

    insert_sql = (
        "INSERT INTO usage_logs (api_key, payment_id, fields) VALUES "
        f"(\"{key_fingerprint}\", \"{safe_payment_id}\", \"{safe_fields}\")"
    )
    try:
        mysql_query(insert_sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert error: {e}")
    
    select_sql = "SELECT timestamp, api_key, payment_id, fields FROM usage_logs"
    try:
        output = mysql_query(select_sql)
        lines = output.strip().split("\n")
        if len(lines) < 2:
            entries = []
        else:
            header = lines[0].split("\t")
            entries = [dict(zip(header, line.split("\t"))) for line in lines[1:]]
        return {"total_requests": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Select error: {e}")

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/portal")


# === Auth helpers for portal ===
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os as _os
import hashlib
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

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == os.getenv("PORTAL_USERNAME", "admin") and credentials.password == os.getenv("PORTAL_PASSWORD", "securepass"):
        return credentials.username
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """

@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """

async def dashboard_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Live Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e17; color: #eee; padding: 20px; }
            .card { background: #1a2332; border-radius: 12px; padding: 20px; margin: 10px; display: inline-block; min-width: 180px; border-left: 4px solid #00d4ff; }
            .value { font-size: 28px; font-weight: bold; color: #00d4ff; }
            .label { font-size: 14px; color: #8a9bb5; text-transform: uppercase; letter-spacing: 1px; }
            .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #00d4ff; }
            .header small { color: #8a9bb5; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏛️ Imperial Network Dashboard</h1>
            <small>Live metrics – auto‑refresh every 10 seconds</small>
        </div>
        <div id="dashboard" class="grid">Loading...</div>
        <script>
            async function fetchData() {
                try {
                    const res = await fetch('/dashboard-latest');
                    const json = await res.json();
                    if (!res.ok) {
                        document.getElementById('dashboard').innerHTML = '<p style="color:red;">Error: ' + (json.detail || 'Unknown') + '</p>';
                        return;
                    }
                    const data = json.data;
                    if (!data) {
                        document.getElementById('dashboard').innerHTML = '<p>No data yet.</p>';
                        return;
                    }
                    const metrics = [
                        { label: 'Valuation (ZAR)', value: data.valuation, fmt: v => Number(v).toLocaleString() },
                        { label: 'Gold Price (R/g)', value: data.gold_price, fmt: v => v },
                        { label: 'Wealth Gain', value: data.wealth_gain, fmt: v => Number(v).toLocaleString() },
                        { label: 'Energy Flow ($/MWh)', value: data.energy_flow, fmt: v => v },
                        { label: 'Grid Status', value: data.grid_status, fmt: v => v == 1 ? '✅ Online' : '❌ Offline' },
                        { label: 'Progress (%)', value: data.progress, fmt: v => v + '%' },
                        { label: 'Lithium Flow (t)', value: data.lithium_flow, fmt: v => v },
                        { label: 'Beira Status (M tons)', value: data.beira_status, fmt: v => v },
                        { label: 'Port Status', value: data.port_status, fmt: v => v == 1 ? '✅ Active' : '❌ Inactive' },
                    ];
                    let html = '';
                    metrics.forEach(m => {
                        const formatted = m.fmt ? m.fmt(m.value) : m.value;
                        html += `<div class="card"><div class="label">${m.label}</div><div class="value">${formatted}</div></div>`;
                    });
                    document.getElementById('dashboard').innerHTML = html;
                } catch (e) {
                    document.getElementById('dashboard').innerHTML = '<p style="color:red;">Error: ' + e.message + '</p>';
                }
            }
            fetchData();
            setInterval(fetchData, 10000);
        </script>
    </body>
    </html>
    """

@app.get("/dashboard-latest")
async def dashboard_latest():
    select_sql = "SELECT * FROM dashboard_metrics ORDER BY id DESC LIMIT 1"
    try:
        output = mysql_query(select_sql)
        lines = output.strip().split("\n")
        if len(lines) < 2:
            return {"data": None}
        header = lines[0].split("\t")
        row = lines[1].split("\t")
        data = dict(zip(header, row))
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB query error: {e}")

@app.get("/dashboard-ui", response_class=HTMLResponse)
async def dashboard_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Live Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e17; color: #eee; padding: 20px; }
            .card { background: #1a2332; border-radius: 12px; padding: 20px; margin: 10px; display: inline-block; min-width: 180px; border-left: 4px solid #00d4ff; }
            .value { font-size: 28px; font-weight: bold; color: #00d4ff; }
            .label { font-size: 14px; color: #8a9bb5; text-transform: uppercase; letter-spacing: 1px; }
            .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #00d4ff; }
            .header small { color: #8a9bb5; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏛️ Imperial Network Dashboard</h1>
            <small>Live metrics – auto‑refresh every 10 seconds</small>
        </div>
        <div id="dashboard" class="grid">Loading...</div>
        <script>
            async function fetchData() {
                try {
                    const res = await fetch('/dashboard-latest');
                    const json = await res.json();
                    if (!res.ok) {
                        document.getElementById('dashboard').innerHTML = '<p style="color:red;">Error: ' + (json.detail || 'Unknown') + '</p>';
                        return;
                    }
                    const data = json.data;
                    if (!data) {
                        document.getElementById('dashboard').innerHTML = '<p>No data yet.</p>';
                        return;
                    }
                    const metrics = [
                        { label: 'Valuation (ZAR)', value: data.valuation, fmt: v => Number(v).toLocaleString() },
                        { label: 'Gold Price (R/g)', value: data.gold_price, fmt: v => v },
                        { label: 'Wealth Gain', value: data.wealth_gain, fmt: v => Number(v).toLocaleString() },
                        { label: 'Energy Flow ($/MWh)', value: data.energy_flow, fmt: v => v },
                        { label: 'Grid Status', value: data.grid_status, fmt: v => v == 1 ? '✅ Online' : '❌ Offline' },
                        { label: 'Progress (%)', value: data.progress, fmt: v => v + '%' },
                        { label: 'Lithium Flow (t)', value: data.lithium_flow, fmt: v => v },
                        { label: 'Beira Status (M tons)', value: data.beira_status, fmt: v => v },
                        { label: 'Port Status', value: data.port_status, fmt: v => v == 1 ? '✅ Active' : '❌ Inactive' },
                    ];
                    let html = '';
                    metrics.forEach(m => {
                        const formatted = m.fmt ? m.fmt(m.value) : m.value;
                        html += `<div class="card"><div class="label">${m.label}</div><div class="value">${formatted}</div></div>`;
                    });
                    document.getElementById('dashboard').innerHTML = html;
                } catch (e) {
                    document.getElementById('dashboard').innerHTML = '<p style="color:red;">Error: ' + e.message + '</p>';
                }
            }
            fetchData();
            setInterval(fetchData, 10000);
        </script>
    </body>
    </html>
    """

@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """

@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """

@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """

@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """

@app.get("/portal", response_class=HTMLResponse)
async def portal(current_user: str = Depends(get_current_user)):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Imperial Data Portal</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f4f4f4; }
            input, button { padding: 10px; width: 100%; margin: 8px 0; }
            button { background: #2d7; border: none; color: white; font-weight: bold; cursor: pointer; }
            #result { background: white; padding: 15px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 Imperial Data Export</h2>
        <p>Logged in as <strong>admin</strong></p>
        <div class="nav">
            <a href="/portal">Export</a> | <a href="/generate-download" onclick="return false;">Generate Download Link</a>
        </div>
        <form id="exportForm">
            <input type="text" id="apiKey" placeholder="Your X-Export-Key" required>
            <input type="text" id="paymentId" placeholder="Payment ID (e.g., tx_001)" required>
            <select id="fields">
                <option value="basic">Basic (tx_id, amount, date)</option>
                <option value="full">Full (id, tx_id, amount, status, created_at)</option>
            </select>
            <button type="submit">Get Data</button>
            <button type="button" id="downloadBtn" onclick="downloadData()">Download CSV</button>
        </form>
        <div id="result"></div>
        <script>
            async function callAPI(endpoint) {
                const key = document.getElementById('apiKey').value;
                const pid = document.getElementById('paymentId').value;
                const fields = document.getElementById('fields').value;
                const res = document.getElementById('result');
                res.innerHTML = 'Loading...';
                try {
                    const response = await fetch(`/${endpoint}?payment_id=${pid}&fields=${fields}`, {
                        headers: { 'X-Export-Key': key }
                    });
                    const data = await response.json();
                    if (response.ok) {
                        if (data.download_link) {
                            res.innerHTML = `<p>Download link: <a href="${data.download_link}" target="_blank">${data.download_link}</a> (expires in ${data.expires_in})</p>`;
                        } else {
                            res.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }
                    } else {
                        res.innerHTML = '<b>Error:</b> ' + (data.detail || 'Unknown error');
                    }
                } catch (err) {
                    res.innerHTML = '<b>Error:</b> ' + err.message;
                }
            }
            document.getElementById('exportForm').addEventListener('submit', (e) => {
                e.preventDefault();
                callAPI('export-data');
            });
            function downloadData() {
                callAPI('generate-download');
            }
        </script>
    </body>
    </html>
    """
def is_valid_export_key(key):
    if not os.path.exists(KEY_FILE):
        return False
    with open(KEY_FILE) as f:
        for line in f:
            if ":" not in line:
                continue
            _, stored_key = line.strip().split(":", 1)
            if stored_key == key:
                return True
    return False

def generate_download_file(data, payment_id):
    if not data:
        return None
    filename = f"{payment_id}_{uuid.uuid4().hex[:8]}.csv"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    header = data[0].keys()
    with open(filepath, 'w') as f:
        f.write(','.join(header) + '\n')
        for row in data:
            f.write(','.join(str(row.get(k, '')) for k in header) + '\n')
    return filepath, filename

@app.get("/download/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found or expired")
    response = FileResponse(filepath, media_type='text/csv', filename=filename)
    async def remove_file():
        if os.path.exists(filepath):
            os.remove(filepath)
    response.background = remove_file
    return response

# === 4. Portal with authentication ===
@app.get("/export-data")
async def export_data(payment_id: str, fields: str = "basic", x_export_key: str = Header(None)):
    if not x_export_key or not is_valid_export_key(x_export_key):
        raise HTTPException(status_code=403, detail="Invalid or missing export key")
    if is_rate_limited(x_export_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    with open(os.path.expanduser("~/imperial_network/usage.log"), "a") as f:
        f.write(f"{time.ctime()}|{x_export_key}|{payment_id}|{fields}\n")
    check_sql = f"SELECT status FROM transactions WHERE tx_id='{payment_id}' LIMIT 1"
    try:
        output = mysql_query(check_sql)
        if "success" not in output:
            raise HTTPException(status_code=402, detail="Payment Required or Invalid ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    columns = "id, tx_id, amount, status, created_at" if fields == "full" else "tx_id, amount, DATE(created_at) as date"
    export_sql = f"SELECT {columns} FROM transactions WHERE status='success'"
    try:
        output = mysql_query(export_sql)
        lines = output.strip().split('\n')
        if len(lines) < 2:
            data = []
        else:
            header = lines[0].split('\t')
            rows = [dict(zip(header, line.split('\t'))) for line in lines[1:]]
            data = rows
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

# === 3. Generate download link ===
@app.get("/generate-download")
async def generate_download(payment_id: str, fields: str = "basic", x_export_key: str = Header(None)):
    if not x_export_key or not is_valid_export_key(x_export_key):
        raise HTTPException(status_code=403, detail="Invalid or missing export key")
    if is_rate_limited(x_export_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    with open(os.path.expanduser("~/imperial_network/usage.log"), "a") as f:
        f.write(f"{time.ctime()}|{x_export_key}|{payment_id}|download|{fields}\n")
    check_sql = f"SELECT status FROM transactions WHERE tx_id='{payment_id}' LIMIT 1"
    try:
        output = mysql_query(check_sql)
        if "success" not in output:
            raise HTTPException(status_code=402, detail="Payment Required or Invalid ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    columns = "id, tx_id, amount, status, created_at" if fields == "full" else "tx_id, amount, DATE(created_at) as date"
    export_sql = f"SELECT {columns} FROM transactions WHERE status='success'"
    try:
        output = mysql_query(export_sql)
        lines = output.strip().split('\n')
        if len(lines) < 2:
            data = []
        else:
            header = lines[0].split('\t')
            rows = [dict(zip(header, line.split('\t'))) for line in lines[1:]]
            data = rows
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        filepath, filename = generate_download_file(data, payment_id)
        if not filepath:
            raise HTTPException(status_code=500, detail="Could not generate file")
        link = f"/download/{filename}"
        return {"download_link": link, "expires_in": "5 minutes"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

@app.post("/yoco-webhook")
async def yoco_webhook(request: Request):
    token = request.query_params.get("token")
    if token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    tx_id = data.get("id")
    amount = data.get("amount")
    status = data.get("status")
    if None in (tx_id, amount, status):
        raise HTTPException(status_code=400, detail="Missing fields")
    sql = f"INSERT INTO transactions (tx_id, amount, status) VALUES ('{tx_id}', {amount}, '{status}')"
    try:
        mysql_query(sql)
        return {"status": "success", "message": "Transaction recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

# === 2. Export (customisable fields) ===
@app.get("/admin/transactions")
async def admin_transactions(admin_key: str = Header(None, alias="X-Admin-Key"), status: str = None):
    if admin_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if status:
        cursor.execute("SELECT * FROM transactions WHERE status = %s ORDER BY id DESC LIMIT 5", (status,))
    else:
        cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 5")
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return {"transactions": entries}

async def root():
    return RedirectResponse(url="/portal")

# === 10. Health ===
@app.get("/admin/metrics")
async def admin_metrics(admin_key: str = Header(None, alias="X-Admin-Key")):
    if admin_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dashboard_metrics ORDER BY id DESC LIMIT 5")
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return {"metrics": entries}

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "E5rbHUSBx63397yO7lV1yApPfZKCyIV")
KEY_FILE = os.path.expanduser("~/imperial_network/api_keys.db")
ADMIN_KEY = os.getenv("ADMIN_KEY", "AdminSecret123")
RATE_LIMIT = 10
RATE_WINDOW = 60
PORTAL_USERNAME = os.getenv("PORTAL_USERNAME", "admin")
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD", "securepass")
DOWNLOAD_DIR = os.path.expanduser("~/imperial_network/downloads")

def is_rate_limited(key):
    now = time.time()
    rate_store[key] = [t for t in rate_store[key] if now - t < RATE_WINDOW]
    if len(rate_store[key]) >= RATE_LIMIT:
        return True
    rate_store[key].append(now)
    return False

def cleanup_downloads():
    now = time.time()
    for f in os.listdir(DOWNLOAD_DIR):
        fp = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(fp) and (now - os.path.getmtime(fp)) > 3600:
            os.remove(fp)
    threading.Timer(3600, cleanup_downloads).start()
cleanup_downloads()
rate_store = defaultdict(list)
