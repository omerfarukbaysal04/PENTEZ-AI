# PENTEZ-AI 🔐
### Akıllı Şehir Sistemlerinde Yapay Zeka Güdümlü Hibrit Çoklu Agent Mimarisi Kullanarak Sızma Testi

> **Pamukkale Üniversitesi — Bilgisayar Mühendisliği Lisans Tezi**  
> Ömer Faruk BAYSAL 
---

## ⚠️ Sorumluluk Reddi

Bu proje **yalnızca akademik araştırma amaçlıdır.** Tüm saldırı senaryoları kontrollü bir simülasyon ortamında (SUMO + Docker) gerçekleştirilmektedir. Gerçek sistemlere, altyapılara veya ağlara karşı kullanılması **kesinlikle yasaktır ve etik değildir.** Proje, güvenlik açıklarını tespit ederek savunma mekanizmalarının geliştirilmesine katkı sağlamak amacıyla hazırlanmıştır.

---

## 📖 Proje Hakkında

PENTEZ-AI, akıllı şehir trafik altyapılarına yönelik sızma testini **otonom** olarak gerçekleştirebilen hibrit bir sistemdir. Geleneksel manuel pentest yöntemlerinin yetersiz kaldığı dinamik ve dağıtık akıllı şehir ortamlarında, **LLM + Çoklu Agent Sistemi (MAS) + Blackboard** mimarisini bir araya getirir.

### !!!BU PROJE AKTİF OLARAK GELİŞTİRİLMEYE DEVAM EDİLMEKTEDİR!!!
### Temel Özellikler

- 🧠 **LLM Tabanlı Stratejik Karar Verme** — Llama 3.1 ile otonom saldırı planlaması
- 🤖 **Mikro-Ajan Mimarisi** — Recon, Web Analysis, Exploit ajanları
- 📋 **Blackboard Koordinasyonu** — Ajanlar arası bağlam kaybı olmadan bilgi paylaşımı
- 🛡️ **VULNERABLE / SECURE Mod** — Saldırı ve savunma senaryolarını karşılaştırmalı test etme
- 🚦 **SUMO Simülasyonu** — Gerçekçi akıllı şehir trafik ortamı

---

## 🏗️ Mimari

```
PENTEZ-AI
├── attacker/                   # Otonom Pentest Motoru
│   ├── agents/
│   │   ├── recon_agent.py      # Port tarama ve keşif
│   │   ├── web_agent.py        # Web servis analizi
│   │   └── exploit_agent.py    # SQL Injection saldırısı
│   ├── blackboard.py           # Ortak hafıza (Blackboard mimarisi)
│   ├── llm_brain.py            # LLM stratejik karar mekanizması
│   └── main.py                 # CLI giriş noktası
│
├── web_panel/                  # Hedef Sistem (Zafiyetli Web Paneli)
│   ├── app.py                  # Flask uygulaması
│   ├── Dockerfile
│   └── requirements.txt
│
├── sumo-config/                # SUMO Simülasyon Dosyaları
│   ├── network.net.xml         # Yol ağı
│   ├── routes.rou.xml          # Araç rotaları
│   ├── simulation.sumocfg      # Simülasyon ayarları
│   └── dedectors.add.xml       # Dedektörler
│
├── traffic_manager.py          # SUMO TraCI köprüsü + Komut sunucusu
├── docker-compose.yaml         # Servis orkestrasyon
└── calistir.bat                # Windows başlatma scripti
```

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

| Araç | Versiyon | Link |
|------|----------|------|
| Python | 3.9+ | [python.org](https://python.org) |
| Docker Desktop | Son sürüm | [docker.com](https://docker.com) |
| SUMO | 1.18+ | [eclipse.dev/sumo](https://eclipse.dev/sumo) |
| Ollama | Son sürüm | [ollama.ai](https://ollama.ai) |
| Llama 3.1 | 8B | `ollama pull llama3.1` |

### Python Bağımlılıkları

```bash
pip install requests beautifulsoup4 traci
```

### Adım Adım Başlatma

**1. Ollama'yı başlat:**
```bash
ollama serve
ollama pull llama3.1
```

**2. Güvenlik modunu seç** — `docker-compose.yaml` dosyasında:
```yaml
environment:
  SECURITY_MODE: VULNERABLE   # VULNERABLE veya SECURE
```

**3. Doğrudan "calistir.bat" dosyasını çalıştır**
```bash
Bu sayede docker ve diğer ortamlar otomatik çalışır ve açılır.
```

**4. PENTEZ-AI'ı çalıştır:**
```bash
cd attacker
python main.py -t localhost -m llama3.1
```

> Windows kullanıcıları için `calistir.bat` adımları 3-5'i otomatik yapar.

---

## 🎯 Saldırı Senaryoları

### Kategori 1 — Araç Odaklı Saldırılar

| # | Saldırı | Hedef | Zafiyet | Etki |
|---|---------|-------|---------|------|
| 1 | **Ransomware** | `vehicle_controller` | Zayıf SSH şifresi | Araç kontrolü kilitleme |
| 2 | **Speed Spoof** | `vehicle_controller` | Kimlik doğrulamasız soket | Ani hızlanma/yavaşlama |
| 3 | **Movement Hack** | `vehicle_controller` | Kimlik doğrulamasız soket | Şerit değiştirme, rota değişimi |

### Kategori 2 — Altyapı Saldırıları

| # | Saldırı | Hedef | Zafiyet | Etki |
|---|---------|-------|---------|------|
| 4 | **Traffic Light Manipulation** | `traffic_controller` | SQL Injection (Web Panel) | Tüm ışıkları yeşil yapma |
| 5 | **IoT/API Data Poisoning** | `sensor_api_service` | Kimlik doğrulamasız API | Sahte trafik yoğunluğu verisi |
| 6 | **Fake Vehicle** | SUMO Ağı | Ağda kimlik doğrulama yok | Hayalet araç spawn etme |
| 7 | **Fake Speed Limit** | `RSU_Unit` | Varsayılan şifre | Hız limiti manipülasyonu |

### Demo Saldırısı (SQL Injection → Traffic Light Manipulation)

PENTEZ-AI'ın otonom çalışma akışı:

```
ADIM 1 [RECON]    → Port taraması → Port 5000 bulundu
ADIM 2 [ANALYSIS] → Web paneli analizi → Admin login formu tespit edildi
ADIM 3 [EXPLOIT]  → SQL Injection → Panele sızıldı → HACK_LIGHTS komutu
SONUÇ             → Tüm kavşak ışıkları yeşile döndü (SUMO'da görünür)
```

---

## 🛡️ VULNERABLE vs SECURE Mod

Sistem iki modda çalışabilir:

### VULNERABLE Mod
```
SQL Injection Payload: ' OR '1'='1
↓
Web panel bypass edilir
↓  
Saldırgan panele erişir
↓
Trafik ışıkları hacklenir
```

### SECURE Mod
```
SQL Injection Payload: ' OR '1'='1
↓
is_sql_injection() fonksiyonu tespit eder
↓
[ALERT] Şüpheli payload engellendi
↓
[LOG] IP adresi kayıt altına alındı
```

Mod değişimi `docker-compose.yaml` dosyasındaki tek bir satırla yapılır:
```yaml
SECURITY_MODE: VULNERABLE  # → SECURE olarak değiştir
```

---

## 📊 Sistem Bileşenleri

### Blackboard Mimarisi
Ajanlar birbirleriyle doğrudan değil, ortak bir bilgi tahtası (blackboard) üzerinden iletişim kurar. Bu sayede:
- Bağlam kaybı (context loss) engellenir
- Her ajan kendi görevine odaklanır
- LLM gereksiz log gürültüsünden etkilenmez

### LLM Karar Mekanizması
```
Blackboard Özeti → Llama 3.1 → JSON Karar
{"decision": "ATTACK_SQL", "reason": "..."}
```

Karar hiyerarşisi (öncelik sırasıyla):
1. `mission_status == BLOCKED/SUCCESS` → **FINISH**
2. `phase == EXPLOIT` → **ATTACK_SQL**
3. `phase == ANALYSIS` → **ANALYZE_WEB**
4. `phase == RECON` → **SCAN_PORTS**

---

## 📚 Referanslar

- Ghena et al. (2014) — Green Lights Forever: Analyzing the Security of Traffic Infrastructure
- Deng et al. (2024) — PentestGPT: Evaluating and Harnessing LLMs for Automated Penetration Testing
- Petit & Shladover (2016) — Remote Attacks on Automated Vehicle Sensors
- Al-Turjman et al. (2023) — Smart City Security and Privacy: A Comprehensive Review

---

## 📄 Lisans

Bu proje **yalnızca akademik kullanım** içindir.  
© 2025 Ömer Faruk BAYSAL — Pamukkale Üniversitesi Bilgisayar Mühendisliği
