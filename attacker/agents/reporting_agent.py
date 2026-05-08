import requests
import json
from datetime import datetime
import os
import re

import platform
if platform.system() == "Windows":
    FONT_DIR = "C:/Windows/Fonts"
    # DejaVu yoksa Arial kullan

# ─── SENARYO VERİ TABANI ────────────────────────────────────────────────────
# Her saldırı senaryosu için CVSS, MITRE, PoC gibi veriler hardcode
# LLM bu verileri uydurmaz — sadece analiz metnini yazar
SCENARIO_DB = {
    "ATTACK_SQL": {
        "baslik": "SQL Enjeksiyonu ile Trafik Kontrol Paneline Yetkisiz Erisim",
        "zafiyet_adi": "SQL Injection (CWE-89)",
        "cvss_skor": "9.8",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1190", "taktor": "Initial Access", "teknik": "Exploit Public-Facing Application"},
            {"id": "T1059", "taktor": "Execution",       "teknik": "Command and Scripting Interpreter"},
            {"id": "T1565", "taktor": "Impact",          "teknik": "Data Manipulation"},
        ],
        "poc": "POST /login HTTP/1.1\nHost: localhost:5000\n\nusername=\' OR \'1\'=\'1&password=\' OR \'1\'=\'1",
        "etki": "Trafik kontrol sistemine tam yetkiyle erişim, tüm kavşak ışıklarının manipülasyonu",
        "oneri": "Parametreli sorgular (prepared statements) kullanılmalı, kullanıcı girdileri whitelist ile doğrulanmalıdır.",
    },
    "ATTACK_RANSOMWARE": {
        "baslik": "SSH Brute Force ile Arac Kontrol Sistemine Fidye Yazilimi Yuklenmesi",
        "zafiyet_adi": "Zayif SSH Kimlik Dogrulamasi (CWE-521) + Ransomware Deployment",
        "cvss_skor": "9.9",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1110.001", "taktor": "Credential Access", "teknik": "Brute Force: Password Guessing"},
            {"id": "T1021.004", "taktor": "Lateral Movement",  "teknik": "Remote Services: SSH"},
            {"id": "T1486",     "taktor": "Impact",            "teknik": "Data Encrypted for Impact"},
            {"id": "T1489",     "taktor": "Impact",            "teknik": "Service Stop"},
        ],
        "poc": "$ py main.py -t localhost -m llama3.1:latest\n[RECON] SSH portu acik: localhost:2222\n[BRUTE FORCE] Deneniyor: root:1234\n[SUCCESS] Sifre bulundu: root:1234\n[SSH] /app/DOSYALARINIZ_SIFRELENDI.txt olusturuldu\n[SSH] /app/control.py ENCRYPTED_BY_RANSOMWARE ile degistirildi\n[SSH] pkill -f control.py\n[IMPACT] localhost:444 uzerinden RANSOMWARE komutu gonderildi",
        "etki": "Zayıf SSH parolası nedeniyle vehicle_controller ele geçirilmiş, fidye notu bırakılmış, control.py dosyası şifrelenmiş ve SUMO tarafına ransomware etki komutu iletilmiştir.",
        "oneri": "SSH anahtar tabanlı kimlik doğrulama zorunlu hale getirilmeli, parola girişi devre dışı bırakılmalı, fail2ban ile brute force koruması uygulanmalıdır.",
    },
    "ATTACK_SPEED_SPOOF": {
        "baslik": "Kimlik Dogrulamasiz Kontrol Soketi Uzerinden Arac Hiz Manipulasyonu",
        "zafiyet_adi": "Kimlik Dogrulamasiz Ag Soketi (CWE-306)",
        "cvss_skor": "9.1",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1498",     "taktor": "Impact",    "teknik": "Network Denial of Service"},
            {"id": "T1565.001", "taktor": "Impact",    "teknik": "Stored Data Manipulation"},
        ],
        "poc": "$ nc localhost 444\nSPEED:hedef_arac:0\nOK: Hiz komutu uygulaniyor\nSPEED:hedef_arac:50\nOK: Hiz komutu uygulaniyor",
        "etki": "Hedef aracın hızının 0 m/s ile 50 m/s (~180 km/h) arasında serbestçe manipüle edilmesi, trafik kazasına yol açma",
        "oneri": "Kontrol soketine token tabanlı kimlik doğrulama eklenmeli, TLS şifrelemesi uygulanmalıdır.",
    },
    "ATTACK_WEBPANEL_LOCKDOWN": {
        "baslik": "Web Panel Uzerinden Arac Yonetim Sistemine Yetkisiz Erisim ve Arac Kilitleme",
        "zafiyet_adi": "Bozuk Erisim Kontrolu (CWE-284) + SQL Injection Zinciri",
        "cvss_skor": "9.6",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1190",     "taktor": "Initial Access",       "teknik": "Exploit Public-Facing Application"},
            {"id": "T1548",     "taktor": "Privilege Escalation", "teknik": "Abuse Elevation Control Mechanism"},
            {"id": "T1499",     "taktor": "Impact",               "teknik": "Endpoint Denial of Service"},
        ],
        "poc": "POST /login -> SQL Injection\nGET /vehicles -> HTTP 200 OK\nPOST /vehicles/lock -> LOCK_VEHICLE komutu iletildi",
        "etki": "Hedef aracın uzaktan kilitlenmesi, trafik içi ani duruş ve çarpışma riski",
        "oneri": "Oturum yönetimi güçlendirilmeli, /vehicles endpoint'ine yetkilendirme middleware eklenmeli, SQL injection için prepared statement kullanılmalıdır.",
    },
    "ATTACK_FAKE_VEHICLE": {
        "baslik": "Sahte Araç Enjeksiyonu ile V2X Yol Kilitleme (Sybil Saldırısı)",
        "zafiyet_adi": "Kimlik Doğrulamasız V2X Araç Enjeksiyon Soketi (CWE-306 + CWE-290)",
        "cvss_skor": "8.2",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1200",     "taktor": "Initial Access", "teknik": "Hardware Additions"},
            {"id": "T1565.002", "taktor": "Impact",         "teknik": "Transmitted Data Manipulation"},
            {"id": "T1499",     "taktor": "Impact",         "teknik": "Endpoint Denial of Service"},
        ],
        "poc": "$ nc localhost 444\nFAKE_VEHICLE\nOK\n# otoban_sag_1 uzerinde temp_sybil_route olusturuldu\n# sybil_block_* kimlikli 50 sahte arac dusuk araliklarla yola yerlestirildi\n# Sahte araclar 0 m/s hizda gri bariyer gibi konumlandirildi\n# Etki: Gercek araclar icin gecis engellendi ve yol kilitlendi",
        "etki": "Kimlik doğrulaması olmayan V2X komuta soketi üzerinden sahte araç kimlikleri üretilerek otoban_sag_1 hattına 50 adet durgun Sybil araç yerleştirilmesi, yolun bariyer gibi kilitlenmesi ve gerçek trafik akışını engellemesi",
        "oneri": "V2X araç kimlikleri PKI tabanlı sertifikalarla doğrulanmalı, aynı kaynaktan kısa sürede üretilen çoklu araç kimlikleri oran sınırlaması ve Sybil tespiti ile engellenmelidir.",
    },
    "ATTACK_SENSOR_SPOOF": {
        "baslik": "IoT Sensör API Zehirlenmesi ile Kavşak Faz Manipülasyonu",
        "zafiyet_adi": "Kimlik Doğrulamasız IoT Sensör API (CWE-306 + CWE-345)",
        "cvss_skor": "8.6",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1565.002", "taktor": "Impact",    "teknik": "Transmitted Data Manipulation"},
            {"id": "T1498",     "taktor": "Impact",    "teknik": "Network Denial of Service"},
        ],
        "poc": "$ nc localhost 444\nATTACK_SENSOR_SPOOF\nOK\n# Enjekte edilen sahte sensor verisi:\n# Ana yol: %0 yogunluk raporlandi (False Negative)\n# Yan yol: %98 yogunluk / 120 arac raporlandi (False Positive)\n# Etki: center kavsaginda yan yol yesile alindi, ana arter kirmizida bekletildi ve faz uzun sure donduruldu",
        "etki": "Kavşak kontrol algoritmasına çapraz yönlü sahte sensör verisi enjekte edilerek ana arterin kırmızıda bekletilmesi, boş/yan yolun önceliklendirilmesi ve trafik ışığı fazının uzun süre dondurulması",
        "oneri": "IoT sensör verileri HMAC veya dijital imza ile doğrulanmalı, birden fazla sensör kaynağı çapraz kontrol edilmeli ve tutarsız yoğunluk verileri için anomali eşikleri tanımlanmalıdır.",
    },
    "ATTACK_IDS_SPOOF_STOP": {
        "baslik": "IDS Yanlış Alarm Üretimi - Sahte Kaza Verisi ile Trafik Durdurma",
        "zafiyet_adi": "IDS/IPS Atlatma via Sahte Sensör Verisi (CWE-345 + CWE-693)",
        "cvss_skor": "7.5",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1565.002", "taktor": "Impact",          "teknik": "Transmitted Data Manipulation"},
            {"id": "T1562.001", "taktor": "Defense Evasion", "teknik": "Impair Defenses: Disable or Modify Tools"},
        ],
        "poc": "$ nc localhost 444\nATTACK_IDS_SPOOF_STOP\nOK\n# Kurban arac secildi ve hiz sensoru 0 km/s olarak zehirlendi\n# IDS ani durus/kaza alarmi uretti\n# Acil arac filosu sahte alarm bolgesine yonlendirildi",
        "etki": "Tek bir sensör kaynağından gelen sahte 0 km/s verisiyle IDS sisteminin kaza alarmi üretmesi, acil araç filosunun yanlış bölgeye yönlendirilmesi ve trafik akışını gereksiz yere durdurması",
        "oneri": "IDS sistemleri birden fazla bağımsız sensör kaynağını çapraz doğrulamalı, ani duruş alarmlarını konum, telemetri ve komşu araç verileriyle ilişkilendirmeden kritik aksiyon başlatmamalıdır.",
    },
    "ATTACK_IDS_SPOOF_SPEED": {
        "baslik": "Işık Zamanlama Sabotajı - Aşırı Hız Verisi ile Kavşak Faz Bozumu",
        "zafiyet_adi": "Sahte Hız Sensör Verisi ile Kavşak Faz Manipülasyonu (CWE-345)",
        "cvss_skor": "8.1",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1565.002", "taktor": "Impact", "teknik": "Transmitted Data Manipulation"},
            {"id": "T1499.002", "taktor": "Impact", "teknik": "Service Exhaustion Flood"},
        ],
        "poc": "$ nc localhost 444\nATTACK_IDS_SPOOF_SPEED\nOK\n# IoT hiz sensor agina 150 km/s sahte telemetri basildi\n# Kavsak kontrol algoritmasi asiri hizli sanal araclar algiladi\n# Etki: Trafik isiklari 1 saniyelik gecislerle disko moduna alindi",
        "etki": "150 km/s sahte hız telemetrisiyle kavşak kontrol algoritmasının karar mekanizmasının bozulması, trafik ışıklarının 1 saniyelik hızlı faz geçişlerine zorlanması ve kavşak akışını güvensiz hale getirmesi",
        "oneri": "Sensör girdilerinde fiziksel olarak mümkün olmayan değerler için sınır kontrolleri uygulanmalı, hız telemetrisi birden fazla kaynakla doğrulanmalı ve outlier tespiti için istatistiksel filtreler kullanılmalıdır.",
    },
    "ATTACK_V2X_V2V": {
        "baslik": "V2V Yanlış Bilgi Yayılımı (Şok Dalgası) — Sahte Acil Fren Sinyali ile Zincirleme Kaza",
        "zafiyet_adi": "V2V Haberleşme Kimlik Sahteciliği (CWE-290 + CWE-345)",
        "cvss_skor": "9.3",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1200",     "taktor": "Initial Access",    "teknik": "Hardware Additions"},
            {"id": "T1565.002", "taktor": "Impact",            "teknik": "Transmitted Data Manipulation"},
            {"id": "T1499",     "taktor": "Impact",            "teknik": "Endpoint Denial of Service"},
            {"id": "T1557",     "taktor": "Credential Access", "teknik": "Adversary-in-the-Middle"},
        ],
        "poc": "$ nc localhost 444\nATTACK_V2X_V2V\n# 1. hedef_arac V2X anteni ele geçirildi\n# 2. Zombi araç 50m yarıçapındaki tüm araçlara\n#    sahte Acil Fren sinyali yayınladı\n# 3. Komşu araçlar panik freni yaparak zincirleme\n#    kazaya neden oldu",
        "etki": "Hedef aracın V2X anteninin ele geçirilerek çevresindeki tüm otonom araçlara sahte acil fren sinyali yayılması ve zincirleme trafik kazasına yol açılması",
        "oneri": "V2V mesajları ETSI ITS-G5 veya IEEE 802.11p standartlarına uygun PKI altyapısıyla imzalanmalı, araç sertifikaları CRL ile doğrulanmalıdır.",
    },
    "ATTACK_V2X_V2I": {
        "baslik": "V2I Altyapı Zehirlenmesi - Sahte OBU Verisiyle Akıllı Kavşak Kilitleme",
        "zafiyet_adi": "V2I Altyapı Protokolünde Kimlik Doğrulaması Eksikliği (CWE-306 + CWE-290)",
        "cvss_skor": "9.1",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1200",     "taktor": "Initial Access", "teknik": "Hardware Additions"},
            {"id": "T1565.002", "taktor": "Impact",         "teknik": "Transmitted Data Manipulation"},
            {"id": "T1498",     "taktor": "Impact",         "teknik": "Network Denial of Service"},
        ],
        "poc": "$ nc localhost 444\nATTACK_V2X_V2I\n# 1. Araç içi ünite (OBU) ele geçirildi\n# 2. Kavşak RSU'suna sahte Acil Durum / Yüksek Hız verisi gönderildi\n# 3. Akıllı kavşak sahte veriye güvenerek kilitlendi",
        "etki": "Araç içi ünitenin (OBU) ele geçirilerek kavşak RSU'suna sahte acil durum verisi iletilmesi ve akıllı kavşak sisteminin kilitlenmesi",
        "oneri": "V2I altyapısında RSU'lar yalnızca sertifikalı OBU'lardan gelen imzalı mesajları kabul etmeli, anormallik tespiti için davranışsal analiz uygulanmalıdır.",
    },
}
# Bilinmeyen senaryo için varsayılan
DEFAULT_SCENARIO = {
    "baslik": "Genel Sızma Testi",
    "zafiyet_adi": "Tespit Edilen Zafiyet",
    "cvss_skor": "7.5",
    "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "risk_seviyesi": "YÜKSEK",
    "mitre": [
        {"id": "T1190", "taktor": "Initial Access", "teknik": "Exploit Public-Facing Application"},
    ],
    "poc": "Log verilerinden elde edilen kanıt",
    "etki": "Sistem güvenliğinin ihlali",
    "oneri": "İlgili güvenlik yamaları uygulanmalıdır.",
}


def normalize_risk(risk):
    value = (risk or "").upper()
    value = value.replace("İ", "I").replace("Ü", "U").replace("Ş", "S")
    value = value.replace("Ğ", "G").replace("Ö", "O").replace("Ç", "C")
    return value


def display_risk(risk):
    labels = {
        "KRITIK": "KRITIK",
        "YUKSEK": "YUKSEK",
        "ORTA": "ORTA",
        "DUSUK": "DUSUK",
    }
    return labels.get(normalize_risk(risk), risk or "BILINMIYOR")


def cwe_from_vulnerability_name(name):
    import re
    matches = re.findall(r"CWE-\d+", name or "")
    return ", ".join(matches) if matches else "N/A"


def format_test_logs(logs):
    if not logs:
        return "- *Log kaydi bulunamadi*"

    cleaned = []
    seen = set()
    for log in logs:
        if not log:
            continue
        line = str(log).strip()
        if "UPDATE: 'logs' guncellendi" in line:
            continue
        if line in seen:
            continue
        seen.add(line)
        cleaned.append(line)

    def sort_key(line):
        import re
        match = re.search(r"\[(\d{2}):(\d{2}):(\d{2})\]", line)
        if not match:
            return (99, 99, 99, line)
        return tuple(int(part) for part in match.groups()) + (line,)

    cleaned.sort(key=sort_key)

    important = []
    for line in cleaned:
        if (
            "target_ip" in line
            or "open_ports" in line
            or "vulnerabilities" in line
            or "selected_scenario" in line
            or "mission_status" in line
            or "SYSTEM_COMPROMISED" in line
            or "ATTACK_BLOCKED" in line
            or line.startswith("SQL")
            or line.startswith("SPEED")
            or line.startswith("SENSOR")
            or line.startswith("IDS")
            or line.startswith("FAKE")
            or line.startswith("V2X")
        ):
            important.append(line)

    if not important:
        important = cleaned

    return "\n".join(f"- `{line}`" for line in important)


def escape_pdf_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def strip_inline_markdown(text):
    return (
        str(text)
        .replace("**", "")
        .replace("`", "")
        .strip()
    )


def clean_llm_response(text):
    text = str(text or "").strip()
    text = re.sub(r"^\s*#+\s*.*\n+", "", text)
    text = re.sub(r"^\s*\*\*[^*\n]{3,80}\*\*\s*\n+", "", text)
    text = re.sub(r"^\s*(Yonetici Ozeti|Yönetici Özeti|Giris|Giriş|Sonuc|Sonuç)\s*:?\s*\n+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*Aşağıdaki .*?:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*Asagidaki .*?:\s*", "", text, flags=re.IGNORECASE)
    if len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        text = text[1:-1].strip()
    return text


class ReportingAgent:
    def __init__(self, model_name="llama3.1:latest", api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url

    def _llm_yorum(self, prompt, max_tokens=500):
        """LLM'den kısa analiz metni al"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.3}
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=120)
            resp.raise_for_status()
            return clean_llm_response(resp.json().get("response", ""))
        except Exception as e:
            return f"[LLM bağlantı hatası: {e}]"

    def _giris_ozeti(self, scenario_data, logs):
        prompt = f"""Sen kıdemli bir siber güvenlik analistisin. Aşağıdaki sızma testi için 3-4 cümlelik Türkçe, akademik ve resmi bir GİRİŞ paragrafı yaz.
PENTEZ-AI, akıllı şehir trafik altyapısına yönelik geliştirilen otonom bir sızma testi aracıdır — V2X bileşeni DEĞİLDİR.
Paragrafta şunları belirt: PENTEZ-AI'ın ne olduğu, test edilen sistemin (V2X trafik altyapısı) önemi, bu testin amacı.
Senaryo: {scenario_data['baslik']}
Sadece paragraf metnini yaz, başlık veya ek açıklama ekleme."""
        return self._llm_yorum(prompt, 300)

    def _yonetici_ozeti(self, scenario_data, logs, durum):
        log_str = "\n".join(logs[-10:]) if logs else "Log verisi yok"
        prompt = f"""Sen kıdemli bir siber güvenlik analistisin ve bu raporu savunma tarafı olarak yazıyorsun.
Aşağıdaki sızma testi için teknik olmayan bir dille 4-5 cümlelik Türkçe YÖNETİCİ ÖZETİ yaz.

ZORUNLU KURALLAR:
- Üçüncü şahıs kullan: "saldırı gerçekleştirildi", "sistem ele geçirildi", "zafiyet tespit edildi"
- "Saldırmış bulunmaktayız", "gerçekleştirdik" gibi birinci şahıs ifadesi YASAK
- Kavşak kilitlenmesi ve sahte veri enjeksiyonu trafik güvenliğini OLUMSUZ etkiler — bunu açıkça belirt
- Saldırının başarılı olduğunu ve bunun ciddi bir güvenlik riski oluşturduğunu vurgula

Senaryo: {scenario_data['baslik']}
Etki: {scenario_data['etki']}
Nihai Durum: {durum}
Loglar: {log_str}
Sadece paragraf metnini yaz, başlık ekleme."""
        return self._llm_yorum(prompt, 400)

    def _zafiyet_detay(self, scenario_data, logs):
        log_str = "\n".join(logs) if logs else "Log verisi yok"
        prompt = f"""Sen kıdemli bir siber güvenlik analistisin.
Aşağıdaki zafiyet için 3-4 cümlelik Türkçe teknik AÇIKLAMA yaz.

ZORUNLU KURALLAR:
- Zafiyet adını veya başlığını tekrar yazma — sadece açıklama metni yaz
- Zafiyetin KÖK NEDENİNİ (neden oluştu), NASIL İSTİSMAR EDİLDİĞİNİ ve SİSTEME ETKİSİNİ belirt
- Akademik ve teknik dil kullan

Zafiyet: {scenario_data['zafiyet_adi']}
Senaryo: {scenario_data['baslik']}
Log Kanıtları: {log_str}
Sadece açıklama metnini yaz, başlık veya zafiyet adını ekleme."""
        return self._llm_yorum(prompt, 350)

    def _sonuc(self, scenario_data, durum):
        prompt = f"""Sen kıdemli bir siber güvenlik analistisin.
Aşağıdaki sızma testi için 3-4 cümlelik Türkçe, resmi ve akademik bir SONUÇ paragrafı yaz.

ZORUNLU KURALLAR:
- Başlık veya liste YAZMA — sadece paragraf metni yaz
- "kaçınılmaz hale geliyor", "ortaya koyuyor" gibi gayri resmi ifadeler YASAK
- Geniş zaman değil geçmiş zaman: "edildi", "tespit edilmiştir", "gösterilmiştir"
- Testin önemini, zafiyetin kritikliğini ve önlem alınması gerekliliğini vurgula
- Üçüncü şahıs, akademik üslup

Senaryo: {scenario_data['baslik']}
Nihai Durum: {durum}
Sadece sonuç paragrafını yaz."""
        return self._llm_yorum(prompt, 300)

    def generate_report(self, blackboard):
        print("\n📝 [RAPORLAMA] Rapor oluşturuluyor...")

        state    = blackboard.read_state()
        logs     = state.get("logs", [])
        durum    = state.get("mission_status", "UNKNOWN")
        scenario = state.get("selected_scenario", "UNKNOWN")

        sc = SCENARIO_DB.get(scenario, DEFAULT_SCENARIO)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        ts_file   = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("⏳ [RAPORLAMA] LLM'den analiz metinleri alınıyor...")

        giris   = self._giris_ozeti(sc, logs)
        ozet    = self._yonetici_ozeti(sc, logs, durum)
        detay   = self._zafiyet_detay(sc, logs)
        sonuc   = self._sonuc(sc, durum)

        risk_key = normalize_risk(sc["risk_seviyesi"])
        risk_label = display_risk(sc["risk_seviyesi"])
        risk_badge = f"[{risk_label}]"

        # MITRE tablosu
        mitre_tablo = "\n".join([
            f"| {m['id']} | {m['taktor']} | {m['teknik']} |"
            for m in sc["mitre"]
        ])

        # Log tablosu
        log_listesi = format_test_logs(logs)

        md = f"""# PENTEZ-AI Sızma Testi Raporu

**Tarih:** {timestamp} | **Hedef Sistem:** V2X Trafik Simülasyon Ağı (SUMO) | **Gizlilik:** KESİNLİKLE GİZLİ

---

## 1. Rapor Başlığı

**{sc['baslik']}**

| Alan | Detay |
|------|-------|
| Rapor Tarihi | {timestamp} |
| Test Aracı | PENTEZ-AI v1.0 |
| Hedef | V2X Trafik Simülasyon Ağı |
| Senaryo | {sc['baslik']} |
| Nihai Durum | **{durum}** |

---

## 2. İçindekiler

3. Giriş
4. Kapsam
5. Yönetici Özeti (Executive Summary)
6. Zafiyetler ve Detaylı Analiz
7. Kanıtlar (Proof of Concept)
8. MITRE ATT&CK Özeti
9. Öneriler
10. Sonuç

---

## 3. Giriş

{giris}

---

## 4. Kapsam

Bu sızma testinin kapsamı aşağıdaki bileşenlerle sınırlıdır:

| Bileşen | Adres | Açıklama |
|---------|-------|----------|
| Web Paneli (Flask) | `localhost:5000` | Trafik kontrol C2 paneli |
| Kontrol Soketi | `localhost:444` | Araç komut soketi |
| SSH Servisi | `localhost:2222` | vehicle_controller SSH |
| SUMO Simülasyonu | TraCI port 8813 | V2X ağ simülasyonu |

---

## 5. Yönetici Özeti (Executive Summary)

{ozet}

### Risk Değerlendirmesi

| Seviye | Adet |
|--------|------|
| Kritik | {1 if risk_key == 'KRITIK' else 0} |
| Yüksek | {1 if risk_key == 'YUKSEK' else 0} |
| Orta | {1 if risk_key == 'ORTA' else 0} |
| Düşük | {1 if risk_key == 'DUSUK' else 0} |
| **Toplam** | **1** |

---

## 6. Zafiyetler ve Detaylı Analiz

### {risk_badge} Z-01 — {sc['zafiyet_adi']}

| Alan | Değer |
|------|-------|
| Risk Seviyesi | **{risk_label}** |
| CVSS v3.1 Skoru | **{sc['cvss_skor']} / 10.0** |
| CVSS Vektörü | `{sc['cvss_vektor']}` |
| CWE | `{cwe_from_vulnerability_name(sc['zafiyet_adi'])}` |

**Açıklama:**

{detay}

**Etki:**

{sc['etki']}

---

## 7. Kanıtlar (Proof of Concept)

```
{sc['poc']}
```

**Test Logları:**

{log_listesi}

---

## 8. MITRE ATT&#38;CK Özeti

| Teknik ID | Taktik | Teknik Adı |
|-----------|--------|------------|
{mitre_tablo}

---

## 9. Öneriler

| Öncelik | Öneri |
|---------|-------|
| **ACİL** | {sc['oneri']} |
| **YÜKSEK** | Tüm servisler için kimlik doğrulama ve yetkilendirme mekanizmaları gözden geçirilmelidir. |
| **ORTA** | Sızma testi bulgularına yönelik düzenli güvenlik denetimleri planlanmalıdır. |
| **DÜŞÜK** | Güvenlik farkındalığı eğitimlerinin personele uygulanması önerilmektedir. |

---

## 10. Sonuç

{sonuc}

---

*Bu rapor PENTEZ-AI otomatik sızma testi aracı tarafından {timestamp} tarihinde oluşturulmuştur.*
*Rapor içeriği gizlidir ve yalnızca yetkili personel tarafından görüntülenebilir.*
"""

        md_path = f"PENTEZ_REPORT_{ts_file}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"✅ [RAPORLAMA] Markdown raporu oluşturuldu: {md_path}")

        # PDF oluştur
        try:
            self._md_to_pdf(md, ts_file)
        except Exception as e:
            print(f"⚠️  [RAPORLAMA] PDF oluşturulamadı: {e}")
            print(f"💡 Markdown dosyasını VSCode veya Typora ile PDF'e dönüştürebilirsiniz.")

        return True

    def _md_to_pdf(self, md_content, ts_file):
        """Markdown'i PDF'e cevir — reportlab + DejaVu (Turkce karakter destegi)"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, Preformatted
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # DejaVu fontlarini kaydet — Turkce karakter destegi
        # Platform'a gore font dizini otomatik tespit edilir
        import platform, os
        _system = platform.system()
        if _system == "Windows":
            # Windows: DejaVu yoksa Arial kullan (Windows varsayilan Unicode font)
            _win_fonts = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
            _candidates = [
                # DejaVu (elle kurulduysa)
                (f"{_win_fonts}/DejaVuSans.ttf",      f"{_win_fonts}/DejaVuSans-Bold.ttf",
                 f"{_win_fonts}/DejaVuSans-Oblique.ttf", f"{_win_fonts}/DejaVuSansMono.ttf"),
                # Arial (Windows varsayilan, Turkce destekler)
                (f"{_win_fonts}/arial.ttf",  f"{_win_fonts}/arialbd.ttf",
                 f"{_win_fonts}/ariali.ttf", f"{_win_fonts}/cour.ttf"),
            ]
            _font_files = None
            for candidate in _candidates:
                if all(os.path.exists(f) for f in candidate):
                    _font_files = candidate
                    break
        else:
            _linux_dir = "/usr/share/fonts/truetype/dejavu"
            if os.path.exists(f"{_linux_dir}/DejaVuSans.ttf"):
                _font_files = (
                    f"{_linux_dir}/DejaVuSans.ttf",
                    f"{_linux_dir}/DejaVuSans-Bold.ttf",
                    f"{_linux_dir}/DejaVuSans-Oblique.ttf",
                    f"{_linux_dir}/DejaVuSansMono.ttf",
                )
            else:
                _font_files = None

        try:
            if _font_files is None:
                raise FileNotFoundError("Uygun font bulunamadi")
            _fn, _fb, _fi, _fm = _font_files
            pdfmetrics.registerFont(TTFont("TR-Normal", _fn))
            pdfmetrics.registerFont(TTFont("TR-Bold",   _fb))
            pdfmetrics.registerFont(TTFont("TR-Italic", _fi))
            pdfmetrics.registerFont(TTFont("TR-Mono",   _fm))
            from reportlab.pdfbase.pdfmetrics import registerFontFamily
            registerFontFamily("TR-Normal", normal="TR-Normal", bold="TR-Bold",
                               italic="TR-Italic", boldItalic="TR-Bold")
            FONT_NORMAL = "TR-Normal"
            FONT_BOLD   = "TR-Bold"
            FONT_MONO   = "TR-Mono"
            print(f"[RAPORLAMA] Font yuklendi: {os.path.basename(_fn)}")
        except Exception as e:
            print(f"[UYARI] Turkce font yuklenemedi: {e}")
            FONT_NORMAL = "Helvetica"
            FONT_BOLD   = "Helvetica-Bold"
            FONT_MONO   = "Courier"

        pdf_path = f"PENTEZ_REPORT_{ts_file}.pdf"
        doc = SimpleDocTemplate(
            pdf_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()

        # Ozel stiller — DejaVu font ile
        s_title   = ParagraphStyle("title_dj",  fontName=FONT_BOLD,
                                   fontSize=20, textColor=colors.HexColor("#1a1a2e"),
                                   spaceAfter=6)
        s_h1      = ParagraphStyle("h1_dj",     fontName=FONT_BOLD,
                                   fontSize=14, textColor=colors.HexColor("#e94560"),
                                   spaceBefore=14, spaceAfter=4)
        s_h2      = ParagraphStyle("h2_dj",     fontName=FONT_BOLD,
                                   fontSize=12, textColor=colors.HexColor("#0f3460"),
                                   spaceBefore=10, spaceAfter=3)
        s_body    = ParagraphStyle("body_dj",   fontName=FONT_NORMAL,
                                   fontSize=10, leading=14, spaceAfter=6)
        s_meta    = ParagraphStyle("meta_dj",   fontName=FONT_NORMAL,
                                   fontSize=9,  textColor=colors.grey, spaceAfter=10)
        s_code    = ParagraphStyle("code_dj",   fontName=FONT_MONO,
                                   fontSize=8,  backColor=colors.HexColor("#f5f5f5"),
                                   borderColor=colors.HexColor("#cccccc"),
                                   borderWidth=1, borderPad=6, spaceAfter=8)
        s_footer  = ParagraphStyle("footer_dj", fontName=FONT_NORMAL,
                                   fontSize=8,  textColor=colors.grey, alignment=TA_CENTER)

        RED   = colors.HexColor("#e94560")
        DARK  = colors.HexColor("#1a1a2e")
        BLUE  = colors.HexColor("#0f3460")
        LIGHT = colors.HexColor("#f5f5f5")

        def make_table(rows, header=True):
            if not rows:
                return Spacer(1, 0)
            col_count = len(rows[0])
            col_width = (A4[0] - 4*cm) / col_count

            # Hücre içeriklerini Paragraph'a çevir — Türkçe karakter desteği
            s_cell      = ParagraphStyle("cell",   fontName=FONT_NORMAL, fontSize=9, leading=12)
            s_cell_bold = ParagraphStyle("cell_b", fontName=FONT_BOLD,   fontSize=9, leading=12,
                                         textColor=colors.white)
            para_rows = []
            for ri, row in enumerate(rows):
                para_row = []
                for ci, cell in enumerate(row):
                    txt = escape_pdf_text(strip_inline_markdown(cell))
                    style = s_cell_bold if (ri == 0 and header) else s_cell
                    para_row.append(Paragraph(txt, style))
                para_rows.append(para_row)

            t = Table(para_rows, colWidths=[col_width]*col_count, repeatRows=1 if header else 0)
            style = [
                ("BACKGROUND", (0,0), (-1,0), DARK if header else LIGHT),
                ("ALIGN",      (0,0), (-1,-1), "LEFT"),
                ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
                ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
                ("PADDING",    (0,0), (-1,-1), 5),
            ]
            t.setStyle(TableStyle(style))
            return t

        story = []

        # Kapak başlık
        story.append(Spacer(1, 0.25*cm))
        story.append(Paragraph("PENTEZ-AI", ParagraphStyle("cover_dj", fontName=FONT_BOLD,
                                fontSize=24, leading=28, textColor=RED,
                                alignment=TA_CENTER, spaceAfter=2)))
        story.append(Paragraph("Sızma Testi Raporu", ParagraphStyle("cover2_dj", fontName=FONT_NORMAL,
                                fontSize=13, leading=17, textColor=DARK,
                                alignment=TA_CENTER, spaceAfter=8)))
        story.append(HRFlowable(width="100%", thickness=1.5, color=RED,
                                spaceBefore=4, spaceAfter=18))

        # Markdown satırlarını parse et
        lines = md_content.split("\n")
        i = 0
        in_code = False
        code_buf = []
        in_table = False
        table_rows = []

        while i < len(lines):
            line = lines[i]

            # Kod bloğu
            if line.strip().startswith("```"):
                if not in_code:
                    in_code = True
                    code_buf = []
                else:
                    in_code = False
                    code_text = "\n".join(code_buf)
                    story.append(Preformatted(code_text, s_code))
                i += 1
                continue

            if in_code:
                code_buf.append(line)
                i += 1
                continue

            # Tablo
            if line.strip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                # Ayraç satırını atla
                if all(set(c).issubset({"-", ":"," "}) for c in cells):
                    i += 1
                    continue
                table_rows.append(cells)
                i += 1
                continue
            else:
                if table_rows:
                    story.append(make_table(table_rows))
                    story.append(Spacer(1, 4))
                    table_rows = []

            # Başlıklar
            if line.startswith("## "):
                heading_text = line[3:]
                # ATT&CK içeren başlıklarda & işaretini koru, diğerlerini escape et
                if "ATT&#38;CK" in heading_text or "ATT&CK" in heading_text:
                    heading_text = heading_text.replace("ATT&#38;CK", "ATT&amp;CK")
                else:
                    heading_text = escape_pdf_text(heading_text)
                story.append(Paragraph(heading_text, s_h1))
            elif line.startswith("### "):
                story.append(Paragraph(line[4:], s_h2))
            elif line.startswith("# "):
                pass  # Ana başlık zaten kapakta
            elif line.startswith("---"):
                story.append(Spacer(1, 6))
            elif line.startswith("- ") or line.startswith("* "):
                txt = escape_pdf_text(strip_inline_markdown(line[2:]))
                if re.match(r"^\d+\.\s+", txt):
                    story.append(Paragraph(txt, s_body))
                else:
                    story.append(Paragraph(f"- {txt}", s_body))
            elif line.strip().startswith("**") and line.strip().endswith("**"):
                story.append(Paragraph(f"<b>{escape_pdf_text(strip_inline_markdown(line))}</b>", s_body))
            elif line.strip():
                clean = escape_pdf_text(line.strip())
                # Bold
                clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', clean)
                clean = re.sub(r'`(.+?)`', rf'<font name="{FONT_MONO}" size="9">\1</font>', clean)
                story.append(Paragraph(clean, s_body))
            else:
                story.append(Spacer(1, 4))

            i += 1

        # Kalan tablo
        if table_rows:
            story.append(make_table(table_rows))

        # Footer
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=RED))
        story.append(Paragraph(
            f"PENTEZ-AI Otomatik Sızma Testi Raporu - {datetime.now().strftime('%Y-%m-%d')} - GİZLİ",
            s_footer
        ))

        doc.build(story)
        print(f"✅ [RAPORLAMA] PDF raporu oluşturuldu: {pdf_path}")
        return pdf_path