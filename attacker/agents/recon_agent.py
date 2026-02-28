import socket
import time
from concurrent.futures import ThreadPoolExecutor

class ReconAgent:
    def __init__(self):
        # 2222: vehicle_controller SSH (docker mapped)
        self.target_ports = [21, 22, 80, 443, 1234, 2222, 3306, 5000, 8080, 8813]

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

    def run(self, blackboard):
        import requests
        # SECURITY_MODE'u web panelden oku
        security_mode = "VULNERABLE"
        try:
            r = requests.get("http://localhost:5000", timeout=2)
            if "MOD: GÜVENLİ" in r.text or "SECURE" in r.text.upper() and "ZAFİYETLİ" not in r.text:
                security_mode = "SECURE"
        except Exception:
            pass

        state     = blackboard.read_state()
        target_ip = state.get("target_ip", "localhost")

        print(f"\n🔍 [RECON] Port taraması başlatılıyor: {target_ip}")
        print(f"🔍 [RECON] Hedef portlar: {self.target_ports}")

        open_ports = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(lambda p: self.scan_port(target_ip, p), self.target_ports)

        for port in results:
            if port:
                open_ports.append(port)
                service = self._identify_service(port)
                print(f"✅ [RECON] AÇIK PORT: {port} ({service})")

        if open_ports:
            blackboard.update_key("open_ports", open_ports)

            # SSH portu açıksa — sadece VULNERABLE modda zafiyet kaydet
            if 2222 in open_ports or 22 in open_ports:
                if security_mode == "VULNERABLE":
                    print(f"🚨 [RECON] KRİTİK: SSH portu açık — zayıf şifre zafiyeti olabilir!")
                    blackboard.update_key("vulnerabilities", ["SSH_OPEN_WEAK_PASSWORD"])
                    blackboard.update_key("current_phase", "EXPLOIT")
                    print(f"📋 [RECON] Faz → EXPLOIT (SSH zafiyeti tespit edildi)")
                else:
                    print(f"🛡️  [RECON] SSH portu açık ama SECURE modda brute force engellendi.")
                    blackboard.update_key("current_phase", "ANALYSIS")
                    print(f"📋 [RECON] Faz → ANALYSIS")
            else:
                blackboard.update_key("current_phase", "ANALYSIS")
                print(f"📋 [RECON] Faz → ANALYSIS")
        else:
            print("❌ [RECON] Hiçbir açık port bulunamadı.")

        time.sleep(1)

    def _identify_service(self, port):
        services = {
            21: "FTP", 22: "SSH", 80: "HTTP", 443: "HTTPS",
            2222: "SSH (vehicle_controller)", 3306: "MySQL",
            5000: "Web Panel (Flask)", 8080: "HTTP-Alt", 8813: "SUMO TraCI"
        }
        return services.get(port, "Bilinmiyor")