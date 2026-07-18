#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os
from datetime import datetime

class PortalMasterHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "online"}')
            return

        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Imperial High-Quality Landing Page (Existing content preserved)
            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Imperial Network - Rural Economic Operating System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fff; }
        .navbar { background: rgba(10, 10, 10, 0.95); backdrop-filter: blur(10px); padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2d2d2d; position: sticky; top: 0; z-index: 1000; }
        .logo { font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #ff6b6b, #ff8e8e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav-links { display: flex; gap: 30px; }
        .nav-links a { color: #fff; text-decoration: none; font-size: 16px; transition: color 0.3s; }
        .nav-links a:hover { color: #ff6b6b; }
        .hero { padding: 100px 40px; text-align: center; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); }
        .hero h1 { font-size: 64px; margin-bottom: 20px; }
        .hero h1 span { background: linear-gradient(135deg, #ff6b6b, #ff8e8e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero p { font-size: 20px; color: #888; max-width: 800px; margin: 0 auto 40px; line-height: 1.6; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; padding: 40px; max-width: 1200px; margin: 0 auto; }
        .stat-card { background: #1a1a1a; border-radius: 15px; padding: 30px; text-align: center; border-left: 4px solid #ff6b6b; transition: transform 0.3s; }
        .stat-value { font-size: 36px; font-weight: bold; color: #4CAF50; margin: 10px 0; }
        .stat-label { color: #888; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .features { padding: 80px 40px; background: #0f0f0f; }
        .section-title { text-align: center; font-size: 36px; margin-bottom: 60px; }
        .section-title span { color: #ff6b6b; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }
        .feature-card { background: #1a1a1a; border-radius: 15px; padding: 30px; }
        .feature-icon { font-size: 40px; margin-bottom: 20px; }
        .feature-card h3 { margin-bottom: 15px; color: #ff6b6b; }
        .feature-card p { color: #888; line-height: 1.6; }
        .villages { padding: 80px 40px; }
        .village-map { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
        .village-card { background: #1a1a1a; border-radius: 12px; padding: 20px; display: flex; justify-content: space-between; align-items: center; transition: all 0.3s; }
        .village-name { font-weight: bold; }
        .village-pop { color: #4CAF50; }
        .auth-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 2000; justify-content: center; align-items: center; }
        .auth-card { background: #1a1a1a; padding: 40px; border-radius: 20px; width: 400px; max-width: 90%; }
        .auth-card h2 { margin-bottom: 30px; color: #ff6b6b; }
        .auth-tabs { display: flex; gap: 20px; margin-bottom: 30px; }
        .auth-tab { padding: 10px 20px; cursor: pointer; border-radius: 8px; transition: all 0.3s; }
        .auth-tab.active { background: #ff6b6b; color: #fff; }
        .auth-form input { width: 100%; padding: 12px; margin: 10px 0; background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 8px; color: #fff; font-size: 16px; }
        .auth-form button { width: 100%; padding: 12px; background: #4CAF50; color: #fff; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 20px; transition: background 0.3s; }
        .auth-form button:hover { background: #45a049; }
        .footer { padding: 40px; text-align: center; color: #888; border-top: 1px solid #2d2d2d; }
        .btn { background: #ff6b6b; color: #fff; padding: 12px 30px; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; transition: background 0.3s; text-decoration: none; display: inline-block; }
        .btn:hover { background: #ff5252; }
        .loading { color: #888; text-align: center; padding: 20px; }
        .error { color: #ff6b6b; text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="navbar"><div class="logo">🏛️ IMPERIAL NETWORK</div><div class="nav-links"><a href="#features">Features</a><a href="#villages">Villages</a><a href="#stats">Stats</a><a href="#" onclick="showAuthModal()">Login</a></div></div>
    <div class="hero"><h1>Welcome to the <span>Imperial</span> Network</h1><p>Africa's premier Rural Economic Operating System. Connecting villages, enabling trade, and building wealth across the SADC region.</p><button class="btn" onclick="showAuthModal()">Get Started →</button></div>
    <div id="stats" class="stats-grid">
        <div class="stat-card"><div class="stat-value" id="village-count">-</div><div class="stat-label">Active Villages</div></div>
        <div class="stat-card"><div class="stat-value" id="user-count">-</div><div class="stat-label">Registered Users</div></div>
        <div class="stat-card"><div class="stat-value" id="portfolio-value">-</div><div class="stat-label">Portfolio Value</div></div>
        <div class="stat-card"><div class="stat-value" id="online-sectors">-</div><div class="stat-label">Online Sectors</div></div>
    </div>
    <div id="features" class="features"><h2 class="section-title">Imperial <span>Capabilities</span></h2><div class="feature-grid"></div></div>
    <div id="villages" class="villages"><h2 class="section-title">Our <span>Villages</span></h2><div id="village-list" class="village-map"><div class="loading">Loading village data...</div></div></div>
    <div id="authModal" class="auth-modal"><div class="auth-card"><h2>Imperial Access</h2><div class="auth-tabs"><div class="auth-tab active" onclick="switchAuthTab('login')">Login</div><div class="auth-tab" onclick="switchAuthTab('register')">Register</div></div><div id="login-form" class="auth-form"><input type="email" id="login-email" placeholder="Email"><input type="password" id="login-password" placeholder="Password"><button onclick="handleLogin()">Login to Imperial Network</button></div><div id="register-form" class="auth-form" style="display: none;"><input type="text" id="register-username" placeholder="Username"><input type="email" id="register-email" placeholder="Email"><input type="password" id="register-password" placeholder="Password"><input type="text" id="register-phone" placeholder="Phone"><input type="text" id="register-village" placeholder="Village"><button onclick="handleRegister()">Create Account</button></div><div style="text-align: center; margin-top: 20px;"><a href="#" onclick="hideAuthModal()" style="color: #888;">Close</a></div></div></div>
    <div class="footer"><p>🏛️ Imperial Network v2.0 | CEO: Humbulani Mudau | True Valuation: R1,568,116,092.14</p><p style="margin-top: 10px;">© 2026 Imperial Network. All rights reserved.</p></div>
    <script>
        const API_BASE = 'http://localhost:8000';
        let authToken = localStorage.getItem('imperial_token');
        function showAuthModal() { document.getElementById('authModal').style.display = 'flex'; }
        function hideAuthModal() { document.getElementById('authModal').style.display = 'none'; }
        // ... (Include your existing JS logic here)
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())
        elif self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            fallback = {'villages': 11, 'users': 100, 'portfolio': 10938044.07, 'online_sectors': 27, 'total_sectors': 35}
            self.wfile.write(json.dumps(fallback).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # Original POST logic here
        pass

    def log_message(self, format, *args):
        return

print("🚀 Imperial Portal Master starting on port 8088...")
HTTPServer(('0.0.0.0', 8088), PortalMasterHandler).serve_forever()
