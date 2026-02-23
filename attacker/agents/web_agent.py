import requests
from bs4 import BeautifulSoup

class WebAnalysisAgent:
    def __init__(self):
        self.found_vulns = []

    def analyze_url(self, ip, port):
        """Verilen IP ve Portta web servisi var mı diye bakar"""
        url = f"http://{ip}:{port}"
        print(f"🌐 [WEB] Analiz ediliyor: {url}")
        
        try:
            # 1. İstek At
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                print(f"✅ [WEB] HTTP Servisi Aktif (Kod: 200)")
                
                # 2. HTML İçeriğini Ayrıştır (Parse)
                soup = BeautifulSoup(response.text, 'html.parser')
                page_text = soup.get_text().lower()
                
                findings = []
                
                # 3. Kritik Şeyleri Ara
                # A. Login Formu Var mı?
                forms = soup.find_all('form')
                if forms:
                    print(f"⚠️ [WEB] BULGU: Sayfada {len(forms)} adet FORM bulundu.")
                    findings.append("html_form")
                
                # B. Şifre Giriş Kutusu Var mı?
                pass_inputs = soup.find_all('input', {'type': 'password'})
                if pass_inputs:
                    print(f"⚠️ [WEB] BULGU: Şifre giriş alanı tespit edildi.")
                    findings.append("password_input")
                
                # C. Anahtar Kelimeler
                if "admin" in page_text or "login" in page_text or "giris" in page_text:
                    print(f"⚠️ [WEB] BULGU: 'Admin/Login' ibareleri mevcut.")
                    findings.append("login_keywords")

                return url, findings
                
        except requests.exceptions.ConnectionError:
            print(f"❌ [WEB] {url} adresine baglanilamadi (Web servisi degil olabilir).")
        except Exception as e:
            print(f"❌ [WEB] Hata: {e}")
            
        return None, []

    def run(self, blackboard):
        """Ajanın ana çalışma fonksiyonu"""
        state = blackboard.read_state()
        target_ip = state.get("target_ip", "localhost")
        open_ports = state.get("open_ports", [])
        
        found_something = False

        for port in open_ports:
            # Sadece olası web portlarını veya bilinmeyenleri dene
            # Bizim senaryoda 5000 ve 80 kritik.
            url, findings = self.analyze_url(target_ip, port)
            
            if url and findings:
                # URL'i kaydet
                blackboard.update_key("target_urls", [url])
                
                # Eğer hem form hem şifre girişi varsa bu kesin bir Login Sayfasıdır
                # Eğer hem form hem şifre girişi varsa bu kesin bir Login Sayfasıdır
                if "html_form" in findings and "password_input" in findings:
                    print(f"🚨 [WEB] KRİTİK: Admin Giriş Paneli Tespit Edildi!")
                    blackboard.update_key("vulnerabilities", ["LOGIN_PAGE_FOUND"])
                    
                    # --- BU SATIRI EKLE (Fazı Değiştiriyoruz) ---
                    blackboard.update_key("current_phase", "EXPLOIT") 
                    # --------------------------------------------
                    
                    found_something = True

        if not found_something:
            print("ℹ️ [WEB] Web analizi bitti, kritik bir yapı bulunamadı.")