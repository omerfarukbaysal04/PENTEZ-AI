import socket
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- AYARLAR ---
MANAGER_HOST = "host.docker.internal"
MANAGER_PORT = 444

# --- GÜVENLİK MODU ---
SECURITY_MODE = os.environ.get("SECURITY_MODE", "VULNERABLE").upper()
print(f"[MOD] Sistem modu: {SECURITY_MODE}")

# --- CSS ---
COMMON_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap');

    *, *::before, *::after { box-sizing: border-box; }

    body {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
        margin: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
    }

    .scanline {
        width: 100%;
        height: 100px;
        z-index: 10;
        background: linear-gradient(0deg, rgba(0,0,0,0) 0%, rgba(51,255,0,0.03) 50%, rgba(0,0,0,0) 100%);
        opacity: 0.1;
        position: absolute;
        bottom: 100%;
        animation: scanline 10s linear infinite;
        pointer-events: none;
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
        width: 90%;
        max-width: 1100px;
        margin-top: 40px;
        z-index: 2;
    }

    /* ── KARTLAR ── */
    .card {
        background: rgba(20,20,20,0.85);
        border: 1px solid #333;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
        backdrop-filter: blur(5px);
        transition: transform 0.25s, border-color 0.25s;
        display: flex;
        flex-direction: column;
    }
    .card:hover {
        transform: translateY(-2px);
        border-color: #00ff41;
    }
    .card .card-body {
        flex: 1;
    }

    /* ── GRİD ── */
    .grid-2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        align-items: stretch;
        margin-bottom: 20px;
    }
    .grid-full {
        margin-bottom: 20px;
    }

    /* ── INPUT ── */
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
    input:focus {
        outline: none;
        border-color: #00ff41;
        box-shadow: 0 0 8px rgba(0,255,65,0.3);
    }

    /* ── BUTONLAR ── */
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
    .btn-login  { background: #00ff41; color: #000; }
    .btn-login:hover { background: #00cc33; box-shadow: 0 0 15px #00ff41; }

    .btn-hack   { background: linear-gradient(45deg,#cc0000,#990000); color:#fff; border:1px solid #ff0000; }
    .btn-hack:hover { background: linear-gradient(45deg,#ff0000,#cc0000); box-shadow:0 0 20px rgba(255,0,0,.6); }

    .btn-lock   { background: linear-gradient(45deg,#ff9900,#cc7a00); color:#000; border:1px solid #ffcc00; }
    .btn-lock:hover { background: linear-gradient(45deg,#ffcc00,#ff9900); box-shadow:0 0 20px rgba(255,153,0,.6); }

    .btn-ransomware { background: linear-gradient(45deg,#8b00ff,#5500aa); color:#fff; border:1px solid #cc00ff; }
    .btn-ransomware:hover { background: linear-gradient(45deg,#cc00ff,#8b00ff); box-shadow:0 0 20px rgba(139,0,255,.7); }

    /* ── STATUS DOT ── */
    .status-dot {
        height: 12px; width: 12px;
        background-color: #00ff41;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #00ff41;
        animation: blink 2s infinite;
        margin-right: 8px;
    }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }

    /* ── KONSOL ── */
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

    /* ── INFO KUTUSU ── */
    .info-box {
        background: #111;
        padding: 10px 14px;
        margin: 14px 0;
        border-radius: 4px;
        font-size: 12px;
        line-height: 1.8;
        font-family: 'Share Tech Mono', monospace;
    }

    /* ── BANNER ── */
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

    /* ── TOPBAR ── */
    .topbar {
        width: 100%;
        background: #0a0a0a;
        border-bottom: 1px solid #222;
        padding: 14px 0;
    }
    .topbar-inner {
        width: 90%; max-width: 1100px;
        margin: 0 auto;
        display: flex; justify-content: space-between; align-items: center;
    }
</style>
"""

# ── LOGIN SAYFASI ──
LOGIN_PAGE = COMMON_STYLE + """
<html>
<head><title>Sistem Girişi</title></head>
<body>
    <div class="scanline"></div>
    <div class="container" style="max-width:420px; margin-top:90px;">
        <div class="card">
            {% if mode == 'VULNERABLE' %}
            <div class="vulnerable-banner">⚠️ MOD: ZAFİYETLİ (VULNERABLE) ⚠️</div>
            {% else %}
            <div class="secure-banner">🛡️ MOD: GÜVENLİ (SECURE) 🛡️</div>
            {% endif %}
            <h2 style="color:#00ff41; text-align:center; margin-bottom:24px; text-shadow:0 0 10px rgba(0,255,65,.5);">
                <span class="status-dot"></span>SİSTEM GİRİŞİ
            </h2>
            <div class="card-body">
                <form method="POST" action="/login">
                    <input type="text"     name="username" placeholder="KULLANICI ADI">
                    <input type="password" name="password" placeholder="ŞİFRE">
                    <button type="submit" class="btn btn-login">ERİŞİM İSTE</button>
                </form>
            </div>
            <p style="color:#555; font-size:12px; text-align:center; margin-top:18px;">
                SECURE CONNECTION V4.2 · AUTHENTICATION REQUIRED
            </p>
        </div>
    </div>
</body>
</html>
"""

# ── DASHBOARD SAYFASI ──
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

        <!-- ÜST İKİ KART -->
        <div class="grid-2">

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
                    <button type="submit" class="btn btn-hack">
                        🚨 TÜM IŞIKLARI YEŞİL YAP
                    </button>
                </form>
            </div>

            <div class="card">
                <h3 style="color:#ff9900; border-bottom:1px solid #2a2a2a; padding-bottom:10px; margin-top:0;">
                    🦠 ARAÇ KİLİTLEME
                </h3>
                <div class="card-body">
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
                    <button type="submit" class="btn btn-lock">
                        🔒 ARACI KİLİTLE
                    </button>
                </form>
            </div>

        </div>

        <!-- RANSOMWARE KARTI -->
        <div class="grid-full">
            <div class="card">
                <h3 style="color:#cc00ff; border-bottom:1px solid #2a2a2a; padding-bottom:10px; margin-top:0;">
                    💀 RANSOMWARE SALDIRISI
                </h3>
                <div class="card-body">
                    <p style="color:#999; font-size:14px; margin:0 0 6px;">
                        Trafik yönetim sürecini sonlandırır, kritik dosyaları kilitler ve sistemde fidye notu bırakır.
                        Tüm trafik kontrolü devre dışı kalır.
                    </p>
                    <div class="info-box" style="color:#cc00ff;">
                        HEDEF: traffic_manager.py (PID) &nbsp;|&nbsp;
                        ETKİ: Tüm Trafik Sistemi Çöküşü &nbsp;|&nbsp;
                        ZAFİYET: Kimlik Doğrulama Yok
                    </div>
                </div>
                <form method="POST" action="/send_command">
                    <input type="hidden" name="cmd" value="RANSOMWARE">
                    <button type="submit" class="btn btn-ransomware">
                        💀 RANSOMWARE BAŞLAT
                    </button>
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
                    <button class="btn btn-lock" style="margin-top:0;">
                        🔗 ARAÇ PANELİNE GİT
                    </button>
                </a>
            </div>
        </div>

        <!-- KONSOL -->
        <div class="console-box">
            <span style="color:#444;">root@admin-panel:~$</span>
            <span> {{ message }}</span>
            <span style="margin-left:4px; opacity:.7;">▌</span>
        </div>

    </div>
</body>
</html>
"""


# ── ARAÇ YÖNETİM SAYFASI ──
VEHICLES_PAGE = COMMON_STYLE + """
<html>
<head><title>Araç Yönetim Paneli</title></head>
<body>
    <div class="scanline"></div>

    <div class="topbar">
        <div class="topbar-inner">
            <div>
                <h2 style="margin:0; font-size:22px; text-shadow:0 0 10px rgba(0,255,65,.4);">
                    ARAÇ YÖNETİM SİSTEMİ
                </h2>
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
                    <p style="color:#999; font-size:14px; margin:0 0 6px;">
                        Araç kontrol sistemine uzaktan erişim sağlandı. Aracı kilitleyerek tüm hareket
                        komutlarını devre dışı bırakabilirsiniz. Araç trafikte ani duruş yaparak anarşiye sebep olur.
                    </p>
                    <div class="info-box" style="color:#ff9900;">
                        ARAÇ ID &nbsp;: hedef_arac<br>
                        PLAKA &nbsp;&nbsp;: 34 TEZ 2026<br>
                        DURUM &nbsp;&nbsp;: AKTİF — Seyir Halinde<br>
                        ZAFİYET : Uzaktan Komut Enjeksiyonu (Port 9999)
                    </div>
                </div>
                <form method="POST" action="/vehicles/lock">
                    <button type="submit" class="btn btn-lock">
                        🔒 ARACI UZAKTAN KİLİTLE
                    </button>
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

# ── HATA SAYFASI ──
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

# ── YARDIMCI FONKSİYONLAR ──

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

# ── ROTALAR ──

@app.route('/', methods=['GET'])
def home():
    return render_template_string(LOGIN_PAGE, mode=SECURITY_MODE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if SECURITY_MODE == "VULNERABLE":
        if password == "admin123" \
                or "' or '1'='1" in username.lower() \
                or "' or '1'='1" in password.lower():
            return render_template_string(
                DASHBOARD_PAGE,
                message="[VULNERABLE] SQL Injection ile sisteme girildi!"
            )
        return render_template_string(
            LOGIN_PAGE + "<h3 style='color:red;text-align:center;'>HATALI ŞİFRE!</h3>",
            mode=SECURITY_MODE
        )
    else:
        if is_sql_injection(username) or is_sql_injection(password):
            print(f"[SECURE] SQL Injection engellendi! username='{username}'")
            return render_template_string(ERROR_PAGE)
        if username == "admin" and password == "admin123":
            return render_template_string(
                DASHBOARD_PAGE,
                message="[SECURE] Kimlik doğrulama başarılı. Hoş geldin, admin."
            )
        return render_template_string(
            LOGIN_PAGE + "<h3 style='color:red;text-align:center;'>HATALI ŞİFRE!</h3>",
            mode=SECURITY_MODE
        )

@app.route('/send_command', methods=['POST'])
def send_command():
    cmd = request.form.get('cmd', '')
    if SECURITY_MODE == "SECURE" and cmd == "RANSOMWARE":
        msg = "[SECURE] Ransomware komutu güvenlik sistemi tarafından engellendi!"
        return render_template_string(DASHBOARD_PAGE, message=msg)
    msg = send_to_manager(cmd)
    return render_template_string(DASHBOARD_PAGE, message=msg)

@app.route('/vehicles', methods=['GET'])
def vehicles():
    # SECURE modda: sadece oturum açmış kullanıcılar erişebilir
    # Basit simülasyon için referer kontrolü yapıyoruz
    if SECURITY_MODE == "SECURE":
        referer = request.headers.get('Referer', '')
        if 'localhost:5000' not in referer and '127.0.0.1:5000' not in referer:
            return render_template_string(ERROR_PAGE)
    return render_template_string(VEHICLES_PAGE, message="Araç yönetim sistemine bağlanıldı.")

@app.route('/vehicles/lock', methods=['POST'])
def lock_vehicle():
    if SECURITY_MODE == "SECURE":
        msg = "[SECURE] Araç kilitleme komutu güvenlik sistemi tarafından engellendi!"
        return render_template_string(VEHICLES_PAGE, message=msg)
    msg = send_to_manager("LOCK_VEHICLE")
    return render_template_string(VEHICLES_PAGE,
        message="[LOCKDOWN] hedef_arac kilitlendi! Araç tüm hareket komutlarına yanıtsız.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)