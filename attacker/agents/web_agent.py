import requests
from bs4 import BeautifulSoup

class WebAnalysisAgent:
    def __init__(self):
        self.found_vulns = []

    def analyze_url(self, ip, port):
        url = f"http://{ip}:{port}"
        print(f"🌐 [WEB] Analiz ediliyor: {url}")
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ [WEB] HTTP Servisi Aktif (Kod: 200)")
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text().lower()
                findings = []
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
        state = blackboard.read_state()
        target_ip = state.get("target_ip", "localhost")
        open_ports = state.get("open_ports", [])
        found_something = False

        for port in open_ports:
            url, findings = self.analyze_url(target_ip, port)
            if url and findings:
                blackboard.update_key("target_urls", [url])
                if "html_form" in findings and "password_input" in findings:
                    print(f"🚨 [WEB] KRİTİK: Admin Giriş Paneli Tespit Edildi!")
                    blackboard.update_key("vulnerabilities", ["LOGIN_PAGE_FOUND"])
                    blackboard.update_key("current_phase", "EXPLOIT")
                    found_something = True

                    # /vehicles sayfası keşfi
                    try:
                        vehicles_url = f"{url}/vehicles"
                        vresp = requests.get(vehicles_url, timeout=2)
                        if vresp.status_code == 200 and (
                            "ARAÇ" in vresp.text.upper() or "VEHICLE" in vresp.text.upper()
                        ):
                            print(f"🚨 [WEB] KRİTİK: Araç Yönetim Paneli Tespit Edildi! ({vehicles_url})")
                            blackboard.update_key("vulnerabilities", ["WEBPANEL_LOCKDOWN"])
                    except Exception:
                        pass

        if not found_something:
            print("ℹ️ [WEB] Web analizi bitti, kritik bir yapı bulunamadı.")