#!/usr/bin/env python3
import os
import pymysql
from flask import Flask, render_template_string
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# Auth
DASH_USER = os.getenv('DASH_USER', 'admin')
DASH_PASS = os.getenv('DASH_PASS', 'Imperia1')
users = { DASH_USER: generate_password_hash(DASH_PASS) }

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# DB config
DB_CONFIG = {
    'user': 'root',
    'password': os.environ.get("MYSQL_ROOT_PASSWORD", ""),
    'unix_socket': '/data/data/com.termux/files/home/mysql_run/mysql.sock',
    'database': 'imperial_nexus'
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def get_performance_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            l.admin_district,
            p.rank,
            p.items,
            v.population,
            ROUND((p.items / NULLIF(v.population, 0)) * (10 - p.rank), 2) AS priority_score,
            COALESCE(SUM(b.variance), 0) AS total_variance
        FROM village_performance p
        JOIN village_lookup l ON p.village = l.local_name
        JOIN villages v ON l.admin_district = v.name
        LEFT JOIN budget_variance b ON l.admin_district = b.district
        GROUP BY l.admin_district, p.rank, p.items, v.population
        ORDER BY priority_score DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_beira_wait():
    try:
        with open(os.path.expanduser('~/imperial_network/cache/beira_wait.txt'), 'r') as f:
            return f.read().strip()
    except:
        return "15.7"

def get_history(table, columns, order="timestamp DESC LIMIT 30"):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {columns} FROM {table} ORDER BY {order}")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Imperial Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 20px; }
        h1 { color: #ffcc00; }
        .section { margin: 30px 0; padding: 15px; background: #151515; border-left: 4px solid #ffcc00; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        th, td { border: 1px solid #444; padding: 10px; text-align: left; }
        th { background: #222; }
        tr:nth-child(even) { background: #1a1a1a; }
        .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px; }
        .chart-box { background: #1a1a1a; padding: 15px; border-radius: 8px; }
        canvas { max-height: 200px; width: 100% !important; }
        @media (max-width: 768px) { .chart-grid { grid-template-columns: 1fr; } }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>🏛️ Imperial Nexus Dashboard</h1>

    <div class="section">
        <h2>📊 District Performance & Budget</h2>
        <table>
            <tr><th>District</th><th>Rank</th><th>Items</th><th>Population</th><th>Priority</th><th>Budget Variance</th></tr>
            {% for row in data %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }}</td>
                <td>{{ row[3] }}</td>
                <td>{{ row[4] }}</td>
                <td>{{ row[5] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="section">
        <h2>🚢 Beira Corridor</h2>
        <p><strong>Median Wait Time:</strong> {{ beira_wait }} days</p>
        <p><strong>Status:</strong> {% if beira_wait|float > 10 %}🔴 Congested (recommend diversion){% else %}🟢 Normal{% endif %}</p>
        <div class="chart-grid">
            <div class="chart-box">
                <canvas id="beiraChart"></canvas>
            </div>
            <div class="chart-box">
                <canvas id="rankChart"></canvas>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📈 Financial & Performance Trends</h2>
        <div class="chart-grid">
            <div class="chart-box">
                <canvas id="varianceChart"></canvas>
            </div>
            <div class="chart-box">
                <canvas id="priorityChart"></canvas>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📈 900‑Village Rollout</h2>
        <p>ROI: <strong>+R1,758,000,000</strong> (Q4 2026)</p>
    </div>

    <script>
        // 1. Beira wait history
        const beiraData = {{ beira_history | tojson }};
        new Chart(document.getElementById('beiraChart'), {
            type: 'line',
            data: {
                labels: beiraData.map(d => d[0]),
                datasets: [{ label: 'Wait Days', data: beiraData.map(d => d[1]), borderColor: '#ffcc00', fill: false }]
            },
            options: { responsive: true, plugins: { legend: { labels: { color: '#eee' } } }, scales: { x: { ticks: { color: '#aaa' } }, y: { ticks: { color: '#aaa' } } } }
        });

        // 2. Rank evolution (last 30)
        const rankData = {{ rank_history | tojson }};
        new Chart(document.getElementById('rankChart'), {
            type: 'line',
            data: {
                labels: rankData.map(d => d[0]),
                datasets: [{ label: 'Rank (lower is better)', data: rankData.map(d => d[2]), borderColor: '#ff6b6b', fill: false }]
            },
            options: { responsive: true, plugins: { legend: { labels: { color: '#eee' } } }, scales: { x: { ticks: { color: '#aaa' } }, y: { reverse: true, ticks: { color: '#aaa' } } } }
        });

        // 3. Budget variance trend (last 30)
        const varianceData = {{ variance_history | tojson }};
        new Chart(document.getElementById('varianceChart'), {
            type: 'bar',
            data: {
                labels: varianceData.map(d => d[0]),
                datasets: [{ label: 'Budget Variance (R)', data: varianceData.map(d => d[2]), backgroundColor: '#4ecdc4' }]
            },
            options: { responsive: true, plugins: { legend: { labels: { color: '#eee' } } }, scales: { x: { ticks: { color: '#aaa' } }, y: { ticks: { color: '#aaa' } } } }
        });

        // 4. Priority score history (last 30)
        const priData = {{ priority_history | tojson }};
        new Chart(document.getElementById('priorityChart'), {
            type: 'bar',
            data: {
                labels: priData.map(d => d[0]),
                datasets: [{ label: 'Priority Score', data: priData.map(d => d[2]), backgroundColor: '#ffcc00' }]
            },
            options: { responsive: true, plugins: { legend: { labels: { color: '#eee' } } }, scales: { x: { ticks: { color: '#aaa' } }, y: { ticks: { color: '#aaa' } } } }
        });
    </script>
</body>
</html>
"""

@app.route('/')
@auth.login_required
def dashboard():
    data = get_performance_data()
    wait = get_beira_wait()
    bhistory = get_history('beira_wait_history', 'timestamp, wait_days')
    rhistory = get_history('rank_history', 'timestamp, district, rank_value')
    vhistory = get_history('budget_variance_history', 'timestamp, district, variance')
    phistory = get_history('priority_history', 'timestamp, district, priority_score')
    return render_template_string(
        HTML_TEMPLATE,
        data=data,
        beira_wait=wait,
        beira_history=bhistory,
        rank_history=rhistory,
        variance_history=vhistory,
        priority_history=phistory
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=False)
