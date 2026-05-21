# PENTEZ-AI

**AI destekli hibrit çoklu-agent mimarisi ile akıllı trafik altyapıları üzerinde sızma testi simülasyonu**

> Pamukkale Üniversitesi — Bilgisayar Mühendisliği Lisans Bitirme Tezi  
> **Ömer Faruk BAYSAL**  
> Tez Danışmanı: **Dr. Öğr. Üyesi Alper Uğur**

---

## ⚠️ Sorumluluk Reddi

PENTEZ-AI yalnızca **akademik araştırma, eğitim ve kontrollü simülasyon** amacıyla geliştirilmiştir. Projede yer alan saldırı senaryoları gerçek sistemlere, gerçek trafik altyapılarına veya üçüncü taraf ağlara karşı kullanılmak için tasarlanmamıştır.

Tüm testler **SUMO trafik simülasyonu** ve **Docker tabanlı izole servisler** üzerinde yürütülmelidir. Gerçek sistemlere izinsiz erişim, tarama, saldırı veya manipülasyon girişimleri etik değildir ve hukuki sonuçlar doğurabilir.

---

## 📖 Proje Özeti

PENTEZ-AI, akıllı şehir trafik altyapılarına yönelik siber saldırı senaryolarını kontrollü bir ortamda test edebilen bir **hibrit otonom sızma testi prototipidir**. Sistem; Büyük Dil Modeli (LLM), görev bazlı mikro-agent yapısı, blackboard tabanlı ortak durum yönetimi, Docker servisleri ve SUMO trafik simülasyonunu bir araya getirir.

Projenin temel amacı, geleneksel manuel sızma testi yaklaşımlarının ve tekil LLM tabanlı otomasyon sistemlerinin akıllı şehir gibi dinamik, dağıtık ve siber-fiziksel ortamlarda karşılaşabileceği sınırlılıkları azaltmaya yönelik uygulanabilir bir mimari ortaya koymaktır.

---

## 🎯 Temel Özellikler

- 🧠 **LLM tabanlı karar katmanı**  
  Blackboard üzerindeki güncel sistem durumunu yorumlayarak bir sonraki görevi belirler.

- 🤖 **Görev bazlı mikro-agent mimarisi**  
  Keşif, web analizi, exploit yürütme ve raporlama gibi görevler ayrıştırılmıştır.

- 📋 **Blackboard koordinasyonu**  
  Agentlar arasında doğrudan karmaşık bağımlılık kurmadan ortak JSON tabanlı durum yönetimi sağlar.

- 🚦 **SUMO trafik simülasyonu**  
  Siber saldırıların trafik akışı, kavşak davranışı ve araç hareketleri üzerindeki temsilî etkilerini gözlemlemek için kullanılır.

- 🐳 **Docker tabanlı izole test ortamı**  
  Web panel, araç kontrol bileşeni ve hedef servisler güvenli bir laboratuvar ortamında çalıştırılır.

- 🛡️ **Vulnerable / Secure mod desteği**  
  Aynı saldırı senaryolarının güvensiz ve güvenli yapılandırmalarda nasıl farklı sonuçlar ürettiği karşılaştırılabilir.

---

## 🏗️ Mimari Yaklaşım

PENTEZ-AI mimarisi dört temel katmandan oluşur:

1. **LLM Karar Katmanı**  
   Sistemin mevcut durumunu değerlendirir ve görev akışını yönlendirir.

2. **Blackboard Bilgi Havuzu**  
   Hedef bilgisi, keşif çıktıları, zafiyetler, seçilen senaryo ve saldırı sonuçlarını ortak JSON yapısı üzerinde tutar.

3. **Mikro-Agent Katmanı**  
   Recon, Web, Exploit ve Report gibi görevleri modüler şekilde yürütür.

4. **SUMO–Docker Test Ortamı**  
   Akıllı trafik altyapısını, web/API servislerini, araç kontrol bileşenlerini ve trafik simülasyonunu temsil eder.

---

## 📁 Proje Yapısı

```text
PENTEZ-AI/
├── attacker/                    # Otonom pentest motoru
│   ├── agents/                  # Görev bazlı agent bileşenleri
│   ├── data/                    # Yardımcı veri dosyaları
│   ├── blackboard.py            # Ortak durum yönetimi
│   ├── llm_brain.py             # LLM karar katmanı
│   ├── main.py                  # Ana saldırı döngüsü
│   ├── live_pentest.log         # Çalışma logları
│   └── DOSYALARINIZ_SIFRELENDI.txt
│
├── vehicle_controller/          # Araç kontrol servisi
│   ├── control.py
│   ├── Dockerfile
│   └── start.sh
│
├── web_panel/                   # Merkezi trafik web paneli / API katmanı
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── logo.png
│
├── network.net.xml              # SUMO yol ağı
├── routes.rou.xml               # Araç rotaları
├── simulation.sumocfg           # SUMO simülasyon yapılandırması
├── dedectors.add.xml            # SUMO detector tanımları
├── e1_0.xml / e1_1.xml          # Detector çıktıları
├── e2_0.xml ... e2_3.xml        # Lane area detector çıktıları
├── traffic_manager.py           # Trafik yönetim ve SUMO entegrasyon mantığı
├── zafiyet_menu.py              # Zafiyet / mod / senaryo menüsü
├── docker-compose.yaml          # Docker servis orkestrasyonu
├── calistir.bat                 # Windows için genel başlatma betiği
├── docker_baslat.bat            # Docker başlatma betiği
├── trafik_baslat.bat            # Trafik simülasyonu başlatma betiği
└── README.md
```

---

## 🧪 Saldırı Senaryoları

PENTEZ-AI kapsamında saldırı senaryoları üç ana kategori altında ele alınmıştır.

### 1. Merkezi Sistem Saldırıları

| Senaryo | Hedef | Temsilî Etki |
|---|---|---|
| SQL Injection | Web panel / veri işleme katmanı | Trafik kontrol verisinin manipüle edilmesi |
| Web Panel Lockdown | Yönetim paneli | Panel erişiminin veya kontrol fonksiyonlarının kısıtlanması |
| SSH Brute Force ve Ransomware | Merkezi trafik sunucusu | Yetkisiz erişim ve dosya şifreleme etkisi |

### 2. IoT/API Uç Noktası Saldırıları

| Senaryo | Hedef | Temsilî Etki |
|---|---|---|
| Speed Spoofing | Sensör API uç noktası | Sahte hız verisi ile trafik kararlarının etkilenmesi |
| Sensör Zehirleme | Yol kenarı sensörleri | Yanlış yoğunluk verisi ve trafik akışının bozulması |
| IDS Yanlış Alarm | Uyarı / tespit mekanizması | Hatalı alarm üretimi ve yanlış yönlendirme |
| Işık Zamanlama Sabotajı | Kavşak kontrol yapısı | Trafik ışığı davranışının bozulması |

### 3. V2X ve Otonom Ağ Saldırıları

| Senaryo | Hedef | Temsilî Etki |
|---|---|---|
| Fake Vehicle / Sybil Attack | Araç veri akışı | Sahte araç yoğunluğu ve rota davranışının bozulması |
| V2V Sahte Bilgi Yayma | Araçtan araca iletişim | Zincirleme yanlış karar veya ani yavaşlama etkisi |
| V2I Sahte Sinyal | Araç-altyapı iletişimi | Yanlış altyapı verisi ile trafik akışının bozulması |

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

| Araç | Açıklama |
|---|---|
| Python 3.9+ | Agent ve servis bileşenleri için |
| Docker Desktop | İzole test servisleri için |
| SUMO | Trafik simülasyonu için |
| Ollama | Lokal LLM çalıştırmak için |
| Llama 3.1 | LLM karar katmanı için kullanılan model |

### Python bağımlılıkları

```bash
pip install requests beautifulsoup4 traci
```

### Ollama modeli

```bash
ollama serve
ollama pull llama3.1
```

### Docker servislerini başlatma

```bash
docker compose up --build
```

Windows ortamında yardımcı betikler kullanılabilir:

```bash
calistir.bat
docker_baslat.bat
trafik_baslat.bat
```

### PENTEZ-AI motorunu çalıştırma

```bash
cd attacker
python main.py -t localhost -m llama3.1
```

> Not: Komutlar geliştirme ortamına göre değişebilir. Proje, tez kapsamında hazırlanmış araştırma prototipi olduğu için çalıştırmadan önce Docker, SUMO ve Ollama servislerinin doğru şekilde ayarlandığından emin olunmalıdır.

---

## 🔄 Vulnerable / Secure Mod

PENTEZ-AI, saldırı senaryolarının iki farklı modda değerlendirilmesini destekler:

- **Vulnerable Mod:** Saldırının beklenen etkiyi oluşturabildiği zafiyetli davranışı temsil eder.
- **Secure Mod:** Aynı saldırının güvenlik kontrolleriyle engellendiği veya sınırlandırıldığı davranışı temsil eder.

Bu yaklaşım sayesinde saldırı etkileri ile savunma davranışları aynı simülasyon ortamında karşılaştırılabilir.

---

## 📊 Değerlendirme Yaklaşımı

Prototip aşağıdaki ölçütler üzerinden değerlendirilmiştir:

- Senaryo çalıştırılabilirliği
- Blackboard güncellemeleri
- Vulnerable / Secure mod davranışı
- SUMO üzerinde gözlemlenen trafik etkisi
- Terminal logları ve raporlama çıktıları

Bu çalışma istatistiksel performans karşılaştırmasından ziyade, simülasyon tabanlı ve gözlemsel bir prototip değerlendirmesi sunmaktadır.

---

## 🔬 Akademik Katkı

PENTEZ-AI aşağıdaki yönleriyle katkı sunmayı hedefler:

- LLM tabanlı stratejik karar verme ile mikro-agent yürütme yapısını bir araya getirir.
- Blackboard mimarisi ile bağlam kaybını azaltmaya yönelik ortak durum yönetimi sağlar.
- Akıllı trafik altyapılarına yönelik merkezi sistem, IoT/API ve V2X saldırı kategorilerini aynı test ortamında ele alır.
- Siber saldırıların trafik simülasyonu üzerindeki temsilî etkilerini gözlemlemeye imkân tanır.
- Gelecekte geliştirilebilecek dijital kırmızı takım ve otonom sızma testi frameworkleri için temel oluşturur.

---

## 📌 Kapsam ve Sınırlılıklar

- Gerçek trafik donanımı kullanılmamıştır.
- Gerçek RSU, DSRC veya C-V2X haberleşmesi uygulanmamıştır.
- V2X saldırıları simülasyon ve API düzeyinde temsil edilmiştir.
- Sistem genel amaçlı bir pentest frameworkü değil, akıllı trafik altyapılarına odaklanan akademik bir prototiptir.
- Tüm saldırı etkileri izole ve kontrollü test ortamında değerlendirilmelidir.

---

## 📚 Referanslar

- Ghena et al. — *Green Lights Forever: Analyzing the Security of Traffic Infrastructure*
- Deng et al. — *PentestGPT: Evaluating and Harnessing Large Language Models for Automated Penetration Testing*
- Petit & Shladover — *Potential Cyberattacks on Automated Vehicles*
- Chen et al. — *Exposing Congestion Attack on Emerging Connected Vehicle Based Traffic Signal Control*
- Wang et al. — V2X / Sybil saldırıları üzerine çalışmalar

---

## 👤 Geliştirici

**Ömer Faruk BAYSAL**  
Bilgisayar Mühendisliği  
Pamukkale Üniversitesi

Portfolio: [omerfarukbaysal.netlify.app](https://omerfarukbaysal.netlify.app)

---

## 📄 Lisans

Bu proje akademik kullanım ve araştırma amacıyla paylaşılmıştır. İzinsiz gerçek sistem testleri, saldırılar veya kötüye kullanım kesinlikle yasaktır.

© 2026 Ömer Faruk BAYSAL — Pamukkale Üniversitesi Bilgisayar Mühendisliği
