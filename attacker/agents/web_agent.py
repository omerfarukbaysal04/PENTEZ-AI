import requests
import os
import re
from bs4 import BeautifulSoup


class WebAnalysisAgent:
    def __init__(self):
        self.found_vulns = []

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
        }
        path = self._compose_path()
        if not path:
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return {}

        status = {}
        for env_key, status_key in mapping.items():
            match = re.search(rf"^\s*{env_key}:\s*[\"']?(true|false)[\"']?", content, re.IGNORECASE | re.MULTILINE)
            if match:
                status[status_key] = match.group(1).lower() == "true"
        return status

    def get_security_status(self):
        """Web panelden saldırı bazlı güvenlik durumunu okur."""
        default = {"sql_injection": False, "webpanel_lock": False, "ransomware": False}
        default.update(self._read_compose_security_status())
        try:
            r = requests.get("http://localhost:5000/security-status", timeout=2)
            if r.status_code == 200:
                default.update(r.json())
        except Exception:
            pass
        return default

    def analyze_url(self, ip, port):
        url = f"http://{ip}:{port}"
        print(f"🌐 [WEB] Analiz ediliyor: {url}")
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ [WEB] HTTP Servisi Aktif (Kod: 200)")
                soup      = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text().lower()
                findings  = []

                forms = soup.find_all("form")
                if forms:
                    print(f"⚠️ [WEB] BULGU: Sayfada {len(forms)} adet FORM bulundu.")
                    findings.append("html_form")

                pass_inputs = soup.find_all("input", {"type": "password"})
                if pass_inputs:
                    print(f"⚠️ [WEB] BULGU: Şifre giriş alanı tespit edildi.")
                    findings.append("password_input")

                if "admin" in page_text or "login" in page_text or "giris" in page_text:
                    print(f"⚠️ [WEB] BULGU: Admin/Login ibareleri mevcut.")
                    findings.append("login_keywords")

                return url, findings
        except requests.exceptions.ConnectionError:
            print(f"❌ [WEB] {url} adresine baglanılamadı.")
        except Exception as e:
            print(f"❌ [WEB] Hata: {e}")
        return None, []

    def run(self, blackboard):
        state     = blackboard.read_state()
        target_ip = state.get("target_ip", "localhost")
        open_ports = state.get("open_ports", [])

        # Güvenlik durumunu al
        sec = self.get_security_status()

        found_something = False

        for port in open_ports:
            url, findings = self.analyze_url(target_ip, port)
            if not url or not findings:
                continue

            blackboard.update_key("target_urls", [url])

            if "html_form" in findings and "password_input" in findings:
                print(f"🚨 [WEB] KRİTİK: Admin Giriş Paneli Tespit Edildi!")
                found_something = True

                # SQL Injection zafiyeti açık mı?
                if sec.get("sql_injection", False):
                    blackboard.update_key("vulnerabilities", ["LOGIN_PAGE_FOUND"])
                    blackboard.update_key("current_phase", "EXPLOIT")
                    print(f"🚨 [WEB] SQL Injection zafiyeti aktif!")
                else:
                    print(f"🛡️  [WEB] Giriş paneli var ama SQL Injection SECURE modda engellendi.")

                # Web Panel Lockdown zafiyeti açık mı?
                try:
                    vehicles_url = f"{url}/vehicles"
                    vresp = requests.get(vehicles_url, timeout=2)
                    if vresp.status_code == 200 and (
                        "ARAÇ" in vresp.text.upper() or "VEHICLE" in vresp.text.upper()
                    ):
                        if sec.get("webpanel_lock", False):
                            print(f"🚨 [WEB] KRİTİK: Araç Yönetim Paneli Tespit Edildi! ({vehicles_url})")
                            blackboard.update_key("vulnerabilities", ["WEBPANEL_LOCKDOWN"])
                        else:
                            print(f"🛡️  [WEB] Araç paneli var ama Web Panel Lockdown SECURE modda engellendi.")
                except Exception:
                    pass

        if not found_something:
            print("ℹ️ [WEB] Web analizi bitti, kritik bir yapı bulunamadı.")
