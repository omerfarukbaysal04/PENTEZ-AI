import requests
import json

class StrategicAgent:
    def __init__(self, model_name="llama3.1:latest"):
        self.model   = model_name
        self.api_url = "http://localhost:11434/api/generate"
        print(f"🧠 [BEYİN] Hazırlanıyor... Model: {self.model}")

    def decide_next_step(self, blackboard_summary):
        system_prompt = """
        SEN OTONOM SIZMA TESTİ KARAR MEKANIZMASISIN.
        Görevin: Blackboard durumuna göre sıradaki EN MANTIKLI adımı seçmektir.

        KARAR HİYERARŞİSİ (SIRAYLA KONTROL ET, İLK UYANA SEÇ):

        0. EN YÜKSEK ÖNCELİK — ÖNCE SADECE BUNU KONTROL ET:
           - 'mission_status' == 'SUCCESS' ise -> 'FINISH' SEÇ.
           - 'mission_status' == 'BLOCKED'  ise -> 'FINISH' SEÇ.
           - 'mission_status' == 'FAIL'     ise -> 'FINISH' SEÇ.
           - 'system_compromised' == true   ise -> 'FINISH' SEÇ.
           - 'attack_blocked'     == true   ise -> 'FINISH' SEÇ.
           KURAL: mission_status 'ONGOING' değilse FINISH seç!

        1. ÖNCELİK — SADECE mission_status 'ONGOING' ise değerlendir:
           - 'phase' == 'EXPLOIT' ise, hangi saldırıyı seçeceğine karar ver:
             * 'vulns' içinde 'SSH_OPEN_WEAK_PASSWORD' varsa -> 'ATTACK_RANSOMWARE' SEÇ.
             * 'vulns' içinde 'LOGIN_PAGE_FOUND' varsa        -> 'ATTACK_SQL' SEÇ.
             * İkisi de varsa -> 'ATTACK_RANSOMWARE' SEÇ. (SSH daha kritik zafiyet)
           - 'phase' == 'ANALYSIS' ise -> 'ANALYZE_WEB' SEÇ.
           - 'phase' == 'RECON'    ise -> 'SCAN_PORTS' SEÇ.

        SADECE JSON FORMATINDA CEVAP VER. Başka hiçbir şey yazma.
        Örnek: {"decision": "ATTACK_RANSOMWARE", "reason": "SSH zafiyeti tespit edildi."}
        """

        user_message = f"ŞU ANKİ DURUM RAPORU: {blackboard_summary}"

        payload = {
            "model":  self.model,
            "prompt": system_prompt + "\n\n" + user_message,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()

            raw_text      = response.json().get('response', '{}')
            decision_data = json.loads(raw_text)

            action = decision_data.get("decision") or decision_data.get("action") or "WAIT"
            reason = decision_data.get("reason", "Sebep belirtilmedi.")
            return {"decision": action, "reason": reason}

        except requests.exceptions.ConnectionError:
            return {"decision": "ERROR", "reason": "Ollama bağlantısı yok! 'ollama serve' çalıştırın."}
        except json.JSONDecodeError:
            return {"decision": "ERROR", "reason": "LLM bozuk JSON üretti."}
        except Exception as e:
            return {"decision": "ERROR", "reason": f"Beklenmedik Hata: {str(e)}"}


if __name__ == "__main__":
    test_state = '{"phase":"EXPLOIT","ports":[22,5000],"vulns":["SSH_OPEN_WEAK_PASSWORD","LOGIN_PAGE_FOUND"],"mission_status":"ONGOING","system_compromised":false,"attack_blocked":false}'
    brain = StrategicAgent(model_name="llama3.1:latest")
    print(f"SONUÇ: {brain.decide_next_step(test_state)}")