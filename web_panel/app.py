import socket
import os
import re
from flask import Flask, request, render_template_string, send_file, abort

app = Flask(__name__)

# ── AYARLAR ─────────────────────────────────────────────────────────────────
MANAGER_HOST = "host.docker.internal"
MANAGER_PORT = 444

# ── GÜVENLİK AYARLARI (Saldırı Bazlı) ──────────────────────────────────────
SQL_INJECTION_ENABLED = os.environ.get("SQL_INJECTION_ENABLED", "true").lower() == "true"
WEBPANEL_LOCK_ENABLED = os.environ.get("WEBPANEL_LOCK_ENABLED", "true").lower() == "true"
RANSOMWARE_ENABLED    = os.environ.get("RANSOMWARE_ENABLED",    "true").lower() == "true"

print(f"[WEB_PANEL] SQL Injection    : {'VULNERABLE' if SQL_INJECTION_ENABLED else 'SECURE'}")
print(f"[WEB_PANEL] Web Panel Lock   : {'VULNERABLE' if WEBPANEL_LOCK_ENABLED else 'SECURE'}")
print(f"[WEB_PANEL] Ransomware       : {'VULNERABLE' if RANSOMWARE_ENABLED else 'SECURE'}")

ATTACK_DEFS = [
    {"id": 1,  "name": "SQL Injection",              "short": "Web ihlali",          "category": "Web", "env": "SQL_INJECTION_ENABLED",   "service": "web_panel"},
    {"id": 2,  "name": "Web Panel Lockdown",         "short": "Araç kilitleme",      "category": "Web", "env": "WEBPANEL_LOCK_ENABLED",   "service": "web_panel"},
    {"id": 3,  "name": "SSH Brute Force & Ransomware","short": "Fidye yazılımı",      "category": "SSH", "env": "SSH_ENABLED",             "service": "vehicle_controller"},
    {"id": 5,  "name": "IoT Sensör Zehirleme",       "short": "Kavşak kilitleme",    "category": "IoT", "env": "IOT_SENSOR_ENABLED",      "service": "traffic_manager"},
    {"id": 6,  "name": "IDS Yanlış Alarm",           "short": "Sahte kaza alarmı",   "category": "IDS", "env": "IDS_FALSE_ALARM_ENABLED", "service": "traffic_manager"},
    {"id": 7,  "name": "Işık Zamanlama Sabotajı",    "short": "Disko modu",          "category": "IDS", "env": "IDS_TIMING_ENABLED",      "service": "traffic_manager"},
    {"id": 4,  "name": "Speed Spoofing",             "short": "Araç hız kontrolü",   "category": "V2X", "env": "SPEED_SPOOF_ENABLED",     "service": "control_socket"},
    {"id": 8,  "name": "Fake Vehicle",               "short": "Hayalet araç duvarı", "category": "V2X", "env": "FAKE_VEHICLE_ENABLED",    "service": "traffic_manager"},
    {"id": 9,  "name": "V2V Yanlış Bilgi Yayılımı",  "short": "Şok dalgası",         "category": "V2X", "env": "V2V_ENABLED",             "service": "traffic_manager"},
    {"id": 10, "name": "V2I Altyapı Zehirlenmesi",   "short": "İçeriden zehirleme",  "category": "V2X", "env": "V2I_ENABLED",             "service": "traffic_manager"},
]

def _bool_text(value):
    return str(value).strip().strip('"').strip("'").lower() == "true"

def compose_flags():
    """docker-compose.yaml icinden tum merkezi zafiyet bayraklarini okur."""
    flags = {}
    for path in ("/config/docker-compose.yaml", "../docker-compose.yaml", "docker-compose.yaml"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            for key, value in re.findall(r"^\s*([A-Z0-9_]+):\s*([\"']?[^\"'\n#]+[\"']?)", content, re.M):
                if key.endswith("_ENABLED") or key in ("SSH_ENABLED", "V2V_ENABLED", "V2I_ENABLED"):
                    flags[key] = _bool_text(value)
            if flags:
                return flags
        except Exception:
            continue
    return flags

def attack_matrix():
    flags = compose_flags()
    rows = []
    for menu_no, item in enumerate(ATTACK_DEFS, start=1):
        enabled = flags.get(item["env"], _bool_text(os.environ.get(item["env"], "false")))
        rows.append({**item, "display_id": menu_no, "enabled": enabled, "status": "VULNERABLE" if enabled else "SECURE"})
    return rows

def attack_counts():
    rows = attack_matrix()
    vulnerable = sum(1 for row in rows if row["enabled"])
    secure = len(rows) - vulnerable
    return {"total": len(rows), "vulnerable": vulnerable, "secure": secure}

# ── CSS ──────────────────────────────────────────────────────────────────────
COMMON_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap');

    *, *::before, *::after { box-sizing: border-box; }

    body {
        background-color: #050505;
        background-image:
            radial-gradient(circle at 18% 12%, rgba(0,255,65,.13) 0%, transparent 28%),
            radial-gradient(circle at 82% 18%, rgba(0,180,255,.10) 0%, transparent 24%),
            radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
        margin: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
        overflow-x: hidden;
        position: relative;
    }
    body::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image:
            linear-gradient(rgba(0,255,65,.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,255,65,.05) 1px, transparent 1px);
        background-size: 48px 48px;
        mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), rgba(0,0,0,.12));
        opacity: .45;
        z-index: 0;
    }
    body::after {
        content: "";
        position: fixed;
        width: 420px;
        height: 420px;
        right: -180px;
        top: 120px;
        pointer-events: none;
        background: radial-gradient(circle, rgba(0,255,65,.13), transparent 68%);
        opacity: .55;
        z-index: 0;
    }
    @keyframes gridDrift {
        from { transform: translateY(0); }
        to { transform: translateY(48px); }
    }
    @keyframes glowFloat {
        from { transform: translate3d(0,0,0) scale(1); opacity: .65; }
        to { transform: translate3d(-80px,70px,0) scale(1.15); opacity: .95; }
    }

    .scanline {
        display: none;
    }
    @keyframes scanline {
        0%   { bottom: 100%; }
        100% { bottom: -100%; }
    }

    h1, h2, h3 {
        font-family: 'Share Tech Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .container {
        width: 96%;
        max-width: 1640px;
        margin-top: 34px;
        z-index: 2;
    }

    .card {
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(145deg, rgba(24,28,26,.94), rgba(8,10,9,.93)),
            rgba(20,20,20,0.85);
        border: 1px solid rgba(108, 255, 146, .16);
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 18px 54px rgba(0,0,0,0.48), inset 0 1px 0 rgba(255,255,255,.04);
        transition: transform 0.25s, border-color 0.25s, box-shadow .25s;
        display: flex;
        flex-direction: column;
    }
    .card::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(115deg, transparent, rgba(0,255,65,.07), transparent);
        transform: translateX(-110%);
        transition: transform .85s ease;
        pointer-events: none;
    }
    .card:hover {
        transform: translateY(-3px);
        border-color: rgba(0,255,65,.7);
        box-shadow: 0 22px 70px rgba(0,0,0,.56), 0 0 24px rgba(0,255,65,.13);
    }
    .card:hover::before { transform: translateX(110%); }
    @keyframes cardIn {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .card .card-body { flex: 1; }

    .grid-2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        align-items: stretch;
        margin-bottom: 20px;
    }
    .grid-full { margin-bottom: 20px; }

    .hero {
        display: grid;
        grid-template-columns: 1.45fr 0.8fr;
        gap: 20px;
        align-items: stretch;
        margin-bottom: 20px;
    }
    .presentation-layout {
        display: grid;
        grid-template-columns: minmax(0, 1.55fr) minmax(520px, 0.95fr);
        gap: 24px;
        align-items: start;
    }
    .left-stack, .right-stack {
        display: grid;
        gap: 20px;
    }
    .hero-title {
        color: #f3f7f5;
        font-size: 34px;
        line-height: 1.05;
        margin: 0 0 14px 0;
        text-shadow: 0 0 16px rgba(0,255,65,.25);
    }
    .hero-subtitle {
        color: #9aa5a0;
        font-size: 16px;
        line-height: 1.55;
        margin: 0;
        max-width: 760px;
    }
    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 20px;
    }
    .metric {
        background: linear-gradient(180deg, rgba(0,255,65,.08), rgba(8,13,10,.92));
        border: 1px solid rgba(0,255,65,.22);
        border-radius: 6px;
        padding: 14px;
        box-shadow: inset 0 0 20px rgba(0,255,65,.04);
    }
    .metric-value {
        display: block;
        font-family: 'Share Tech Mono', monospace;
        font-size: 28px;
        color: #00ff41;
    }
    .metric-label {
        color: #78837e;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .attack-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(150px, 1fr));
        gap: 14px;
    }
    .attack-tile {
        background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(11,13,12,.96));
        border: 1px solid #242b27;
        border-radius: 6px;
        padding: 16px;
        min-height: 142px;
        transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
    }
    .attack-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0,0,0,.35);
    }
    .attack-tile.vulnerable {
        border-color: rgba(255, 68, 68, .75);
        background: linear-gradient(180deg, rgba(110, 0, 0, .32), #0b0d0c);
        box-shadow: inset 0 0 18px rgba(255,0,0,.06);
    }
    .attack-tile.secure {
        border-color: rgba(0, 255, 65, .45);
        background: linear-gradient(180deg, rgba(0, 60, 20, .18), #0b0d0c);
    }
    @keyframes dangerPulse {
        0%, 100% { box-shadow: inset 0 0 0 rgba(255,0,0,0); }
        50% { box-shadow: inset 0 0 22px rgba(255,0,0,.08); }
    }
    .attack-index {
        font-family: 'Share Tech Mono', monospace;
        color: #6f7a75;
        font-size: 11px;
    }
    .attack-name {
        color: #f0f4f2;
        font-weight: 700;
        font-size: 15px;
        line-height: 1.15;
        margin: 10px 0 8px 0;
        min-height: 38px;
    }
    .attack-meta {
        color: #87918c;
        font-size: 12px;
        line-height: 1.25;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        padding: 4px 7px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 10px;
        margin-top: 8px;
    }
    .badge.vulnerable { color: #ff5959; border: 1px solid #ff3333; background: rgba(255,0,0,.08); }
    .badge.secure { color: #00ff41; border: 1px solid #00aa3a; background: rgba(0,255,65,.08); }
    .flow {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
    }
    .flow-step {
        background: #0c0f0d;
        border: 1px solid #27332b;
        border-radius: 6px;
        padding: 13px;
        color: #9aa5a0;
        font-size: 13px;
        line-height: 1.35;
    }
    .flow-step b {
        display: block;
        color: #00ff41;
        font-family: 'Share Tech Mono', monospace;
        margin-bottom: 6px;
    }
    .login-panel {
        background: rgba(10,12,11,.96);
        border: 1px solid #2d372f;
        border-radius: 8px;
        padding: 22px;
    }
    .mini-link {
        color: #00ff41;
        font-family: 'Share Tech Mono', monospace;
        font-size: 12px;
        text-decoration: none;
    }
    .live-terminal {
        background: #020403;
        border: 1px solid #1d2b22;
        border-left: 4px solid #00ff41;
        border-radius: 6px;
        padding: 14px;
        height: 640px;
        overflow: auto;
        color: #9fffb8;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.35;
        white-space: pre-wrap;
        box-shadow: inset 0 0 36px rgba(0,255,65,.08);
    }
    .terminal-card {
        cursor: zoom-in;
    }
    .terminal-card.expanded {
        position: fixed;
        inset: 28px;
        z-index: 80;
        cursor: zoom-out;
        animation: terminalExpand .18s ease both;
    }
    .terminal-card.expanded .live-terminal {
        height: calc(100vh - 145px);
        font-size: 13px;
    }
    .terminal-card.expanded::after {
        content: "Kapatmak için tekrar tıklayın";
        position: absolute;
        right: 24px;
        bottom: 14px;
        color: #6dff96;
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
        opacity: .75;
    }
    @keyframes terminalExpand {
        from { transform: scale(.985); opacity: .92; }
        to { transform: scale(1); opacity: 1; }
    }
    body.terminal-expanded .left-stack,
    body.terminal-expanded .site-footer,
    body.terminal-expanded .topbar,
    body.terminal-expanded .right-stack > .card:not(.expanded) {
        filter: blur(2px);
        opacity: .26;
    }
    .terminal-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }
    .terminal-pill {
        border: 1px solid #285c37;
        color: #00ff41;
        border-radius: 4px;
        padding: 4px 8px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
    }
    .report-list {
        display: grid;
        gap: 8px;
    }
    .report-item {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 10px;
        align-items: center;
        background: #0b0d0c;
        border: 1px solid #242b27;
        border-radius: 6px;
        padding: 10px;
    }
    .report-name {
        color: #f0f4f2;
        font-size: 12px;
        line-height: 1.25;
        word-break: break-word;
    }
    .report-meta {
        color: #77817c;
        font-size: 11px;
        margin-top: 3px;
    }
    .report-actions {
        display: flex;
        gap: 6px;
    }
    .small-btn {
        border: 1px solid #285c37;
        color: #00ff41;
        background: rgba(0,255,65,.06);
        border-radius: 4px;
        padding: 6px 8px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 10px;
        text-decoration: none;
    }
    .top-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        align-items: center;
        margin-top: 6px;
    }
    .site-footer {
        width: 96%;
        max-width: 1640px;
        margin: 28px auto 22px auto;
        border-top: 1px solid #26302b;
        padding: 18px 0 0 0;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 20px;
        color: #7f8a84;
    }
    .footer-logo-slot {
        width: 170px;
        min-height: 54px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }
    .footer-logo-slot img {
        max-width: 170px;
        max-height: 58px;
        object-fit: contain;
        filter: drop-shadow(0 0 12px rgba(0,255,65,.22));
    }
    .footer-name {
        color: #f3f7f5;
        font-family: 'Share Tech Mono', monospace;
        font-size: 15px;
        letter-spacing: 2px;
        text-align: center;
        text-transform: uppercase;
    }
    .footer-brand {
        justify-self: end;
        color: #00ff41;
        font-family: 'Share Tech Mono', monospace;
        font-size: 20px;
        letter-spacing: 5px;
        text-shadow: 0 0 12px rgba(0,255,65,.45);
    }
    @media (max-width: 980px) {
        .hero { grid-template-columns: 1fr; }
        .presentation-layout { grid-template-columns: 1fr; }
        .attack-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .flow { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 640px) {
        .metric-row, .flow { grid-template-columns: 1fr; }
        .attack-grid { grid-template-columns: 1fr; }
        .hero-title { font-size: 26px; }
        .site-footer { grid-template-columns: 1fr; text-align: center; }
        .footer-logo-slot, .footer-brand { justify-self: center; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation: none !important;
            transition: none !important;
            scroll-behavior: auto !important;
        }
    }

    input[type="text"], input[type="password"] {
        background: #111;
        border: 1px solid #444;
        color: #00ff41;
        padding: 12px;
        width: 100%;
        margin-bottom: 15px;
        border-radius: 4px;
        font-family: 'Share Tech Mono', monospace;
    }
    input:focus { outline: none; border-color: #00ff41; box-shadow: 0 0 8px rgba(0,255,65,0.3); }

    .btn {
        width: 100%;
        padding: 15px;
        border: none;
        border-radius: 4px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 16px;
        cursor: pointer;
        text-transform: uppercase;
        font-weight: bold;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-top: 12px;
    }
    .btn-login      { background: #00ff41; color: #000; }
    .btn-login:hover { background: #00cc33; box-shadow: 0 0 15px #00ff41; }
    .btn-hack       { background: linear-gradient(45deg,#cc0000,#990000); color:#fff; border:1px solid #ff0000; }
    .btn-hack:hover { background: linear-gradient(45deg,#ff0000,#cc0000); box-shadow:0 0 20px rgba(255,0,0,.6); }
    .btn-lock       { background: linear-gradient(45deg,#ff9900,#cc7a00); color:#000; border:1px solid #ffcc00; }
    .btn-lock:hover { background: linear-gradient(45deg,#ffcc00,#ff9900); box-shadow:0 0 20px rgba(255,153,0,.6); }
    .btn-ransomware { background: linear-gradient(45deg,#8b00ff,#5500aa); color:#fff; border:1px solid #cc00ff; }
    .btn-ransomware:hover { background: linear-gradient(45deg,#cc00ff,#8b00ff); box-shadow:0 0 20px rgba(139,0,255,.7); }
    .btn-disabled   { background: #222; color: #555; border: 1px solid #333; cursor: not-allowed; }

    .status-dot {
        height: 12px; width: 12px;
        background-color: #00ff41;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #00ff41;
        margin-right: 8px;
    }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }

    .console-box {
        background-color: #000;
        border: 1px solid #333;
        border-left: 4px solid #00ff41;
        color: #00ff41;
        font-family: 'Courier New', monospace;
        padding: 15px;
        margin-top: 10px;
        font-size: 14px;
        min-height: 60px;
        border-radius: 4px;
        margin-bottom: 40px;
    }

    .info-box {
        background: #111;
        padding: 10px 14px;
        margin: 14px 0;
        border-radius: 4px;
        font-size: 12px;
        line-height: 1.8;
        font-family: 'Share Tech Mono', monospace;
    }

    .secure-banner {
        background: linear-gradient(45deg,#003300,#004400);
        border: 2px solid #00ff41; color: #00ff41;
        padding: 10px 20px; border-radius: 4px;
        font-family: 'Share Tech Mono', monospace;
        text-align: center; margin-bottom: 12px; font-size: 13px;
    }
    .vulnerable-banner {
        background: linear-gradient(45deg,#330000,#440000);
        border: 2px solid #ff0000; color: #ff3333;
        padding: 10px 20px; border-radius: 4px;
        font-family: 'Share Tech Mono', monospace;
        text-align: center; margin-bottom: 12px; font-size: 13px;
    }
    .attack-blocked-banner {
        background: linear-gradient(45deg,#003300,#004400);
        border: 2px solid #00ff41; color: #00ff41;
        padding: 8px 16px; border-radius: 4px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 12px; margin-bottom: 8px;
    }

    .topbar {
        width: 100%;
        background: #0a0a0a;
        border-bottom: 1px solid #222;
        padding: 14px 0;
    }
    .topbar-inner {
        width: 96%; max-width: 1640px;
        margin: 0 auto;
        display: flex; justify-content: space-between; align-items: center;
    }
</style>
"""

# ── JÜRİ SUNUM / LOGIN SAYFASI ───────────────────────────────────────────────
LOGIN_PAGE = COMMON_STYLE + """
<html>
<head><title>PENTEZ-AI Sunum Paneli</title></head>
<body>
    <div class="scanline"></div>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <h2 style="margin:0; font-size:22px;">PENTEZ-AI JÜRİ SUNUM PANELİ</h2>
                <span style="color:#777; font-size:11px; font-family:monospace;">CENTRAL VULNERABILITY ORCHESTRATION // V2X TRAFFIC CYBER RANGE</span>
            </div>
            <div style="text-align:right;">
                <div style="color:#00ff41; font-weight:bold; font-family:monospace;">
                    <span class="status-dot"></span>DEMO HAZIR
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <div class="card">
                <h1 class="hero-title">Otonom Trafik Sistemleri İçin Yapay Zeka Destekli Sızma Testi</h1>
                <p class="hero-subtitle">
                    Bu panel, PENTEZ-AI mimarisindeki merkezi zafiyet açma/kapatma sistemini, canlı saldırı yüzeyini
                    ve SUMO tabanlı trafik etkisini jüri sunumu için tek ekranda özetler.
                </p>
                <div class="metric-row">
                    <div class="metric">
                        <span class="metric-value">{{ counts.total }}</span>
                        <span class="metric-label">Toplam Senaryo</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value" style="color:#ff4d4d;">{{ counts.vulnerable }}</span>
                        <span class="metric-label">Vulnerable</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{{ counts.secure }}</span>
                        <span class="metric-label">Secure</span>
                    </div>
                </div>
            </div>

            <div class="login-panel">
                {% if sql_blocked %}
                <div class="secure-banner">SQL INJECTION KORUMASI AKTİF</div>
                {% else %}
                <div class="vulnerable-banner">SQL INJECTION ZAFİYETİ AKTİF</div>
                {% endif %}
                <h3 style="color:#00ff41; margin-top:0;">Admin Giriş Noktası</h3>
                <form method="POST" action="/login">
                    <input type="text" name="username" placeholder="KULLANICI ADI">
                    <input type="password" name="password" placeholder="ŞİFRE">
                    <button type="submit" class="btn btn-login">PANELE GİR</button>
                </form>
                <div class="info-box">
                    Normal giriş: admin / admin123<br>
                    SQLi demo: ' OR '1'='1
                </div>
            </div>
        </div>

        <div class="grid-full">
            <div class="card">
                <h3 style="color:#00ff41; margin-top:0;">Merkezi Zafiyet Matrisi</h3>
                <div class="attack-grid">
                    {% for attack in attacks %}
                    <div class="attack-tile {{ 'vulnerable' if attack.enabled else 'secure' }}">
                        <div class="attack-index">#{{ "%02d"|format(attack.display_id) }} · {{ attack.category }}</div>
                        <div class="attack-name">{{ attack.name }}</div>
                        <div class="attack-meta">{{ attack.short }}<br>{{ attack.service }}</div>
                        <span class="badge {{ 'vulnerable' if attack.enabled else 'secure' }}">{{ attack.status }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="grid-full">
            <div class="card">
                <h3 style="color:#f3f7f5; margin-top:0;">Sunum Akışı</h3>
                <div class="flow">
                    <div class="flow-step"><b>1. Seç</b>zafiyet_menu.py ile 10 saldırı ayrı ayrı secure/vulnerable yapılır.</div>
                    <div class="flow-step"><b>2. Başlat</b>calistir.bat Docker, Web Panel ve SUMO ortamını ayağa kaldırır.</div>
                    <div class="flow-step"><b>3. Saldır</b>Pentest aracı recon yapar, açıkları seçtirir ve exploit çalıştırır.</div>
                    <div class="flow-step"><b>4. Raporla</b>Markdown/PDF raporunda etki, PoC, CVSS ve öneriler üretilir.</div>
                </div>
            </div>
        </div>

        <div class="grid-full">
            <div class="card">
                <div class="terminal-head">
                    <h3 style="color:#00ff41; margin:0;">Canlı Pentest Terminali</h3>
                    <span class="terminal-pill" id="live-status">BEKLENİYOR</span>
                </div>
                <div id="live-terminal" class="live-terminal">Pentest aracı çalıştırıldığında terminal çıktısı burada canlı görünecek.</div>
            </div>
        </div>

        <div class="card">
            <div class="console-box" style="margin:0;">
                root@pentez-ai:~$ calistir.bat → docker-compose → traffic_manager.py → attacker/main.py
            </div>
        </div>
    </div>
    <script>
        let lastLiveLogText = '';
        let lastLiveStatus = null;
        async function refreshLiveLog() {
            try {
                const response = await fetch('/live-log?tail=90', { cache: 'no-store' });
                const data = await response.json();
                const terminal = document.getElementById('live-terminal');
                const status = document.getElementById('live-status');
                const nextText = data.lines && data.lines.length ? data.lines.join('\\n') : terminal.textContent;
                if (nextText !== lastLiveLogText) {
                    const nearBottom = terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 90;
                    terminal.textContent = nextText;
                    lastLiveLogText = nextText;
                    if (nearBottom) terminal.scrollTop = terminal.scrollHeight;
                }
                if (data.active !== lastLiveStatus) {
                    status.textContent = data.active ? 'CANLI' : 'BEKLENİYOR';
                    status.style.color = data.active ? '#00ff41' : '#999';
                    lastLiveStatus = data.active;
                }
            } catch (err) {
                document.getElementById('live-status').textContent = 'BAĞLANTI YOK';
            }
        }
        refreshLiveLog();
        setInterval(refreshLiveLog, 1500);
    </script>
</body>
</html>
"""

# ── DASHBOARD SAYFASI ────────────────────────────────────────────────────────
PRESENTATION_PAGE = COMMON_STYLE + """
<html>
<head><title>PENTEZ-AI Sunum Paneli</title></head>
<body>
    <div class="scanline"></div>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <h2 style="margin:0; font-size:22px;">PENTEZ-AI JURI SUNUM PANELİ</h2>
                <span style="color:#777; font-size:11px; font-family:monospace;">CENTRAL VULNERABILITY ORCHESTRATION // V2X TRAFFIC CYBER RANGE</span>
            </div>
            <div style="text-align:right;">
                <div style="color:#00ff41; font-weight:bold; font-family:monospace;">
                    <span class="status-dot"></span>DEMO HAZIR
                </div>
                <div class="top-actions">
                    <a class="small-btn" href="/login-page">ADMIN GİRİŞ</a>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="presentation-layout">
            <div class="left-stack">
                <div class="card">
                    <h1 class="hero-title">Otonom Trafik Sistemleri İçin Yapay Zeka Destekli Sızma Testi</h1>
                    <p class="hero-subtitle">
                        PENTEZ-AI; merkezi zafiyet açma/kapatma, otonom pentest ajanları, SUMO trafik simülasyonu ve otomatik raporlamayı tek demo ortamında birleştirir.
                    </p>
                    <div class="metric-row">
                        <div class="metric"><span class="metric-value">{{ counts.total }}</span><span class="metric-label">Toplam Senaryo</span></div>
                        <div class="metric"><span class="metric-value" style="color:#ff4d4d;">{{ counts.vulnerable }}</span><span class="metric-label">Vulnerable</span></div>
                        <div class="metric"><span class="metric-value">{{ counts.secure }}</span><span class="metric-label">Secure</span></div>
                    </div>
                </div>

                <div class="card">
                    <h3 style="color:#00ff41; margin-top:0;">Merkezi Zafiyet Matrisi</h3>
                    <div class="attack-grid">
                        {% for attack in attacks %}
                        <div class="attack-tile {{ 'vulnerable' if attack.enabled else 'secure' }}">
                            <div class="attack-index">#{{ "%02d"|format(attack.display_id) }} · {{ attack.category }}</div>
                            <div class="attack-name">{{ attack.name }}</div>
                            <div class="attack-meta">{{ attack.short }}<br>{{ attack.service }}</div>
                            <span class="badge {{ 'vulnerable' if attack.enabled else 'secure' }}">{{ attack.status }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card">
                    <h3 style="color:#f3f7f5; margin-top:0;">Sunum Akışı</h3>
                    <div class="flow">
                        <div class="flow-step"><b>1. Seç</b>zafiyet_menu.py ile saldırılar ayrı ayrı secure/vulnerable yapılır.</div>
                        <div class="flow-step"><b>2. Başlat</b>calistir.bat Docker, Web Panel ve SUMO ortamını ayağa kaldırır.</div>
                        <div class="flow-step"><b>3. Saldır</b>Pentest aracı recon yapar, açıkları seçtirir ve exploit çalıştırır.</div>
                        <div class="flow-step"><b>4. Raporla</b>Markdown/PDF raporunda etki, PoC, CVSS ve öneriler üretilir.</div>
                    </div>
                </div>
            </div>

            <div class="right-stack">
                <div class="card terminal-card" id="terminal-card" title="Terminali büyütmek için tıklayın">
                    <div class="terminal-head">
                        <h3 style="color:#00ff41; margin:0;">Canlı Pentest Terminali</h3>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <span class="terminal-pill">BÜYÜT</span>
                            <span class="terminal-pill" id="live-status">BEKLENİYOR</span>
                        </div>
                    </div>
                    <div id="live-terminal" class="live-terminal">Pentest aracı çalıştırıldığında terminal çıktısı burada canlı görünecek.</div>
                </div>

                <div class="card">
                    <div class="terminal-head">
                        <h3 style="color:#f3f7f5; margin:0;">Rapor Merkezi</h3>
                        <span class="terminal-pill">{{ reports|length }} DOSYA</span>
                    </div>
                    <div class="report-list" id="report-list">
                        {% if reports %}
                            {% for report in reports %}
                            <div class="report-item">
                                <div>
                                    <div class="report-name">{{ report.name }}</div>
                                    <div class="report-meta">{{ report.modified }} · {{ report.size_kb }} KB</div>
                                </div>
                                <div class="report-actions">
                                    <a class="small-btn" href="/reports/{{ report.name }}" target="_blank">AÇ</a>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="info-box">Henüz rapor üretilmedi. Pentest sonunda rapor oluşturulduğunda burada görünecek.</div>
                        {% endif %}
                    </div>
                </div>

            </div>
        </div>
    </div>
    <footer class="site-footer">
        <div class="footer-logo-slot"><img src="/logo.png" alt="PENTEZ-AI logo"></div>
        <div class="footer-name">Ömer Faruk Baysal</div>
        <div class="footer-brand">PENTEZ-AI</div>
    </footer>
    <script>
        let lastLiveLogText = '';
        let lastLiveStatus = null;
        let lastReportsPayload = '';
        async function refreshLiveLog() {
            try {
                const response = await fetch('/live-log?tail=90', { cache: 'no-store' });
                const data = await response.json();
                const terminal = document.getElementById('live-terminal');
                const status = document.getElementById('live-status');
                const nextText = data.lines && data.lines.length ? data.lines.join('\\n') : terminal.textContent;
                if (nextText !== lastLiveLogText) {
                    const nearBottom = terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 90;
                    terminal.textContent = nextText;
                    lastLiveLogText = nextText;
                    if (nearBottom) terminal.scrollTop = terminal.scrollHeight;
                }
                if (data.active !== lastLiveStatus) {
                    status.textContent = data.active ? 'CANLI' : 'BEKLENİYOR';
                    status.style.color = data.active ? '#00ff41' : '#999';
                    lastLiveStatus = data.active;
                }
            } catch (err) {
                document.getElementById('live-status').textContent = 'BAĞLANTI YOK';
            }
        }
        async function refreshReports() {
            try {
                const response = await fetch('/reports', { cache: 'no-store' });
                const reports = await response.json();
                const list = document.getElementById('report-list');
                const visibleReports = reports.slice(0, 8);
                const nextPayload = JSON.stringify(visibleReports);
                if (nextPayload === lastReportsPayload) return;
                lastReportsPayload = nextPayload;
                if (!reports.length) {
                    list.innerHTML = '<div class="info-box">Henüz rapor üretilmedi. Pentest sonunda rapor oluşturulduğunda burada görünecek.</div>';
                    return;
                }
                list.innerHTML = visibleReports.map((report) => `
                    <div class="report-item">
                        <div>
                            <div class="report-name">${report.name}</div>
                            <div class="report-meta">${report.modified} · ${report.size_kb} KB</div>
                        </div>
                        <div class="report-actions">
                            <a class="small-btn" href="/reports/${report.name}" target="_blank">AÇ</a>
                        </div>
                    </div>
                `).join('');
            } catch (err) {}
        }
        refreshLiveLog();
        refreshReports();
        setInterval(refreshLiveLog, 1500);
        setInterval(refreshReports, 10000);
        const terminalCard = document.getElementById('terminal-card');
        terminalCard.addEventListener('click', () => {
            terminalCard.classList.toggle('expanded');
            document.body.classList.toggle('terminal-expanded', terminalCard.classList.contains('expanded'));
            const terminal = document.getElementById('live-terminal');
            setTimeout(() => { terminal.scrollTop = terminal.scrollHeight; }, 80);
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && terminalCard.classList.contains('expanded')) {
                terminalCard.classList.remove('expanded');
                document.body.classList.remove('terminal-expanded');
            }
        });
    </script>
</body>
</html>
"""

ADMIN_LOGIN_PAGE = COMMON_STYLE + """
<html>
<head><title>Admin Giriş</title></head>
<body>
    <div class="scanline"></div>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <h2 style="margin:0; font-size:22px;">ADMIN GİRİŞ NOKTASI</h2>
                <span style="color:#777; font-size:11px; font-family:monospace;">WEB PANEL AUTHENTICATION // SQLI DEMO</span>
            </div>
            <a class="small-btn" href="/">SUNUM PANELİNE DÖN</a>
        </div>
    </div>
    <div class="container" style="max-width:460px; margin-top:70px;">
        <div class="login-panel">
            {% if sql_blocked %}
            <div class="secure-banner">SQL INJECTION KORUMASI AKTİF</div>
            {% else %}
            <div class="vulnerable-banner">SQL INJECTION ZAFİYETİ AKTİF</div>
            {% endif %}
            <h3 style="color:#00ff41; margin-top:0;">Kimlik Doğrulama</h3>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="KULLANICI ADI">
                <input type="password" name="password" placeholder="ŞİFRE">
                <button type="submit" class="btn btn-login">PANELE GİR</button>
            </form>
            <div class="info-box">
                Normal giriş: admin / admin123<br>
                SQLi demo: ' OR '1'='1
            </div>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = COMMON_STYLE + """
<html>
<head><title>Komuta Kontrol Merkezi</title></head>
<body>
    <div class="scanline"></div>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <h2 style="margin:0; font-size:22px; text-shadow:0 0 10px rgba(0,255,65,.4);">
                    TRAFİK KONTROL MERKEZİ
                </h2>
                <span style="color:#555; font-size:11px; font-family:monospace;">C2 SERVER // ADMIN_ACCESS</span>
            </div>
            <div style="text-align:right;">
                <div style="color:#00ff41; font-weight:bold; font-family:monospace;">
                    <span class="status-dot"></span>BAĞLANTI AKTİF
                </div>
                <div style="color:#555; font-size:11px;">LATENCY: 12ms</div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="grid-2">

            <!-- HACK LIGHTS -->
            <div class="card">
                <h3 style="color:#ff3333; border-bottom:1px solid #2a2a2a; padding-bottom:10px; margin-top:0;">
                    ⚠️ KRİTİK ALTYAPI SALDIRISI
                </h3>
                <div class="card-body">
                    <p style="color:#999; font-size:14px; margin:0 0 6px;">
                        Hedef kavşaktaki tüm sinyalizasyon sistemini manipüle ederek kaotik durum oluşturur.
                    </p>
                    <div class="info-box" style="color:#ff3333;">
                        HEDEF: Center Junction<br>
                        ETKİ: Denial of Service (DoS)
                    </div>
                </div>
                <form method="POST" action="/send_command">
                    <input type="hidden" name="cmd" value="HACK_LIGHTS">
                    <button type="submit" class="btn btn-hack">🚨 TÜM IŞIKLARI YEŞİL YAP</button>
                </form>
            </div>

            <!-- WEB PANEL LOCKDOWN -->
            <div class="card">
                <h3 style="color:#ff9900; border-bottom:1px solid #2a2a2a; padding-bottom:10px; margin-top:0;">
                    🦠 ARAÇ KİLİTLEME
                </h3>
                <div class="card-body">
                    {% if not webpanel_lock_enabled %}
                    <div class="attack-blocked-banner">🛡️ SECURE: Araç kilitleme koruması aktif</div>
                    {% endif %}
                    <p style="color:#999; font-size:14px; margin:0 0 6px;">
                        Hedef aracın ECU sistemine sızarak frenleri kilitler ve aracı durdurur.
                    </p>
                    <div class="info-box" style="color:#ff9900;">
                        HEDEF: 34 TEZ 2026<br>
                        ETKİ: Trafik Akışını Durdurma
                    </div>
                </div>
                <form method="POST" action="/send_command">
                    <input type="hidden" name="cmd" value="HACK_VEHICLE">
                    {% if webpanel_lock_enabled %}
                    <button type="submit" class="btn btn-lock">🔒 ARACI KİLİTLE</button>
                    {% else %}
                    <button type="button" class="btn btn-disabled" disabled>🛡️ ENGELLENDI</button>
                    {% endif %}
                </form>
            </div>

        </div>

        <!-- RANSOMWARE -->
        <div class="grid-full">
            <div class="card">
                <h3 style="color:#cc00ff; border-bottom:1px solid #2a2a2a; padding-bottom:10px; margin-top:0;">
                    💀 RANSOMWARE SALDIRISI
                </h3>
                <div class="card-body">
                    {% if not ransomware_enabled %}
                    <div class="attack-blocked-banner">🛡️ SECURE: Ransomware koruması aktif</div>
                    {% endif %}
                    <p style="color:#999; font-size:14px; margin:0 0 6px;">
                        Trafik yönetim sürecini sonlandırır, kritik dosyaları kilitler ve sistemde fidye notu bırakır.
                    </p>
                    <div class="info-box" style="color:#cc00ff;">
                        HEDEF: traffic_manager.py (PID) &nbsp;|&nbsp;
                        ETKİ: Tüm Trafik Sistemi Çöküşü &nbsp;|&nbsp;
                        ZAFİYET: Kimlik Doğrulama Yok
                    </div>
                </div>
                <form method="POST" action="/send_command">
                    <input type="hidden" name="cmd" value="RANSOMWARE">
                    {% if ransomware_enabled %}
                    <button type="submit" class="btn btn-ransomware">💀 RANSOMWARE BAŞLAT</button>
                    {% else %}
                    <button type="button" class="btn btn-disabled" disabled>🛡️ ENGELLENDİ</button>
                    {% endif %}
                </form>
            </div>
        </div>

        <!-- ARAÇ YÖNETİM LİNKİ -->
        <div class="grid-full">
            <div class="card" style="border-color:#ff9900;">
                <h3 style="color:#ff9900; margin:0 0 10px 0;">🚗 ARAÇ YÖNETİM SİSTEMİ</h3>
                <p style="color:#999; font-size:13px; margin:0 0 10px 0;">
                    Bağlı araçları görüntüle ve uzaktan kontrol et.
                </p>
                <a href="/vehicles" style="text-decoration:none;">
                    <button class="btn btn-lock" style="margin-top:0;">🔗 ARAÇ PANELİNE GİT</button>
                </a>
            </div>
        </div>

        <div class="grid-full">
            <div class="card">
                <div class="terminal-head">
                    <h3 style="color:#00ff41; margin:0;">Canlı Pentest Terminali</h3>
                    <span class="terminal-pill" id="live-status">BEKLENİYOR</span>
                </div>
                <div id="live-terminal" class="live-terminal">Pentest aracı çalıştırıldığında terminal çıktısı burada canlı görünecek.</div>
            </div>
        </div>

        <div class="console-box">
            <span style="color:#444;">root@admin-panel:~$</span>
            <span> {{ message }}</span>
            <span style="margin-left:4px; opacity:.7;">▌</span>
        </div>
    </div>
    <script>
        let lastLiveLogText = '';
        let lastLiveStatus = null;
        async function refreshLiveLog() {
            try {
                const response = await fetch('/live-log?tail=90', { cache: 'no-store' });
                const data = await response.json();
                const terminal = document.getElementById('live-terminal');
                const status = document.getElementById('live-status');
                const nextText = data.lines && data.lines.length ? data.lines.join('\\n') : terminal.textContent;
                if (nextText !== lastLiveLogText) {
                    const nearBottom = terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 90;
                    terminal.textContent = nextText;
                    lastLiveLogText = nextText;
                    if (nearBottom) terminal.scrollTop = terminal.scrollHeight;
                }
                if (data.active !== lastLiveStatus) {
                    status.textContent = data.active ? 'CANLI' : 'BEKLENİYOR';
                    status.style.color = data.active ? '#00ff41' : '#999';
                    lastLiveStatus = data.active;
                }
            } catch (err) {
                document.getElementById('live-status').textContent = 'BAĞLANTI YOK';
            }
        }
        refreshLiveLog();
        setInterval(refreshLiveLog, 1500);
    </script>
</body>
</html>
"""

# ── ARAÇ YÖNETİM SAYFASI ────────────────────────────────────────────────────
VEHICLES_PAGE = COMMON_STYLE + """
<html>
<head><title>Araç Yönetim Paneli</title></head>
<body>
    <div class="scanline"></div>
    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <h2 style="margin:0; font-size:22px;">ARAÇ YÖNETİM SİSTEMİ</h2>
                <span style="color:#555; font-size:11px; font-family:monospace;">VEHICLE MANAGEMENT // ADMIN_ACCESS</span>
            </div>
            <div style="text-align:right;">
                <div style="color:#00ff41; font-weight:bold; font-family:monospace;">
                    <span class="status-dot"></span>SİSTEM AKTİF
                </div>
                <a href="/" style="color:#555; font-size:11px; font-family:monospace;">← ANA PANEL</a>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="grid-full">
            <div class="card">
                <h3 style="color:#ff9900; border-bottom:1px solid #2a2a2a; padding-bottom:10px; margin-top:0;">
                    🚗 ARAÇ KONTROL PANELİ — hedef_arac (34 TEZ 2026)
                </h3>
                <div class="card-body">
                    {% if not webpanel_lock_enabled %}
                    <div class="attack-blocked-banner">🛡️ SECURE: Araç kilitleme koruması aktif — bu komut engellendi</div>
                    {% endif %}
                    <p style="color:#999; font-size:14px; margin:0 0 6px;">
                        Araç kontrol sistemine uzaktan erişim sağlandı.
                    </p>
                    <div class="info-box" style="color:#ff9900;">
                        ARAÇ ID &nbsp;: hedef_arac<br>
                        PLAKA &nbsp;&nbsp;: 34 TEZ 2026<br>
                        DURUM &nbsp;&nbsp;: AKTİF — Seyir Halinde<br>
                        ZAFİYET : Uzaktan Komut Enjeksiyonu (Port 444)
                    </div>
                </div>
                <form method="POST" action="/vehicles/lock">
                    {% if webpanel_lock_enabled %}
                    <button type="submit" class="btn btn-lock">🔒 ARACI UZAKTAN KİLİTLE</button>
                    {% else %}
                    <button type="button" class="btn btn-disabled" disabled>🛡️ ENGELLENDİ</button>
                    {% endif %}
                </form>
            </div>
        </div>

        <div class="console-box">
            <span style="color:#444;">root@vehicle-mgmt:~$</span>
            <span> {{ message }}</span>
            <span style="margin-left:4px; opacity:.7;">▌</span>
        </div>
    </div>
</body>
</html>
"""

# ── HATA SAYFASI ─────────────────────────────────────────────────────────────
ERROR_PAGE = COMMON_STYLE + """
<html>
<head><title>Erişim Reddedildi</title></head>
<body>
    <div class="scanline"></div>
    <div class="container" style="max-width:440px; margin-top:90px;">
        <div class="card">
            <div class="secure-banner">🛡️ MOD: GÜVENLİ (SECURE) 🛡️</div>
            <h2 style="color:#ff3333; text-align:center; margin-bottom:16px;">ERİŞİM ENGELLENDİ</h2>
            <div class="card-body">
                <p style="color:#999; font-size:14px; text-align:center;">
                    SQL Injection girişimi tespit edildi.<br>
                    Bu istek güvenlik sistemi tarafından engellendi ve loglandı.
                </p>
                <div class="info-box" style="color:#ff3333; text-align:left;">
                    [ALERT] Şüpheli payload tespit edildi<br>
                    [BLOCK] İstek reddedildi<br>
                    [LOG] &nbsp; IP adresi kayıt altına alındı
                </div>
            </div>
            <a href="/" style="color:#00ff41; font-family:monospace; display:block; text-align:center; margin-top:16px;">
                ← GERİ DÖN
            </a>
        </div>
    </div>
</body>
</html>
"""

# ── YARDIMCI FONKSİYONLAR ────────────────────────────────────────────────────

def send_to_manager(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((MANAGER_HOST, MANAGER_PORT))
        sock.sendall(command.encode('utf-8'))
        response = sock.recv(1024)
        sock.close()
        return f"KOMUT BAŞARIYLA İLETİLDİ >> {command}"
    except socket.timeout:
        return "HATA: Sunucu Zaman Aşımı [TIMEOUT]"
    except ConnectionRefusedError:
        return "HATA: Bağlantı Reddedildi — traffic_manager çalışıyor mu?"
    except Exception as e:
        return f"SİSTEM HATASI: {e}"

def is_sql_injection(value: str) -> bool:
    sql_keywords = [
        "' or ", "\" or ", "or '1'='1", "or 1=1",
        "--", ";--", "/*", "*/", "xp_", "drop ", "select ",
        "insert ", "delete ", "update ", "union ", "exec "
    ]
    return any(kw in value.lower() for kw in sql_keywords)

def live_log_path():
    for path in ("/attacker_logs/live_pentest.log", "../attacker/live_pentest.log", "attacker/live_pentest.log"):
        if os.path.exists(path):
            return path
    return None

def clean_terminal_line(line):
    line = re.sub(r"\x1b\[[0-9;]*m", "", line)
    return line.rstrip("\r\n")

def reports_dir():
    for path in ("/attacker_logs", "../attacker", "attacker"):
        if os.path.isdir(path):
            return path
    return None

def report_files(limit=8):
    folder = reports_dir()
    if not folder:
        return []
    reports = []
    try:
        for name in os.listdir(folder):
            if not name.startswith("PENTEZ_REPORT_") or not (name.endswith(".pdf") or name.endswith(".md")):
                continue
            path = os.path.join(folder, name)
            stat = os.stat(path)
            reports.append({
                "name": name,
                "modified_ts": stat.st_mtime,
                "modified": __import__("datetime").datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "size_kb": max(1, round(stat.st_size / 1024)),
            })
    except Exception:
        return []
    reports.sort(key=lambda item: item["modified_ts"], reverse=True)
    return reports[:limit]

# ── ROTALAR ──────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def home():
    return render_template_string(
        PRESENTATION_PAGE,
        sql_blocked=not SQL_INJECTION_ENABLED,
        attacks=attack_matrix(),
        counts=attack_counts(),
        reports=report_files()
    )

@app.route('/logo.png', methods=['GET'])
def logo_image():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if not os.path.exists(logo_path):
        abort(404)
    return send_file(logo_path, mimetype="image/png")

@app.route('/login-page', methods=['GET'])
def login_page():
    return render_template_string(
        ADMIN_LOGIN_PAGE,
        sql_blocked=not SQL_INJECTION_ENABLED
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # SQL Injection zafiyeti KAPALI
    if not SQL_INJECTION_ENABLED:
        if is_sql_injection(username) or is_sql_injection(password):
            print(f"[SECURE] SQL Injection engellendi! username='{username}'")
            return render_template_string(ERROR_PAGE)
        if username == "admin" and password == "admin123":
            return render_template_string(
                DASHBOARD_PAGE,
                message="[SECURE] Kimlik doğrulama başarılı. Hoş geldin, admin.",
                webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED,
                ransomware_enabled=RANSOMWARE_ENABLED
            )
        return render_template_string(
            ADMIN_LOGIN_PAGE + "<h3 style='color:red;text-align:center;'>HATALI ŞİFRE!</h3>",
            sql_blocked=True
        )

    # SQL Injection zafiyeti AÇIK
    if password == "admin123" \
            or "' or '1'='1" in username.lower() \
            or "' or '1'='1" in password.lower():
        return render_template_string(
            DASHBOARD_PAGE,
            message="[VULNERABLE] SQL Injection ile sisteme girildi!",
            webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED,
            ransomware_enabled=RANSOMWARE_ENABLED
        )
    return render_template_string(
        ADMIN_LOGIN_PAGE + "<h3 style='color:red;text-align:center;'>HATALI ŞİFRE!</h3>",
        sql_blocked=False
    )

@app.route('/send_command', methods=['POST'])
def send_command():
    cmd = request.form.get('cmd', '')

    # Ransomware koruması
    if cmd == "RANSOMWARE" and not RANSOMWARE_ENABLED:
        msg = "[SECURE] Ransomware komutu güvenlik sistemi tarafından engellendi!"
        return render_template_string(
            DASHBOARD_PAGE, message=msg,
            webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED,
            ransomware_enabled=RANSOMWARE_ENABLED
        )

    # Web Panel Lockdown koruması
    if cmd == "HACK_VEHICLE" and not WEBPANEL_LOCK_ENABLED:
        msg = "[SECURE] Araç kilitleme komutu güvenlik sistemi tarafından engellendi!"
        return render_template_string(
            DASHBOARD_PAGE, message=msg,
            webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED,
            ransomware_enabled=RANSOMWARE_ENABLED
        )

    msg = send_to_manager(cmd)
    return render_template_string(
        DASHBOARD_PAGE, message=msg,
        webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED,
        ransomware_enabled=RANSOMWARE_ENABLED
    )

@app.route('/vehicles', methods=['GET'])
def vehicles():
    if not WEBPANEL_LOCK_ENABLED:
        referer = request.headers.get('Referer', '')
        if 'localhost:5000' not in referer and '127.0.0.1:5000' not in referer:
            return render_template_string(ERROR_PAGE)
    return render_template_string(
        VEHICLES_PAGE,
        message="Araç yönetim sistemine bağlanıldı.",
        webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED
    )

@app.route('/vehicles/lock', methods=['POST'])
def lock_vehicle():
    if not WEBPANEL_LOCK_ENABLED:
        msg = "[SECURE] Araç kilitleme komutu güvenlik sistemi tarafından engellendi!"
        return render_template_string(
            VEHICLES_PAGE, message=msg,
            webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED
        )
    send_to_manager("LOCK_VEHICLE")
    return render_template_string(
        VEHICLES_PAGE,
        message="[LOCKDOWN] hedef_arac kilitlendi! Araç tüm hareket komutlarına yanıtsız.",
        webpanel_lock_enabled=WEBPANEL_LOCK_ENABLED
    )

@app.route('/live-log', methods=['GET'])
def live_log():
    from flask import jsonify
    path = live_log_path()
    tail = request.args.get("tail", "90")
    try:
        tail = max(20, min(200, int(tail)))
    except ValueError:
        tail = 90

    if not path:
        return jsonify({"active": False, "lines": []})

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [clean_terminal_line(line) for line in f.readlines()]
        lines = [line for line in lines if line.strip()]
        return jsonify({"active": True, "lines": lines[-tail:]})
    except Exception as e:
        return jsonify({"active": False, "lines": [f"Log okunamadi: {e}"]})

@app.route('/reports', methods=['GET'])
def reports_index():
    from flask import jsonify
    return jsonify(report_files(limit=30))

@app.route('/reports/<path:filename>', methods=['GET'])
def open_report(filename):
    folder = reports_dir()
    if not folder or "/" in filename or "\\" in filename:
        abort(404)
    if not filename.startswith("PENTEZ_REPORT_") or not (filename.endswith(".pdf") or filename.endswith(".md")):
        abort(404)
    path = os.path.abspath(os.path.join(folder, filename))
    root = os.path.abspath(folder)
    if not path.startswith(root) or not os.path.exists(path):
        abort(404)
    mimetype = "application/pdf" if filename.endswith(".pdf") else "text/markdown; charset=utf-8"
    return send_file(path, mimetype=mimetype, as_attachment=False)

@app.route('/security-status', methods=['GET'])
def security_status():
    """Saldırı bazlı güvenlik durumunu JSON olarak döner."""
    from flask import jsonify
    flags = {row["env"].lower().replace("_enabled", ""): row["enabled"] for row in attack_matrix()}
    return jsonify({
        "sql_injection": flags.get("sql_injection", SQL_INJECTION_ENABLED),
        "webpanel_lock": flags.get("webpanel_lock", WEBPANEL_LOCK_ENABLED),
        "ransomware": flags.get("ssh", RANSOMWARE_ENABLED),
        "ssh": flags.get("ssh", False),
        "speed_spoof": flags.get("speed_spoof", False),
        "iot_sensor": flags.get("iot_sensor", False),
        "ids_false_alarm": flags.get("ids_false_alarm", False),
        "ids_timing": flags.get("ids_timing", False),
        "fake_vehicle": flags.get("fake_vehicle", False),
        "v2v": flags.get("v2v", False),
        "v2i": flags.get("v2i", False),
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
