import requests
import json
import markdown
import pdfkit
from datetime import datetime
import os

class ReportingAgent:
    def __init__(self, model_name="llama3.1", api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url

    def generate_report(self, blackboard):
        print("\n📝 [RAPORLAMA] LLM Ajanı verileri analiz ediyor...")

        state = blackboard.read_state()
        
        logs = state.get("logs", [])
        status = state.get("mission_status", "UNKNOWN")
        scenario = state.get("selected_scenario", "UNKNOWN")
        
        if not logs:
            print("❌ [RAPORLAMA] Analiz edilecek log bulunamadı.")
            return False

        raw_data = {
            "scenario_executed": scenario,
            "final_status": status,
            "system_logs": logs
        }

        # 1. ADIM: SİSTEM PROMPTU
        system_prompt = """
        Sen 'PENTEZ-AI' adında kıdemli bir Siber Güvenlik Analistisin. 
        Görevin, sana verilen V2X (Otonom Araç Ağı) sızma testi loglarını inceleyerek profesyonel bir sızma testi raporu oluşturmaktır.
        
        Rapor dili TÜRKÇE, resmi, akademik ve pasif bir dil olmalıdır.
        Çıktıyı SADECE Markdown formatında ver. Ekstra sohbet veya giriş cümlesi kurma.
        
        Aşağıdaki şablonu KESİNLİKLE birebir kullan:

        # PENTEZ-AI Sızma Testi Raporu
        **Tarih:** [Günün Tarihi] | **Hedef Sistem:** V2X Trafik Simülasyon Ağı (SUMO)
        
        ## 1. Rapor Başlığı
        [Senaryoya uygun profesyonel bir başlık üret]

        ## 2. İçindekiler
        - 3. Giriş
        - 4. Kapsam
        - 5. Yönetici Özeti (Executive Summary)
        - 6. Zafiyetler ve Detaylı Analiz
        - 7. MITRE ATT&CK Özeti
        - 8. Sonuç

        ## 3. Giriş
        [PENTEZ-AI'ın ne olduğunu ve V2X haberleşmesinin önemini anlatan kısa bir giriş yaz.]

        ## 4. Kapsam
        Bu sızma testinin kapsamı; Web Paneli (Port 5000), Komuta Soketi (Port 444) ve SUMO V2X ağ simülasyonu ile sınırlıdır.

        ## 5. Yönetici Özeti
        [Sisteme nasıl sızıldığını ve trafik/can güvenliği üzerindeki genel etkisini teknik olmayan bir dille özetle.]

        ## 6. Zafiyetler ve Detaylı Analiz
        [Sana verilen loglara bakarak tespit edilen zafiyetleri (örn: SQL Injection, Sybil Attack) CVSS skorları (X.X formatında), Açıklama ve Etki olarak listele. Loglardaki verileri kanıt (PoC) olarak sun.]

        ## 7. MITRE ATT&CK Özeti
        [Saldırıları MITRE ATT&CK taktiklerine göre (örn: Initial Access, Denial of Service) eşleştirerek açıkla.]

        ## 8. Sonuç
        [Tüm testin sonucunu toparlayan profesyonel bir kapanış yap.]
        """

        prompt = f"{system_prompt}\n\nİNCELENECEK LOG VERİLERİ:\n{json.dumps(raw_data, indent=2)}"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False 
        }

        try:
            print("⏳ [RAPORLAMA] Ollama API'sine bağlanılıyor (Bu işlem 10-30 saniye sürebilir)...")
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            report_text = result.get("response", "")

            # DOSYA ISMI VE KAYIT
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            md_filename = f"PENTEZ_REPORT_{timestamp}.md"
            
            with open(md_filename, "w", encoding="utf-8") as f:
                f.write(report_text)
            
            print(f"✅ [RAPORLAMA] Rapor başarıyla oluşturuldu: {md_filename}")
            print(f"💡 İpucu: Bu .md dosyasını VSCode ile açıp PDF'e dönüştürebilirsiniz.")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ [RAPORLAMA] Ollama API Hatası: {e}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"❌ [RAPORLAMA] Ollama API Hatası: {e}")
            return False
        except Exception as e:
            print(f"❌ [RAPORLAMA] PDF Çeviri Hatası: {e}")
            print("💡 İpucu: PDF çevirisi için sisteminizde 'wkhtmltopdf' aracının kurulu olması gerekebilir.")
            return True # MD kaydedilmiş olabilir, o yüzden True dönüyoruz