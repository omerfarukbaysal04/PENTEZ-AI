import requests
import json
from datetime import datetime
import os

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
        "etki": "Trafik kontrol sistemine tam yetkiyle erisim, tum kavsak isiklainin manipulasyonu",
        "oneri": "Parametreli sorgular (prepared statements) kullanilmali, kullanici girdileri whitelist ile dogrulanmalidir.",
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
        "poc": "$ hydra -l root -P wordlist.txt ssh://localhost:2222\n[22][ssh] host: localhost  login: root  password: 1234\n$ ssh root@localhost -p 2222\n# echo ENCRYPTED > /app/control.py && pkill -f control.py",
        "etki": "Arac kontrol dosyalarinin sifrelenmesi, arac kontrol surecinin sonlandirilmasi, tum araclarin durdurulmasi ve kavsaklarin kilitlenmesi",
        "oneri": "SSH anahtar tabanli kimlik dogrulama zorunlu hale getirilmeli, parola girisi devre disi birakilmali, fail2ban ile brute force korumasi uygulanmalidir.",
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
        "etki": "Hedef aracin hizinin 0 m/s ile 50 m/s (~180 km/h) arasinda serbestce manipule edilmesi, trafik kazasina yol acma",
        "oneri": "Kontrol soketine token tabanli kimlik dogrulama eklenmeli, TLS sifrelemesi uygulanmalidir.",
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
        "etki": "Hedef aracin uzaktan kilitlenmesi, trafik ici ani durus ve carpisme riski",
        "oneri": "Oturum yonetimi guclendirilmeli, /vehicles endpoint'ine yetkilendirme middleware eklenmeli, SQL injection icin prepared statement kullanilmalidir.",
    },
    "ATTACK_FAKE_VEHICLE": {
        "baslik": "Sahte Arac Enjeksiyonu ile V2X Trafik Manipulasyonu (Sybil Saldirisi)",
        "zafiyet_adi": "Kimlik Dogrulamasiz V2X Arac Enjeksiyon Soketi (CWE-306 + CWE-290)",
        "cvss_skor": "8.2",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1200",     "taktor": "Initial Access", "teknik": "Hardware Additions"},
            {"id": "T1565.002", "taktor": "Impact",         "teknik": "Transmitted Data Manipulation"},
            {"id": "T1499",     "taktor": "Impact",         "teknik": "Endpoint Denial of Service"},
        ],
        "poc": "$ nc localhost 444\nFAKE_VEHICLE\nOK: Sahte arac enjekte edildi\n# 5 sahte arac simulasyona eklendi\n# Trafik yogunlugu yapay olarak artirildi",
        "etki": "Simulasyona sahte arac enjekte edilerek trafik yogunlugunun yapay artirilmasi ve kavsak algoritmalarinin yaniltilmasi",
        "oneri": "V2X arac kimlik dogrulamasi icin PKI tabanli sertifika altyapisi kurulmali, arac kimlikleri kriptografik olarak dogrulanmalidir.",
    },
    "ATTACK_SENSOR_SPOOF": {
        "baslik": "IoT Sensor API Zehirlenmesi ile Kavsak Algoritmasi Manipulasyonu",
        "zafiyet_adi": "Kimlik Dogrulamasiz IoT Sensor API (CWE-306 + CWE-345)",
        "cvss_skor": "8.6",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1565.002", "taktor": "Impact",    "teknik": "Transmitted Data Manipulation"},
            {"id": "T1498",     "taktor": "Impact",    "teknik": "Network Denial of Service"},
        ],
        "poc": "$ nc localhost 444\nATTACK_SENSOR_SPOOF\n# Enjekte edilen sahte sensor verisi:\n# vehicle_count: 999, speed: 0\n# Etki: Kavsak tum yonlerden asiri arac geldigini sanarak kilitlendi",
        "etki": "Kavsak kontrol algoritmasina capraz yonlu sahte arac verisi enjekte edilerek tum sinyalizasyonun kilitlenmesi ve trafik felci",
        "oneri": "IoT sensor verileri HMAC veya dijital imza ile dogrulanmali, anomali tespiti icin esik degerleri tanimlanmalidir.",
    },
    "ATTACK_IDS_SPOOF_STOP": {
        "baslik": "IDS Yanlis Alarm Uretimi - Sahte Kaza Verisi ile Trafik Durdurma",
        "zafiyet_adi": "IDS/IPS Atlatma via Sahte Sensor Verisi (CWE-345 + CWE-693)",
        "cvss_skor": "7.5",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1565.002", "taktor": "Impact",          "teknik": "Transmitted Data Manipulation"},
            {"id": "T1562.001", "taktor": "Defense Evasion", "teknik": "Impair Defenses: Disable or Modify Tools"},
        ],
        "poc": "$ nc localhost 444\nATTACK_IDS_SPOOF_STOP\n# Tum araclara hiz=0 km/s sahte verisi\n# Etki: IDS sistemi kaza oldugunu sanarak tum kavsaklari durdurdu",
        "etki": "Tum araclarin hizini 0 olarak raporlayan sahte sensor verisiyle IDS yanlis alarm uretmesi ve trafik sisteminin gereksiz yere durdurulmasi",
        "oneri": "IDS sistemleri birden fazla bagimsiz sensor kaynagini capraz dogrulamali, tek kaynakli verilere dayanmamalidir.",
    },
    "ATTACK_IDS_SPOOF_SPEED": {
        "baslik": "Isik Zamanlama Sabotaji - Asiri Hiz Verisi ile Kavsak Cokusu",
        "zafiyet_adi": "Kavsak Kontrol Algoritmasi Manipulasyonu via Asiri Hiz Enjeksiyonu (CWE-345)",
        "cvss_skor": "8.1",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H",
        "risk_seviyesi": "YUKSEK",
        "mitre": [
            {"id": "T1565.002", "taktor": "Impact", "teknik": "Transmitted Data Manipulation"},
            {"id": "T1499.002", "taktor": "Impact", "teknik": "Service Exhaustion Flood"},
        ],
        "poc": "$ nc localhost 444\nATTACK_IDS_SPOOF_SPEED\n# Tum araclara hiz=150 km/s sahte verisi\n# Etki: Kavsak algoritmasi coktu, isiklar 1 sn'de bir degisti (disko modu)",
        "etki": "150 km/s sahte hiz verisiyle kavsak kontrolorunun cokmesi, trafik isiklainin kontrolsuz yanip sonmesi",
        "oneri": "Sensor girdilerinde fiziksel olarak mumkun olmayan degerler icin sinir kontrolleri uygulanmali, outlier tespiti icin istatistiksel filtreler kullanilmalidir.",
    },
    "ATTACK_V2X_V2V": {
        "baslik": "V2V Sybil Saldirisi - Sahte Acil Fren Sinyali ile Zincirleme Kaza",
        "zafiyet_adi": "V2V Haberlesme Kimlik Sahteciligi (CWE-290 + CWE-345)",
        "cvss_skor": "9.3",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1200",     "taktor": "Initial Access",    "teknik": "Hardware Additions"},
            {"id": "T1565.002", "taktor": "Impact",            "teknik": "Transmitted Data Manipulation"},
            {"id": "T1499",     "taktor": "Impact",            "teknik": "Endpoint Denial of Service"},
            {"id": "T1557",     "taktor": "Credential Access", "teknik": "Adversary-in-the-Middle"},
        ],
        "poc": "$ nc localhost 444\nATTACK_V2X_V2V\n# 1. hedef_arac V2X anteni ele gecirildi\n# 2. Zombi arac 50m yaricapindaki tum araclara\n#    sahte Acil Fren sinyali yayinladi\n# 3. Komsu araclar panik freni yaparak zincirleme\n#    kazaya neden oldu",
        "etki": "Hedef aracin V2X anteninin ele gecirilerek cevredeki tum otonom araclara sahte acil fren sinyali yayilmasi ve zincirleme trafik kazasina yol acilmasi",
        "oneri": "V2V mesajlari ETSI ITS-G5 veya IEEE 802.11p standartlarina uygun PKI altyapiyla imzalanmali, arac sertifikalari CRL ile dogrulanmalidir.",
    },
    "ATTACK_V2X_V2I": {
        "baslik": "V2I Altyapi Zehirlenmesi - Sahte OBU Verisiyle Akilli Kavsak Kilitleme",
        "zafiyet_adi": "V2I Altyapi Protokolunde Kimlik Dogrulamasi Eksikligi (CWE-306 + CWE-290)",
        "cvss_skor": "9.1",
        "cvss_vektor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:H/A:H",
        "risk_seviyesi": "KRITIK",
        "mitre": [
            {"id": "T1200",     "taktor": "Initial Access", "teknik": "Hardware Additions"},
            {"id": "T1565.002", "taktor": "Impact",         "teknik": "Transmitted Data Manipulation"},
            {"id": "T1498",     "taktor": "Impact",         "teknik": "Network Denial of Service"},
        ],
        "poc": "$ nc localhost 444\nATTACK_V2X_V2I\n# 1. Arac ici unite (OBU) ele gecirildi\n# 2. Kavsak RSU'suna sahte Acil Durum / Yuksek Hiz verisi gonderildi\n# 3. Akilli kavsak sahte veriye guvenerek kilitlendi",
        "etki": "Arac ici unitenin (OBU) ele gecirilerek kavsak RSU'suna sahte acil durum verisi iletilmesi ve akilli kavsak sisteminin kilitlenmesi",
        "oneri": "V2I altyapisinda RSU'lar yalnizca sertifikali OBU'lardan gelen imzali mesajlari kabul etmeli, anormallik tespiti icin davranissal analiz uygulanmalidir.",
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
            return resp.json().get("response", "").strip()
        except Exception as e:
            return f"[LLM bağlantı hatası: {e}]"

    def _giris_ozeti(self, scenario_data, logs):
        prompt = f"""Sen kıdemli bir siber güvenlik analistisin. Aşağıdaki V2X sızma testi için 3-4 cümlelik Türkçe, akademik ve resmi bir GİRİŞ paragrafı yaz. 
PENTEZ-AI'ın ne olduğunu, V2X haberleşmesinin önemini ve bu testin amacını belirt. 
Senaryo: {scenario_data['baslik']}
Sadece paragraf metnini yaz, başlık veya ek açıklama ekleme."""
        return self._llm_yorum(prompt, 300)

    def _yonetici_ozeti(self, scenario_data, logs, durum):
        log_str = "\n".join(logs[-10:]) if logs else "Log verisi yok"
        prompt = f"""Sen kıdemli bir siber güvenlik analistisin. Aşağıdaki sızma testi için teknik olmayan bir dille 4-5 cümlelik Türkçe YÖNETİCİ ÖZETİ yaz.
Saldırı nasıl gerçekleşti, trafik ve can güvenliğine etkisi ne oldu, sonuç ne oldu - bunları özetle.
Senaryo: {scenario_data['baslik']}
Nihai Durum: {durum}
Loglar: {log_str}
Sadece paragraf metnini yaz."""
        return self._llm_yorum(prompt, 400)

    def _zafiyet_detay(self, scenario_data, logs):
        log_str = "\n".join(logs) if logs else "Log verisi yok"
        prompt = f"""Aşağıdaki zafiyet için 3-4 cümlelik Türkçe teknik AÇIKLAMA yaz. 
Zafiyetin neden oluştuğunu, nasıl istismar edildiğini ve sistemdeki köken nedenini belirt.
Zafiyet: {scenario_data['zafiyet_adi']}
Senaryo: {scenario_data['baslik']}
Log Kanıtları: {log_str}
Sadece açıklama metnini yaz, başlık ekleme."""
        return self._llm_yorum(prompt, 350)

    def _sonuc(self, scenario_data, durum):
        prompt = f"""Aşağıdaki V2X sızma testi için 3-4 cümlelik Türkçe, resmi ve akademik bir SONUÇ paragrafı yaz.
Testin önemini, bulunan zafiyetin kritikliğini ve alınması gereken önlemlerin aciliyetini vurgula.
Senaryo: {scenario_data['baslik']}
Nihai Durum: {durum}
Sadece sonuç metnini yaz."""
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

        # Risk seviyesine göre sembol
        risk_icon = {"KRİTİK": "🔴", "YÜKSEK": "🟠", "ORTA": "🟡", "DÜŞÜK": "🟢"}.get(sc["risk_seviyesi"], "⚪")

        # MITRE tablosu
        mitre_tablo = "\n".join([
            f"| {m['id']} | {m['taktor']} | {m['teknik']} |"
            for m in sc["mitre"]
        ])

        # Log tablosu
        log_listesi = "\n".join([f"- `{l}`" for l in logs]) if logs else "- *Log kaydı bulunamadı*"

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
| Senaryo | `{scenario}` |
| Nihai Durum | **{durum}** |

---

## 2. İçindekiler

- 3. Giriş
- 4. Kapsam
- 5. Yönetici Özeti (Executive Summary)
- 6. Zafiyetler ve Detaylı Analiz
- 7. Kanıtlar (Proof of Concept)
- 8. MITRE ATT&CK Özeti
- 9. Öneriler
- 10. Sonuç

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
| 🔴 Kritik | {1 if sc['risk_seviyesi'] == 'KRİTİK' else 0} |
| 🟠 Yüksek | {1 if sc['risk_seviyesi'] == 'YÜKSEK' else 0} |
| 🟡 Orta | 0 |
| 🟢 Düşük | 0 |
| **Toplam** | **1** |

---

## 6. Zafiyetler ve Detaylı Analiz

### {risk_icon} Z-01 — {sc['zafiyet_adi']}

| Alan | Değer |
|------|-------|
| Risk Seviyesi | **{sc['risk_seviyesi']}** |
| CVSS v3.1 Skoru | **{sc['cvss_skor']} / 10.0** |
| CVSS Vektörü | `{sc['cvss_vektor']}` |
| CWE | `{sc['zafiyet_adi'].split("(")[-1].replace(")", "") if "CWE" in sc['zafiyet_adi'] else "N/A"}` |

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

## 8. MITRE ATT&CK Özeti

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
                    txt = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("PENTEZ-AI", ParagraphStyle("cover_dj", fontName=FONT_BOLD,
                                fontSize=28, textColor=RED, alignment=TA_CENTER)))
        story.append(Paragraph("Sizmaaa Testi Raporu", ParagraphStyle("cover2_dj", fontName=FONT_NORMAL,
                                fontSize=18, textColor=DARK, alignment=TA_CENTER)))
        story.append(HRFlowable(width="100%", thickness=2, color=RED, spaceAfter=10))
        story.append(Spacer(1, 0.5*cm))

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
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#eeeeee"), spaceBefore=8))
                story.append(Paragraph(line[3:], s_h1))
            elif line.startswith("### "):
                story.append(Paragraph(line[4:], s_h2))
            elif line.startswith("# "):
                pass  # Ana başlık zaten kapakta
            elif line.startswith("---"):
                story.append(HRFlowable(width="100%", thickness=0.5,
                                        color=colors.HexColor("#cccccc"), spaceBefore=4, spaceAfter=4))
            elif line.startswith("- ") or line.startswith("* "):
                txt = line[2:].replace("`", "").replace("**", "")
                story.append(Paragraph(f"• {txt}", s_body))
            elif line.strip().startswith("**") and line.strip().endswith("**"):
                story.append(Paragraph(f"<b>{line.strip()[2:-2]}</b>", s_body))
            elif line.strip():
                clean = (line.strip()
                         .replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;"))
                # Bold
                import re
                clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', clean)
                clean = re.sub(r'`(.+?)`', r'<font name="Courier" size="9">\1</font>', clean)
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
            f"PENTEZ-AI Otomatik Sızma Testi Raporu — {datetime.now().strftime('%Y-%m-%d')} — GİZLİ",
            s_footer
        ))

        doc.build(story)
        print(f"✅ [RAPORLAMA] PDF raporu oluşturuldu: {pdf_path}")
        return pdf_path