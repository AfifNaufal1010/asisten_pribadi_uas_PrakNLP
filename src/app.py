"""
app.py — Web UI untuk ARIA
Flask server yang menyajikan antarmuka chat berbasis web.
Jalankan: python src/app.py
Buka: http://localhost:5000
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

load_dotenv()

# Import komponen asisten (pastikan asisten.py ada di folder yang sama)
import sys
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)

# ─── Lazy-load asisten agar Flask start dulu ──────────────────────
_asisten = None

def get_asisten():
    global _asisten
    if _asisten is None:
        from asisten import AsistenPribadi
        _asisten = AsistenPribadi()
    return _asisten


# ─── HTML Template ────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARIA — Asisten Pribadi Bahasa Indonesia</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0D1117;
    --surface:  #161B22;
    --border:   #21262D;
    --accent:   #2F81F7;
    --accent2:  #A855F7;
    --green:    #3FB950;
    --text:     #E6EDF3;
    --muted:    #7D8590;
    --user-bg:  #1C2333;
    --ai-bg:    #161B22;
    --radius:   14px;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    flex-shrink: 0;
  }
  .logo {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 16px; color: white;
    flex-shrink: 0;
  }
  .header-info h1 { font-size: 15px; font-weight: 600; }
  .header-info p  { font-size: 12px; color: var(--muted); margin-top: 1px; }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 6px var(--green);
    margin-left: auto;
    flex-shrink: 0;
  }
  .status-label { font-size: 12px; color: var(--green); }

  /* ── Badges ── */
  .badges {
    display: flex; gap: 8px; margin-left: 10px;
  }
  .badge {
    font-size: 10px; font-weight: 600; padding: 3px 8px;
    border-radius: 20px; letter-spacing: 0.5px;
  }
  .badge-lc  { background: #1a3a6e; color: #79C0FF; border: 1px solid #1e4a8a; }
  .badge-lg  { background: #2d1a5e; color: #C084FC; border: 1px solid #3d1a7e; }
  .badge-ls  { background: #0f3d2a; color: #3FB950; border: 1px solid #1a5c3a; }

  /* ── Body layout ── */
  .body-wrap {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* ── Sidebar ── */
  .sidebar {
    width: 220px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-shrink: 0;
    overflow-y: auto;
  }
  .sidebar-title {
    font-size: 10px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: 1px;
    padding: 4px 8px 8px;
  }
  .tool-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 10px; border-radius: 8px;
    font-size: 13px; color: var(--muted);
    cursor: default; transition: background .15s;
  }
  .tool-item:hover { background: var(--border); color: var(--text); }
  .tool-icon {
    width: 28px; height: 28px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0;
  }
  .tool-icon.calc  { background: #1a3a6e; }
  .tool-icon.time  { background: #0f3d2a; }
  .tool-icon.note  { background: #3d2010; }
  .tool-icon.info  { background: #2d1a5e; }
  .tool-item.active { background: var(--border); color: var(--text); }

  .sidebar-divider {
    height: 1px; background: var(--border); margin: 8px 0;
  }
  .tip-box {
    background: #161f2c; border: 1px solid #1e3050;
    border-radius: 8px; padding: 10px 12px;
    font-size: 11.5px; color: var(--muted); line-height: 1.6;
    margin-top: auto;
  }
  .tip-box strong { color: var(--accent); }

  /* ── Chat area ── */
  .chat-wrap {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  #chat-box {
    flex: 1;
    overflow-y: auto;
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    scroll-behavior: smooth;
  }
  #chat-box::-webkit-scrollbar { width: 5px; }
  #chat-box::-webkit-scrollbar-track { background: transparent; }
  #chat-box::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

  /* ── Messages ── */
  .msg-row {
    display: flex;
    gap: 12px;
    max-width: 780px;
    width: 100%;
    animation: fadeUp .25s ease;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .msg-row.user { flex-direction: row-reverse; margin-left: auto; }
  .msg-row.ai   { margin-right: auto; }

  .avatar {
    width: 34px; height: 34px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; align-self: flex-end;
  }
  .avatar.ai   { background: linear-gradient(135deg, var(--accent), var(--accent2)); font-weight: 700; font-size: 13px; color: white; }
  .avatar.user { background: var(--user-bg); border: 1px solid var(--border); }

  .bubble {
    padding: 12px 16px;
    border-radius: var(--radius);
    font-size: 14px;
    line-height: 1.65;
    max-width: 100%;
    word-break: break-word;
  }
  .msg-row.user .bubble {
    background: var(--accent);
    color: white;
    border-bottom-right-radius: 4px;
  }
  .msg-row.ai .bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-bottom-left-radius: 4px;
  }

  .msg-meta {
    font-size: 10.5px; color: var(--muted);
    margin-top: 5px; padding: 0 4px;
  }
  .msg-row.user .msg-meta { text-align: right; }

  /* typing indicator */
  .typing .bubble {
    display: flex; align-items: center; gap: 6px;
    padding: 14px 18px;
  }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: blink 1.2s infinite; }
  .dot:nth-child(2) { animation-delay: .2s; }
  .dot:nth-child(3) { animation-delay: .4s; }
  @keyframes blink { 0%,80%,100% { opacity:.3; transform:scale(.8); } 40% { opacity:1; transform:scale(1); } }

  /* ── Input area ── */
  .input-area {
    border-top: 1px solid var(--border);
    padding: 14px 20px 18px;
    background: var(--bg);
    flex-shrink: 0;
  }
  .input-row {
    display: flex; gap: 10px; align-items: flex-end;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 14px;
    transition: border-color .2s;
  }
  .input-row:focus-within { border-color: var(--accent); }
  #user-input {
    flex: 1; background: none; border: none; outline: none;
    color: var(--text); font-family: 'Inter', sans-serif;
    font-size: 14px; resize: none; max-height: 120px;
    line-height: 1.5;
  }
  #user-input::placeholder { color: var(--muted); }
  #send-btn {
    width: 36px; height: 36px; border-radius: 9px;
    background: var(--accent); border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background .15s, transform .1s;
  }
  #send-btn:hover { background: #388bfd; }
  #send-btn:active { transform: scale(.93); }
  #send-btn svg { width: 16px; height: 16px; fill: white; }
  #send-btn:disabled { background: var(--border); cursor: not-allowed; }

  .quick-cmds {
    display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;
  }
  .qcmd {
    font-size: 11.5px; color: var(--muted);
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px; cursor: pointer;
    transition: all .15s;
  }
  .qcmd:hover { border-color: var(--accent); color: var(--accent); }

  /* ── Welcome ── */
  .welcome {
    text-align: center; margin: auto;
    padding: 40px 20px;
  }
  .welcome .big-logo {
    width: 72px; height: 72px; border-radius: 20px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; font-weight: 800; color: white;
    margin: 0 auto 20px;
    box-shadow: 0 8px 32px rgba(47,129,247,.3);
  }
  .welcome h2 { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
  .welcome p  { font-size: 14px; color: var(--muted); max-width: 380px; margin: 0 auto; line-height: 1.7; }
  .feature-pills {
    display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;
    margin-top: 20px;
  }
  .fpill {
    font-size: 12px; padding: 6px 14px; border-radius: 20px;
    background: var(--surface); border: 1px solid var(--border);
    color: var(--muted);
  }
</style>
</head>
<body>

<header>
  <div class="logo">AR</div>
  <div class="header-info">
    <h1>ARIA — Asisten Pribadi Bahasa Indonesia</h1>
    <p>Ditenagai LangChain · LangGraph · LangSmith · Groq (Llama 3.3)</p>
  </div>
  <div class="badges">
    <span class="badge badge-lc">LangChain</span>
    <span class="badge badge-lg">LangGraph</span>
    <span class="badge badge-ls">LangSmith</span>
  </div>
  <div style="margin-left:16px; display:flex; align-items:center; gap:6px;">
    <div class="status-dot"></div>
    <span class="status-label">Online</span>
  </div>
</header>

<div class="body-wrap">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-title">Tools Tersedia</div>

    <div class="tool-item" onclick="setInput('Hitung 125 dikali 8')">
      <div class="tool-icon calc">🔢</div>
      Kalkulator
    </div>
    <div class="tool-item" onclick="setInput('Sekarang jam berapa?')">
      <div class="tool-icon time">🕐</div>
      Waktu & Tanggal
    </div>
    <div class="tool-item" onclick="setInput('Ingatkan aku rapat jam 3 sore')">
      <div class="tool-icon note">📌</div>
      Pengingat
    </div>
    <div class="tool-item" onclick="setInput('Apa itu machine learning?')">
      <div class="tool-icon info">🔍</div>
      Informasi
    </div>

    <div class="sidebar-divider"></div>
    <div class="sidebar-title">Alur LangGraph</div>
    <div style="font-size:11.5px; color:var(--muted); padding:4px 8px; line-height:2;">
      START<br>
      └─ klasifikasi<br>
      &nbsp;&nbsp;&nbsp;├─ tool node<br>
      &nbsp;&nbsp;&nbsp;├─ percakapan<br>
      &nbsp;&nbsp;&nbsp;└─ selesai<br>
      END
    </div>

    <div class="tip-box" style="margin-top:12px;">
      <strong>Tips:</strong> Klik contoh di atas atau ketik perintah langsung dalam Bahasa Indonesia.
    </div>
  </aside>

  <!-- Chat -->
  <div class="chat-wrap">
    <div id="chat-box">
      <div class="welcome" id="welcome-screen">
        <div class="big-logo">AR</div>
        <h2>Halo! Saya ARIA</h2>
        <p>Asisten pribadi cerdas berbahasa Indonesia. Tanya apa saja — saya siap membantu!</p>
        <div class="feature-pills">
          <span class="fpill">Kalkulator</span>
          <span class="fpill">Info Waktu</span>
          <span class="fpill">Pengingat</span>
          <span class="fpill">Informasi Umum</span>
          <span class="fpill">Percakapan Bebas</span>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-row">
        <textarea id="user-input" rows="1" placeholder="Ketik perintah dalam Bahasa Indonesia..." onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
        <button id="send-btn" onclick="sendMessage()" title="Kirim">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </button>
      </div>
      <div class="quick-cmds">
        <span class="qcmd" onclick="setInput('Halo, perkenalkan dirimu!')">👋 Perkenalan</span>
        <span class="qcmd" onclick="setInput('Berapa 256 dibagi 16?')">🔢 Hitung</span>
        <span class="qcmd" onclick="setInput('Sekarang jam berapa?')">🕐 Jam sekarang</span>
        <span class="qcmd" onclick="setInput('Tampilkan semua pengingat saya')">📋 Pengingat</span>
        <span class="qcmd" onclick="setInput('Apa itu NLP?')">🔍 Tanya info</span>
      </div>
    </div>
  </div>
</div>

<script>
  const chatBox   = document.getElementById('chat-box');
  const input     = document.getElementById('user-input');
  const sendBtn   = document.getElementById('send-btn');
  let   firstMsg  = true;

  function timeNow() {
    return new Date().toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'});
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  function setInput(text) {
    input.value = text;
    input.focus();
    autoResize(input);
  }

  function appendMsg(role, text) {
    if (firstMsg) {
      document.getElementById('welcome-screen').remove();
      firstMsg = false;
    }
    const row = document.createElement('div');
    row.className = `msg-row ${role}`;

    const av = document.createElement('div');
    av.className = `avatar ${role}`;
    av.textContent = role === 'ai' ? 'AR' : '👤';

    const inner = document.createElement('div');
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    meta.textContent = timeNow();

    inner.appendChild(bubble);
    inner.appendChild(meta);
    row.appendChild(av);
    row.appendChild(inner);
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;
    return row;
  }

  function showTyping() {
    if (firstMsg) {
      document.getElementById('welcome-screen').remove();
      firstMsg = false;
    }
    const row = document.createElement('div');
    row.className = 'msg-row ai typing';
    row.id = 'typing-indicator';
    const av = document.createElement('div');
    av.className = 'avatar ai'; av.textContent = 'AR';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    row.appendChild(av); row.appendChild(bubble);
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function removeTyping() {
    const t = document.getElementById('typing-indicator');
    if (t) t.remove();
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    appendMsg('user', text);
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    showTyping();

    try {
      const res  = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({perintah: text})
      });
      const data = await res.json();
      removeTyping();
      appendMsg('ai', data.respons || 'Maaf, tidak ada respons.');
    } catch (err) {
      removeTyping();
      appendMsg('ai', 'Maaf, terjadi kesalahan koneksi. Pastikan server berjalan dengan benar.');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():
    data     = request.get_json()
    perintah = data.get("perintah", "").strip()
    if not perintah:
        return jsonify({"respons": "Perintah tidak boleh kosong."})
    try:
        asisten  = get_asisten()
        respons  = asisten.proses_perintah(perintah)
        return jsonify({"respons": respons})
    except Exception as e:
        return jsonify({"respons": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  ARIA Web UI — Asisten Pribadi Bahasa Indonesia")
    print("=" * 55)
    print("  Buka browser dan akses: http://localhost:5000")
    print("  Tekan Ctrl+C untuk menghentikan server")
    print("=" * 55)
    app.run(debug=False, host="0.0.0.0", port=5000)
