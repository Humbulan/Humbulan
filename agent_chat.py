#!/usr/bin/env python3
"""Imperial Nexus Agent — Browser Command Console"""
import os
import subprocess
from flask import Flask, request, jsonify

AGENT_DIR = "/data/data/com.termux/files/home/Build-your-own-Claude-Code"
AGENT_PY  = os.path.join(AGENT_DIR, ".venv/bin/python3")
MAIN_PY   = os.path.join(AGENT_DIR, "app/main.py")

app = Flask(__name__)

AGENT_USER = os.environ.get("AGENT_USER", "humbu")
AGENT_PASS = os.environ.get("AGENT_PASS", "ImperialNexus2026!")

@app.before_request
def _require_auth():
    if request.path == "/health":
        return None
    auth = request.authorization
    if not auth or auth.username != AGENT_USER or auth.password != AGENT_PASS:
        return (
            "<html><body style='background:#0a0f18;color:#f0a838;font-family:sans-serif;text-align:center;padding:60px'>"
            "<h2>\U0001F512 Imperial Nexus — Authentication Required</h2>"
            "<p style='color:#7d8a9f'>Enter your credentials to access the agent console.</p>"
            "</body></html>",
            401,
            {"WWW-Authenticate": 'Basic realm="Imperial Nexus"'},
        )

@app.route("/health")
def health():
    return {"status": "ok"}


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Imperial Nexus — Agent Console</title>
<style>
  :root {
    --bg:#070a10; --bg2:#0c1119; --panel:#111823; --panel2:#18202e;
    --border:#232d3f; --border2:#2d3a52;
    --text:#e8eef7; --dim:#7d8a9f; --dim2:#4d5a70;
    --amber:#f0a838; --amber-glow:rgba(240,168,56,.18);
    --green:#3fb950; --red:#f85149; --blue:#58a6ff; --purple:#a371f7;
  }
  * { box-sizing:border-box; margin:0; padding:0; }
  html,body { height:100%; }
  body {
    background:var(--bg); color:var(--text); height:100vh; display:grid;
    grid-template-columns:280px 1fr; grid-template-rows:60px 1fr;
    font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    overflow:hidden;
  }
  /* ---------- HEADER ---------- */
  header {
    grid-column:1/-1; padding:0 20px; background:linear-gradient(180deg,#0d131d,#0a0f18);
    border-bottom:1px solid var(--border); display:flex; align-items:center; gap:14px;
    box-shadow:0 1px 0 rgba(240,168,56,.06),0 8px 24px rgba(0,0,0,.4);
  }
  .crown {
    width:34px; height:34px; border-radius:9px; display:grid; place-items:center;
    background:linear-gradient(135deg,#1a2333,#0f1725); border:1px solid var(--border2);
    font-size:19px; box-shadow:inset 0 0 12px var(--amber-glow);
  }
  .brand h1 {
    font-size:14px; font-weight:700; letter-spacing:2.5px; color:var(--text);
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  }
  .brand .sub { font-size:10.5px; color:var(--dim); letter-spacing:.6px; margin-top:1px; }
  .status {
    margin-left:auto; display:flex; align-items:center; gap:8px;
    font-size:11px; color:var(--dim); font-family:ui-monospace,Menlo,monospace;
    padding:6px 12px; background:var(--panel); border:1px solid var(--border);
    border-radius:20px;
  }
  .dot { width:7px; height:7px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); animation:pulse 2s infinite; }
  .dot.busy { background:var(--amber); box-shadow:0 0 8px var(--amber); }
  .dot.off { background:var(--red); box-shadow:0 0 8px var(--red); }
  @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.4;} }
  .menu-btn { display:none; background:transparent; border:1px solid var(--border); color:var(--dim); padding:6px 10px; border-radius:6px; cursor:pointer; }

  /* ---------- SIDEBAR ---------- */
  aside {
    background:var(--bg2); border-right:1px solid var(--border); overflow-y:auto;
    padding:18px 14px; display:flex; flex-direction:column; gap:16px;
  }
  .sect-label {
    font-size:9.5px; font-weight:700; letter-spacing:1.6px; color:var(--dim2);
    text-transform:uppercase; margin-bottom:8px;
  }
  .card {
    background:var(--panel); border:1px solid var(--border); border-radius:10px;
    padding:12px 14px;
  }
  .stat-row { display:flex; justify-content:space-between; align-items:baseline; padding:5px 0; font-size:12px; }
  .stat-row + .stat-row { border-top:1px solid var(--border); }
  .stat-row .v { font-family:ui-monospace,Menlo,monospace; color:var(--amber); font-weight:600; }
  .stat-row .k { color:var(--dim); }
  .quick { display:flex; flex-direction:column; gap:6px; }
  .quick button {
    text-align:left; background:var(--panel); border:1px solid var(--border);
    color:var(--text); padding:9px 12px; border-radius:8px; cursor:pointer;
    font-size:12px; transition:all .15s; font-family:inherit;
  }
  .quick button:hover { background:var(--panel2); border-color:var(--amber); transform:translateX(2px); }
  .quick button::before { content:"▸ "; color:var(--amber); margin-right:2px; }
  .links a {
    display:block; padding:7px 0; color:var(--dim); text-decoration:none;
    font-size:12px; border-bottom:1px solid var(--border); transition:color .15s;
  }
  .links a:last-child { border-bottom:none; }
  .links a:hover { color:var(--amber); }
  .ceo-block { font-size:11px; color:var(--dim); line-height:1.7; padding:0 4px; }
  .ceo-block b { color:var(--text); font-weight:600; }
  .ceo-block .title { color:var(--amber); font-size:10px; letter-spacing:1px; }

  /* ---------- CHAT ---------- */
  main { display:flex; flex-direction:column; overflow:hidden; background:radial-gradient(ellipse at top,rgba(240,168,56,.03),transparent 60%),var(--bg); }
  #chat { flex:1; overflow-y:auto; padding:24px 26px 20px; scroll-behavior:smooth; }
  #chat::-webkit-scrollbar, aside::-webkit-scrollbar { width:8px; }
  #chat::-webkit-scrollbar-thumb, aside::-webkit-scrollbar-thumb { background:var(--border2); border-radius:8px; }
  #chat::-webkit-scrollbar-track, aside::-webkit-scrollbar-track { background:transparent; }

  .msg { max-width:820px; margin:0 auto 18px; display:flex; gap:12px; animation:fadeUp .3s ease; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(6px);} to{opacity:1;transform:none;} }
  .msg.user { flex-direction:row-reverse; }
  .avatar {
    flex-shrink:0; width:34px; height:34px; border-radius:9px; display:grid; place-items:center;
    font-size:16px; background:linear-gradient(135deg,#1a2333,#0f1725);
    border:1px solid var(--border2);
  }
  .msg.user .avatar { background:linear-gradient(135deg,#1c3a66,#122a4d); border-color:#2c5282; }
  .bubble {
    flex:1; padding:13px 17px; border-radius:12px; background:var(--panel);
    border:1px solid var(--border); border-left:3px solid var(--amber);
    white-space:pre-wrap; word-wrap:break-word; font-size:13.5px; line-height:1.65;
  }
  .msg.user .bubble { background:linear-gradient(180deg,#16233a,#111a2b); border-color:#243350; border-left:none; border-right:3px solid var(--blue); }
  .msg.error .bubble { border-left-color:var(--red); background:rgba(248,81,73,.05); }
  .meta { font-size:10.5px; color:var(--dim2); margin-top:9px; font-family:ui-monospace,Menlo,monospace; display:flex; gap:14px; }
  .meta span { display:inline-flex; align-items:center; gap:4px; }
  .bubble code { background:var(--bg); border:1px solid var(--border); padding:1px 6px; border-radius:4px; font-family:ui-monospace,Menlo,monospace; font-size:12px; color:var(--amber); }
  .bubble strong { color:var(--text); font-weight:600; }

  .thinking .bubble { color:var(--dim); font-style:italic; border-left-color:var(--dim2); }
  .thinking .bubble::after { content:""; display:inline-block; animation:dots 1.4s steps(4,end) infinite; }
  @keyframes dots { 0%{content:"";} 25%{content:".";} 50%{content:"..";} 75%{content:"...";} 100%{content:"";} }

  /* Welcome block */
  .welcome { max-width:820px; margin:0 auto 26px; padding:22px 24px; background:linear-gradient(135deg,rgba(240,168,56,.06),rgba(240,168,56,.01)); border:1px solid rgba(240,168,56,.22); border-radius:14px; box-shadow:inset 0 0 40px rgba(240,168,56,.03); }
  .welcome h2 { font-size:15px; letter-spacing:2px; color:var(--amber); margin-bottom:4px; font-family:ui-monospace,Menlo,monospace; }
  .welcome .tag { font-size:10.5px; color:var(--dim); letter-spacing:1.4px; text-transform:uppercase; margin-bottom:14px; }
  .welcome p { font-size:13px; color:var(--text); line-height:1.75; margin-bottom:8px; }
  .welcome ul { margin:12px 0 12px 4px; list-style:none; }
  .welcome li { font-size:12.5px; color:var(--dim); padding:3px 0; }
  .welcome li::before { content:"◆ "; color:var(--amber); font-size:9px; margin-right:4px; }
  .welcome .sig { margin-top:16px; padding-top:12px; border-top:1px solid rgba(240,168,56,.15); font-size:11.5px; color:var(--dim); }
  .welcome .sig b { color:var(--amber); font-weight:600; letter-spacing:.5px; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
  .chip {
    background:rgba(240,168,56,.08); border:1px solid rgba(240,168,56,.28); color:var(--amber);
    padding:7px 14px; border-radius:20px; font-size:11.5px; cursor:pointer;
    font-family:inherit; transition:all .15s; letter-spacing:.3px;
  }
  .chip:hover { background:rgba(240,168,56,.18); border-color:var(--amber); transform:translateY(-1px); }

  /* Input */
  footer { padding:14px 26px 18px; background:linear-gradient(0deg,#0a0f18,#070a10); border-top:1px solid var(--border); }
  .input-wrap { max-width:820px; margin:0 auto; position:relative; }
  textarea {
    width:100%; background:var(--panel); border:1px solid var(--border); border-radius:12px;
    color:var(--text); padding:14px 118px 14px 18px; font:inherit; resize:none;
    min-height:52px; max-height:180px; transition:border-color .15s, box-shadow .15s;
  }
  textarea:focus { outline:none; border-color:var(--amber); box-shadow:0 0 0 3px var(--amber-glow); }
  textarea::placeholder { color:var(--dim2); }
  .send {
    position:absolute; right:8px; bottom:9px; height:36px; padding:0 18px;
    background:linear-gradient(180deg,#f0a838,#d68f1e); color:#0a0f18; border:none;
    border-radius:8px; font-weight:700; font-size:12.5px; letter-spacing:.8px;
    cursor:pointer; font-family:inherit; transition:all .15s;
  }
  .send:hover { filter:brightness(1.1); box-shadow:0 0 14px var(--amber-glow); }
  .send:disabled { opacity:.35; cursor:not-allowed; }
  .helper { max-width:820px; margin:8px auto 0; font-size:10.5px; color:var(--dim2); display:flex; justify-content:space-between; font-family:ui-monospace,Menlo,monospace; }
  .helper button { background:transparent; border:none; color:var(--dim2); cursor:pointer; font-size:10.5px; font-family:inherit; padding:0; }
  .helper button:hover { color:var(--amber); }

  /* Mobile */
  @media (max-width:820px) {
    body { grid-template-columns:1fr; }
    aside { position:fixed; top:60px; left:0; bottom:0; width:280px; z-index:20; transform:translateX(-100%); transition:transform .25s; box-shadow:8px 0 24px rgba(0,0,0,.5); }
    aside.open { transform:none; }
    .menu-btn { display:block; margin-left:auto; }
    .status { display:none; }
    #chat, footer { padding-left:16px; padding-right:16px; }
  }
</style>
</head>
<body>

<header>
  <div class="crown">👑</div>
  <div class="brand">
    <h1>IMPERIAL NEXUS</h1>
    <div class="sub">Agent Command Console · v2.0</div>
  </div>
  <div class="status" id="status"><span class="dot"></span><span id="status-text">READY</span></div>
  <button class="menu-btn" onclick="toggleSidebar()">☰</button>
</header>

<aside id="sidebar">
  <div>
    <div class="sect-label">System</div>
    <div class="card">
      <div class="stat-row"><span class="k">Services</span><span class="v" id="ports">— / 76</span></div>
      <div class="stat-row"><span class="k">Database</span><span class="v" style="color:var(--green)">ONLINE</span></div>
      <div class="stat-row"><span class="k">Prometheus</span><span class="v" style="color:var(--green)">:9091</span></div>
      <div class="stat-row"><span class="k">Grafana</span><span class="v" style="color:var(--green)">:3001</span></div>
      <div class="stat-row"><span class="k">Agent</span><span class="v" style="color:var(--purple)">ONLINE</span></div>
    </div>
  </div>

  <div>
    <div class="sect-label">Quick Commands</div>
    <div class="quick">
      <button onclick="quick('Give me a full system status report')">System status report</button>
      <button onclick="quick('What is the current real revenue and where is it coming from?')">Revenue breakdown</button>
      <button onclick="quick('Show me today\\'s commodity prices and any alerts')">Commodities & alerts</button>
      <button onclick="quick('Check the last 10 lines of logs/sadc_alerts.log')">Tail recent alerts</button>
      <button onclick="quick('List all files in ~/imperial_network/scripts/ and briefly describe each')">Scripts inventory</button>
    </div>
  </div>

  <div>
    <div class="sect-label">Dashboards</div>
    <div class="links">
      <a href="http://localhost:3001/" target="_blank">Grafana → :3001</a>
      <a href="http://localhost:9091/" target="_blank">Prometheus → :9091</a>
      <a href="http://localhost:9092/" target="_blank">Pushgateway → :9092</a>
      <a href="http://localhost:9093/" target="_blank">Alertmanager → :9093</a>
    </div>
  </div>

  <div style="margin-top:auto">
    <div class="sect-label">Operator</div>
    <div class="ceo-block">
      <b>Humbulani Mudau</b><br>
      <span class="title">LEAD CYBER SECURITY ARCHITECT</span><br>
      <span style="color:var(--dim2)">Humbu Wandeme Trading Enterprise</span>
    </div>
  </div>
</aside>

<main>
  <div id="chat"></div>
  <footer>
    <div class="input-wrap">
      <textarea id="prompt" placeholder="Ask the Imperial Nexus agent anything…" rows="1"></textarea>
      <button class="send" id="send" onclick="send()">SEND</button>
    </div>
    <div class="helper">
      <span>Enter to send · Shift+Enter for newline</span>
      <button onclick="clearChat()">⟲ clear conversation</button>
    </div>
  </footer>
</main>

<script>
const chat = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');
const statusText = document.getElementById('status-text');
const statusDot = document.querySelector('#status .dot');

const WELCOME = `
<div class="welcome">
  <h2>👑 IMPERIAL NEXUS AGENT</h2>
  <div class="tag">Live Command Console</div>
  <p>Greetings, CEO. I am the <b>Imperial Nexus Agent</b>, your personal AI running directly on this device.</p>
  <p>I have live access to:</p>
  <ul>
    <li>76 services across ports 1880–11434</li>
    <li>MariaDB — imperial_nexus database</li>
    <li>Prometheus · Pushgateway · Grafana stack</li>
    <li>The imperial_network codebase</li>
    <li>Web search for real-time information</li>
  </ul>
  <div class="sig">
    <b>Humbulani Mudau</b> — Lead Cyber Security Architect<br>
    <span style="color:var(--dim2)">Humbu Wandeme Trading Enterprise</span>
  </div>
  <div class="chips">
    <button class="chip" onclick="quick('Give me a full system status report')">System status</button>
    <button class="chip" onclick="quick('What is the current real revenue and where is it coming from?')">Revenue</button>
    <button class="chip" onclick="quick('Show me today\\'s commodity prices')">Commodities</button>
    <button class="chip" onclick="quick('What were the last errors in the logs?')">Recent errors</button>
  </div>
</div>`;

function escapeHTML(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function renderMD(s) {
  let h = escapeHTML(s);
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  return h;
}

function addMsg(text, cls, meta) {
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + cls;
  const av = document.createElement('div');
  av.className = 'avatar';
  av.textContent = cls.includes('user') ? '👤' : '👑';
  const bub = document.createElement('div');
  bub.className = 'bubble';
  if (cls.includes('user') || cls.includes('error')) {
    bub.textContent = text;
  } else {
    bub.innerHTML = renderMD(text);
  }
  if (meta) {
    const m = document.createElement('div');
    m.className = 'meta';
    m.innerHTML = meta;
    bub.appendChild(m);
  }
  wrap.appendChild(av);
  wrap.appendChild(bub);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

function showWelcome() {
  const d = document.createElement('div');
  d.innerHTML = WELCOME;
  chat.appendChild(d.firstElementChild);
}

function clearChat() {
  if (!confirm('Clear this conversation?')) return;
  chat.innerHTML = '';
  localStorage.removeItem('imperial_chat_v2');
  showWelcome();
}
function saveChat() { localStorage.setItem('imperial_chat_v2', chat.innerHTML); }
function restoreChat() {
  const s = localStorage.getItem('imperial_chat_v2');
  if (s) { chat.innerHTML = s; chat.scrollTop = chat.scrollHeight; }
  else { showWelcome(); }
}
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }
function quick(t) { promptEl.value = t; promptEl.focus(); autoGrow(); }

function setStatus(state, text) {
  statusDot.className = 'dot' + (state === 'busy' ? ' busy' : state === 'off' ? ' off' : '');
  statusText.textContent = text;
}

function autoGrow() {
  promptEl.style.height = 'auto';
  promptEl.style.height = Math.min(promptEl.scrollHeight, 180) + 'px';
}
promptEl.addEventListener('input', autoGrow);

promptEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

async function send() {
  const text = promptEl.value.trim();
  if (!text) return;
  if (chat.querySelector('.welcome')) chat.querySelector('.welcome').remove();

  promptEl.value = ''; autoGrow();
  addMsg(text, 'user');
  saveChat();

  const thinking = addMsg('Thinking', 'agent thinking');
  sendBtn.disabled = true;
  setStatus('busy', 'PROCESSING');
  const t0 = Date.now();

  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({prompt: text})
    });
    const data = await r.json();
    const secs = ((Date.now() - t0) / 1000).toFixed(1);
    thinking.remove();
    if (data.error) {
      addMsg('⚠ ' + data.error, 'agent error', `⏱ ${secs}s`);
    } else {
      const toolStr = (data.tools_used || 0) === 1 ? '1 tool' : (data.tools_used || 0) + ' tools';
      addMsg(data.response, 'agent', `<span>⏱ ${secs}s</span><span>🔧 ${toolStr}</span><span>🕐 ${new Date().toLocaleTimeString()}</span>`);
    }
  } catch (e) {
    thinking.remove();
    addMsg('⚠ Network error: ' + e.message, 'agent error');
  } finally {
    sendBtn.disabled = false;
    setStatus('', 'READY');
    saveChat();
  }
}

async function pollStatus() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    document.getElementById('ports').textContent = d.online + ' / ' + d.total;
  } catch (e) {}
}

restoreChat();
pollStatus();
setInterval(pollStatus, 60000);
</script>
</body>
</html>"""

PORTS = [1880,1883,8000,8001,8080,8081,8082,8083,8085,8086,8087,8088,8090,8091,
         8092,8093,8094,8095,8096,8097,8098,8099,8100,8101,8102,8103,8104,8105,
         8106,8107,8108,8110,8111,8112,8113,8114,8115,8117,8118,8119,8120,8121,
         8122,8191,8880,8885,8888,8889,8890,9001,9002,9003,9090,9091,9092,9093,
         9102,11434,12345,18789,3001,3006,5001,5002,5003,5006,5007,5008,5173,
         65412,65413,8084,8089,8002,8005,3306]

@app.route("/")
def index():
    return HTML

@app.route("/api/status")
def status():
    import socket
    online = 0
    for p in PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.08)
        try:
            if s.connect_ex(("127.0.0.1", p)) == 0:
                online += 1
        except Exception:
            pass
        finally:
            s.close()
    return jsonify({"online": online, "total": len(PORTS)})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
    if not os.path.exists(AGENT_PY) or not os.path.exists(MAIN_PY):
        return jsonify({"error": "Agent not found"}), 500
    try:
        r = subprocess.run(
            [AGENT_PY, MAIN_PY, "-p", prompt],
            capture_output=True, text=True, timeout=240, cwd=AGENT_DIR,
        )
        out = (r.stdout or "").strip()
        if r.returncode != 0 and not out:
            return jsonify({"error": (r.stderr or "").strip()[:500]}), 500
        return jsonify({"response": out or "(no output)", "tools_used": 0})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Agent timed out after 240s"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("👑 Imperial Nexus Agent Console running on http://0.0.0.0:8098")
    app.run(host="0.0.0.0", port=8098, threaded=True)
