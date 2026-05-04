import socket
import time
import requests
import os
import re
from concurrent.futures import ThreadPoolExecutor


class ReconAgent:
    def __init__(self):
        self.target_ports = [21, 22, 80, 443, 444, 1234, 2222, 3306, 5000, 8080, 8813]

    def scan_port(self, ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return port
        except Exception:
            pass
        return None

    def scan_ports(self, target_ip):
        open_ports = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(lambda p: self.scan_port(target_ip, p), self.target_ports)

        for port in results:
            if port:
                open_ports.append(port)
        return open_ports

    def wait_for_open_ports(self, target_ip, expected_ports=None, attempts=12, delay=3):
        expected_ports = set(expected_ports or [])
        last_open_ports = []

        for attempt in range(1, attempts + 1):
            open_ports = self.scan_ports(target_ip)
            last_open_ports = open_ports

            if open_ports and (not expected_ports or expected_ports.issubset(set(open_ports))):
                return open_ports

            if attempt < attempts:
                missing = sorted(expected_ports - set(open_ports))
                if missing:
                    print(f"⏳ [RECON] Beklenen portlar henüz hazır değil {missing}; tekrar deneniyor ({attempt}/{attempts})...")
                else:
                    print(f"⏳ [RECON] Servisler henüz hazır değil; tekrar deneniyor ({attempt}/{attempts})...")
                time.sleep(delay)

        return last_open_ports

    def expected_ports_from_status(self, sec):
        expected = set()

        if sec.get("sql_injection", False) or sec.get("webpanel_lock", False):
            expected.add(5000)

        if sec.get("ssh", False):
            expected.add(2222)

        traffic_keys = (
            "speed_spoof",
            "iot_sensor",
            "ids_false_alarm",
            "ids_timing",
            "fake_vehicle",
            "v2v",
            "v2i",
        )
        if any(sec.get(key, False) for key in traffic_keys):
            expected.add(444)

        return expected

    def _compose_path(self):
        candidates = [
            os.path.join(os.getcwd(), "docker-compose.yaml"),
            os.path.join(os.getcwd(), "..", "docker-compose.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yaml"),
        ]
        for path in candidates:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                return full_path
        return None

    def _read_compose_security_status(self):
        mapping = {
            "SQL_INJECTION_ENABLED": "sql_injection",
            "WEBPANEL_LOCK_ENABLED": "webpanel_lock",
            "RANSOMWARE_ENABLED": "ransomware",
            "SSH_ENABLED": "ssh",
            "SPEED_SPOOF_ENABLED": "speed_spoof",
            "IOT_SENSOR_ENABLED": "iot_sensor",
            "IDS_FALSE_ALARM_ENABLED": "ids_false_alarm",
            "IDS_TIMING_ENABLED": "ids_timing",
            "FAKE_VEHICLE_ENABLED": "fake_vehicle",
            "V2V_ENABLED": "v2v",
            "V2I_ENABLED": "v2i",
        }
        path = self._compose_path()
        if not path:
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  [RECON] docker-compose.yaml okunamadı: {e}")
            return {}

        status = {}
        for env_key, status_key in mapping.items():
            match = re.search(rf"^\s*{env_key}:\s*[\"']?(true|false)[\"']?", content, re.IGNORECASE | re.MULTILINE)
            if match:
                status[status_key] = match.group(1).lower() == "true"

        if status:
            print(f"🔍 [RECON] Compose fallback güvenlik durumu: {status}")
        return status

    def get_security_status(self):
        """
        Web panelden ve komuta portundan saldırı bazlı güvenlik durumunu okur.
        """
        default = {
            "sql_injection":    False,
            "webpanel_lock":    False,
            "ransomware":       False,
            "ssh":              False,
            "speed_spoof":      False,
            "iot_sensor":       False,
            "ids_false_alarm":  False,
            "ids_timing":       False,
            "fake_vehicle":     False,
            "v2v":              False,
            "v2i":              False,
        }
        default.update(self._read_compose_security_status())

        # Web panel'den oku (SQL, WebPanel, Ransomware)
        try:
            r = requests.get("http://localhost:5000/security-status", timeout=2)
            if r.status_code == 200:
                web_status = r.json()
                default.update(web_status)
                print(f"🔍 [RECON] Web panel güvenlik durumu: {web_status}")
        except Exception as e:
            print(f"⚠️  [RECON] Web panel durumu okunamadı: {e}")

        # Komuta portundan oku (Speed, IoT, IDS, FakeVehicle, V2X)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(("localhost", 444))
            sock.sendall(b"STATUS")
            response = sock.recv(4096).decode("utf-8").strip()
            sock.close()
            import json
            if not response:
                raise ValueError("Komuta portu bos STATUS yaniti dondu")
            vc_status = json.loads(response)
            default.update(vc_status)
            print(f"🔍 [RECON] Komuta portu güvenlik durumu: {vc_status}")
        except Exception as e:
            print(f"⚠️  [RECON] Komuta portu durumu okunamadı: {e}")

        return default

    def run(self, blackboard):
        state     = blackboard.read_state()
        target_ip = state.get("target_ip", "localhost")

        print(f"\n🔍 [RECON] Port taraması başlatılıyor: {target_ip}")
        print(f"🔍 [RECON] Hedef portlar: {self.target_ports}")

        compose_sec = self._read_compose_security_status()
        expected_ports = self.expected_ports_from_status(compose_sec)
        if expected_ports:
            print(f"🔍 [RECON] Beklenen açık portlar: {sorted(expected_ports)}")

        open_ports = self.wait_for_open_ports(target_ip, expected_ports=expected_ports)

        if not open_ports:
            print("❌ [RECON] Hiçbir açık port bulunamadı.")
            print("💡 [RECON] Docker/SUMO servisleri henüz açılmamış olabilir. calistir.bat penceresinde hata var mı kontrol edin.")
            blackboard.update_key("mission_status", "FAIL")
            time.sleep(1)
            return

        for port in open_ports:
            print(f"✅ [RECON] AÇIK PORT: {port} ({self._identify_service(port)})")

        blackboard.update_key("open_ports", open_ports)

        # Güvenlik durumunu portlar hazır olduktan sonra al.
        sec = self.get_security_status()
        vulns = []

        # ── Web Panel ───────────────────────────────────────────────────────
        if 5000 in open_ports:
            if sec.get("sql_injection", False):
                print(f"🚨 [RECON] KRİTİK: Web panel SQL Injection zafiyeti açık!")
                vulns.append("LOGIN_PAGE_FOUND")
            else:
                print(f"🛡️  [RECON] SQL Injection SECURE modda engellendi.")

            if sec.get("webpanel_lock", False):
                print(f"🚨 [RECON] KRİTİK: Web Panel Lockdown zafiyeti açık!")
                vulns.append("WEBPANEL_LOCKDOWN")
            else:
                print(f"🛡️  [RECON] Web Panel Lockdown SECURE modda engellendi.")
        elif sec.get("sql_injection", False) or sec.get("webpanel_lock", False):
            print("⚠️  [RECON] Web panel zafiyeti açık görünüyor ama 5000 portu hazır değil.")

        # ── SSH / Ransomware ────────────────────────────────────────────────
        if 2222 in open_ports or 22 in open_ports:
            if sec.get("ssh", False):
                print(f"🚨 [RECON] KRİTİK: SSH portu açık — zayıf şifre zafiyeti!")
                vulns.append("SSH_OPEN_WEAK_PASSWORD")
            else:
                print(f"🛡️  [RECON] SSH portu açık ama brute force koruması aktif.")
        elif sec.get("ssh", False):
            print("⚠️  [RECON] SSH/Ransomware zafiyeti açık görünüyor ama 2222 portu hazır değil.")

        # ── Port 444 bazlı zafiyetler ───────────────────────────────────────
        if 444 in open_ports:
            if sec.get("speed_spoof", False):
                print(f"🚨 [RECON] KRİTİK: Port 444 — kimlik doğrulamasız hız kontrol soketi!")
                vulns.append("UNAUTHENTICATED_SPEED_CONTROL")
            else:
                print(f"🛡️  [RECON] Speed Spoof SECURE modda engellendi.")

            if sec.get("iot_sensor", False):
                print(f"🚨 [RECON] KRİTİK: IoT Sensör API'sine yetkisiz erişim!")
                vulns.append("UNAUTHENTICATED_SENSOR_API")
            else:
                print(f"🛡️  [RECON] IoT Sensör SECURE modda engellendi.")

            if sec.get("ids_false_alarm", False):
                print(f"🚨 [RECON] KRİTİK: IDS Yanlış Alarm zafiyeti tespit edildi!")
                vulns.append("IDS_FALSE_ALARM_VULN")
            else:
                print(f"🛡️  [RECON] IDS Yanlış Alarm SECURE modda engellendi.")

            if sec.get("ids_timing", False):
                print(f"🚨 [RECON] KRİTİK: Işık Zamanlama Sabotajı zafiyeti tespit edildi!")
                vulns.append("IDS_TIMING_VULN")
            else:
                print(f"🛡️  [RECON] Işık Zamanlama Sabotajı SECURE modda engellendi.")

            if sec.get("fake_vehicle", False):
                print(f"🚨 [RECON] KRİTİK: Hayalet araç enjeksiyonu mümkün!")
                vulns.append("UNAUTHENTICATED_VEHICLE_INJECTION")
            else:
                print(f"🛡️  [RECON] Fake Vehicle SECURE modda engellendi.")

            if sec.get("v2v", False):
                print(f"🚨 [RECON] KRİTİK: V2V yanlış bilgi yayılımı zafiyeti!")
                vulns.append("UNAUTHENTICATED_V2V_API")
            else:
                print(f"🛡️  [RECON] V2V SECURE modda engellendi.")

            if sec.get("v2i", False):
                print(f"🚨 [RECON] KRİTİK: V2I altyapı zehirlenmesi zafiyeti!")
                vulns.append("UNAUTHENTICATED_V2I_API")
            else:
                print(f"🛡️  [RECON] V2I SECURE modda engellendi.")

        # Faz kararı
        if vulns:
            blackboard.update_key("vulnerabilities", vulns)
            blackboard.update_key("current_phase", "EXPLOIT")
            print(f"📋 [RECON] Faz → EXPLOIT ({len(vulns)} zafiyet tespit edildi)")
        else:
            blackboard.update_key("current_phase", "ANALYSIS")
            print(f"📋 [RECON] Faz → ANALYSIS (port açık ama zafiyet yok)")
            if not any(p in open_ports for p in (80, 443, 5000, 8080)):
                blackboard.update_key("logs", ["ATTACK_BLOCKED: Aktif zafiyet bulunamadi."])
                blackboard.update_key("mission_status", "BLOCKED")

        time.sleep(1)

    def _identify_service(self, port):
        services = {
            21: "FTP", 22: "SSH", 80: "HTTP", 443: "HTTPS",
            444: "Traffic attack control socket",
            2222: "SSH", 3306: "MySQL",
            5000: "Web Panel (Flask)", 8080: "HTTP-Alt", 8813: "SUMO TraCI"
        }
        return services.get(port, "Bilinmiyor")
