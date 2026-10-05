#!/usr/bin/env python3
"""Imperial Agent Chat — Browser UI for your_program.sh"""
import os
import shlex
import subprocess
from flask import Flask, request, jsonify

AGENT_DIR = "/data/data/com.termux/files/home/Build-your-own-Claude-Code"
AGENT_PY  = os.path.join(AGENT_DIR, ".venv/bin/python3")
MAIN_PY   = os.path.join(AGENT_DIR, "app/main.py")

app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Imperial Agent</title>
<style>
  :root { --bg:#0d1117; --panel:#161b22; --border:#30363d; --text:#e6edf3; --dim:#8b949e; --accent:#e8a33d; --user:#1f6feb; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--text); font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",monospace; height:100vh; display:flex; flex-direction:column; }
  header { padding:14px 18px; border-bottom:1px solid var(--border); background:var(--panel); display:flex; align-items:center; gap:10px; }
  header .logo { font-size:20px; }
  header h1 { font-size:15px; font-weight:600; letter-spacing:.5px; }
  header .sub { color:var(--dim); font-size:12px; margin-left:auto; }
  #chat { flex:1; overflow-y:auto; padding:18px; scroll-behavior:smooth; }
  .msg { max-width:80%; padding:10px 14px; margin:8px 0; border-radius:10px; white-space:pre-wrap; word-wrap:break-word; }
  .user { background:var(--user); margin-left:auto; border-bottom-right-radius:2px; }
  .agent { background:var(--panel); border:1px solid var(--border); border-bottom-left-radius:2px; }
  .agent.error { border-color:#f85149; color:#ffa198; }
  .meta { font-size:11px; color:var(--dim); margin-top:6px; }
  .thinking { color:var(--dim); font-style:italic; }
  .thinking::after { content:"..."; animation:dots 1.4s steps(3,end) infinite; }
  @keyframes dots { 0%{content:"";} 33%{content:".";} 66%{content:"..";} 100%{content:"...";} }
  footer { padding:12px 14px; border-top:1px solid var(--border); background:var(--panel); display:flex; gap:8px; }
  textarea { flex:1; background:var(--bg); border:1px solid var(--border); border-radius:8px; color:var(--text); padding:10px 12px; font:inherit; resize:none; max-height:120px; min-height:44px; }
  textarea:focus { outline:none; border-color:var(--accent); }
  button { background:var(--accent); color:#0d1117; border:none; border-radius:8px; padding:0 20px; font-weight:600; cursor:pointer; font-size:13px; }
  button:disabled { opacity:.4; cursor:not-allowed; }
  button.clear { background:transparent; color:var(--dim); padding:0 12px; }
</style>
</head>
<body>
<header>
  <span class="logo">👑</span>
  <h1>IMPERIAL AGENT</h1>
  <span class="sub" id="status">ready</span>
</header>
<div id="chat"></div>
<footer>
  <textarea id="prompt" placeholder="Ask the agent anything… (Enter to send, Shift+Enter for newline)"></textarea>
  <button class="clear" onclick="clearChat()">clear</button>
  <button id="send" onclick="send()">Send</button>
</footer>
<script>
const chat = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');
const statusEl = document.getElementById('status');

function addMsg(text, cls, meta) {
  const d = document.createElement('div');
  d.className = 'msg ' + cls;
  d.textContent = text;
  if (meta) {
    const m = document.createElement('div');
    m.className = 'meta';
    m.textContent = meta;
    d.appendChild(m);
  }
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
}

function clearChat() {
  chat.innerHTML = '';
  localStorage.removeItem('imperial_chat');
}

function saveChat() {
  localStorage.setItem('imperial_chat', chat.innerHTML);
}

function restoreChat() {
  const saved = localStorage.getItem('imperial_chat');
  if (saved) chat.innerHTML = saved;
  chat.scrollTop = chat.scrollHeight;
}

async function send() {
  const text = promptEl.value.trim();
  if (!text) return;
  promptEl.value = '';
  addMsg(text, 'user');
  saveChat();

  const thinking = addMsg('Thinking', 'agent thinking');
  sendBtn.disabled = true;
  statusEl.textContent = 'working…';
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
      addMsg('⚠ ' + data.error, 'agent error');
    } else {
      addMsg(data.response, 'agent', `⏱ ${secs}s · 🔧 ${data.tools_used} tool${data.tools_used===1?'':'s'}`);
    }
  } catch (e) {
    thinking.remove();
    addMsg('⚠ Network error: ' + e.message, 'agent error');
  } finally {
    sendBtn.disabled = false;
    statusEl.textContent = 'ready';
    saveChat();
  }
}

promptEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

restoreChat();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    if not os.path.exists(AGENT_PY):
        return jsonify({"error": f"Agent venv not found: {AGENT_PY}"}), 500
    if not os.path.exists(MAIN_PY):
        return jsonify({"error": f"Agent script not found: {MAIN_PY}"}), 500

    try:
        result = subprocess.run(
            [AGENT_PY, MAIN_PY, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=AGENT_DIR,
        )
        output = (result.stdout or "").strip()
        if result.returncode != 0 and not output:
            err = (result.stderr or "").strip()
            return jsonify({"error": err[:500] or f"exit {result.returncode}"}), 500
        return jsonify({"response": output or "(no output)", "tools_used": 0})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Agent timed out after 180s"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("👑 Imperial Agent Chat running on http://0.0.0.0:8098")
    app.run(host="0.0.0.0", port=8098, threaded=True)
