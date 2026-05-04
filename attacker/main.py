import argparse
import time
import sys
import os

print("[BOOT] PENTEZ-AI pentest araci yukleniyor...", flush=True)

try:
    from blackboard import Blackboard
    from llm_brain import StrategicAgent
    from agents.recon_agent import ReconAgent
    from agents.web_agent import WebAnalysisAgent
    from agents.exploit_agent import ExploitAgent
    from agents.ransomware_agent import RansomwareAgent
except ImportError as e:
    print(f"HATA: Modüller bulunamadı! {e}")
    sys.exit(1)

class Colors:
    HEADER  = '\033[95m'
    BLUE    = '\033[94m'
    CYAN    = '\033[96m'
    GREEN   = '\033[92m'
    WARNING = '\033[93m'
    FAIL    = '\033[91m'
    ENDC    = '\033[0m'
    BOLD    = '\033[1m'

def print_banner():
    banner = f"""{Colors.GREEN}
    ██████╗   ███████╗  ███╗   ██╗  ████████╗  ███████╗  ███████╗            █████╗   ██╗
    ██╔══██╗  ██╔════╝  ████╗  ██║  ╚══██╔══╝  ██╔════╝  ╚════██║           ██╔══██╗  ██║
    ██████╔╝  █████╗    ██╔██╗ ██║     ██║     █████╗        ██╔╝  ██████╗  ███████║  ██║
    ██╔═══╝   ██╔══╝    ██║╚██╗██║     ██║     ██╔══╝       ██╔╝   ╚═════╝  ██╔══██║  ██║
    ██║       ███████╗  ██║ ╚████║     ██║     ███████╗  ██╗██║             ██║  ██║  ██║
    ╚═╝       ╚══════╝  ╚═╝  ╚═══╝     ╚═╝     ╚══════╝  ╚═╝╚═╝             ╚═╝  ╚═╝  ╚═╝
    {Colors.ENDC}
    {Colors.CYAN}>> Otonom Sızma Testi Aracı (Tez Projesi v1.0){Colors.ENDC}
    {Colors.CYAN}>> Mimari: Hibrit (LLM + Blackboard + Mikro-Ajanlar){Colors.ENDC}
    """
    print(banner)

SCENARIO_MAP = {
    "SSH_OPEN_WEAK_PASSWORD":       ("ATTACK_RANSOMWARE",   "Ransomware (SSH Brute Force)"),
    "UNAUTHENTICATED_SPEED_CONTROL":("ATTACK_SPEED_SPOOF",  "Speed Spoof (Hız Kontrolü Ele Geçirme)"),
    # "MOVEMENT_HACK_VULN":           ("ATTACK_MOVEMENT_HACK","Movement Hack (Rota/Serit Manipülasyonu)"),
    "LOGIN_PAGE_FOUND":             ("ATTACK_SQL",          "SQL Injection (Web Panel)"),
    "WEBPANEL_LOCKDOWN":            ("ATTACK_WEBPANEL_LOCKDOWN", "Web Panel Lockdown (Araç Kilitleme)"),
    "UNAUTHENTICATED_VEHICLE_INJECTION": ("ATTACK_FAKE_VEHICLE", "Fake Vehicle (Sybil)"),
    "UNAUTHENTICATED_SENSOR_API":   ("ATTACK_SENSOR_SPOOF", "IoT Sensör Zehirleme (Çapraz Yönlü)"),
    "IDS_FALSE_ALARM_VULN":         ("ATTACK_IDS_SPOOF_STOP", "IDS Yanlış Alarm (Acil Araç Filosu)"),
    "IDS_TIMING_VULN":              ("ATTACK_IDS_SPOOF_SPEED", "Işık Zamanlama Sabotajı (Disko Modu)"),
    "UNAUTHENTICATED_V2V_API":      ("ATTACK_V2X_V2V", "V2V Yanlış Bilgi Yayılımı (Şok Dalgası)"),
    "UNAUTHENTICATED_V2I_API":      ("ATTACK_V2X_V2I", "V2I Altyapı Zehirlenmesi (İçeriden)"),
}

SUB_SCENARIO_LABELS = {
    "UNAUTHENTICATED_SENSOR_API": "5 - IoT Sensor Zehirleme",
    "IDS_FALSE_ALARM_VULN": "6 - IDS Yanlis Alarm",
    "IDS_TIMING_VULN": "7 - Isik Zamanlama Sabotaji",
    "UNAUTHENTICATED_V2V_API": "9 - V2V Yanlis Bilgi Yayilimi",
    "UNAUTHENTICATED_V2I_API": "10 - V2I Altyapi Zehirlenmesi",
}


def describe_grouped_vulns(action, vulns):
    if action == "CATEGORY_IOT_ATTACKS":
        keys = ["UNAUTHENTICATED_SENSOR_API", "IDS_FALSE_ALARM_VULN", "IDS_TIMING_VULN"]
    elif action == "CATEGORY_V2X_ATTACKS":
        keys = ["UNAUTHENTICATED_V2V_API", "UNAUTHENTICATED_V2I_API"]
    else:
        return []

    return [SUB_SCENARIO_LABELS[key] for key in keys if key in vulns]


def ask_user_scenario(vulns):
    """Bulunan zafiyetleri göster, kullanıcıya senaryo seçtir"""
    print(f"\n{Colors.WARNING}{'='*55}{Colors.ENDC}")
    print(f"{Colors.WARNING}  RECON TAMAMLANDI — ZAFİYETLER TESPİT EDİLDİ{Colors.ENDC}")
    print(f"{Colors.WARNING}{'='*55}{Colors.ENDC}")

    available = []
    seen_actions = set()
    for vuln in vulns:
        if vuln in SCENARIO_MAP:
            action, label = SCENARIO_MAP[vuln]
            if action in seen_actions:
                continue
            seen_actions.add(action)
            available.append((vuln, action, label))

    if not available:
        print(f"{Colors.FAIL}  Exploit edilebilir zafiyet bulunamadı.{Colors.ENDC}")
        return None

    for i, (vuln, action, label) in enumerate(available, start=1):
        print(f"  [{i}] {label}")
        print(f"       Zafiyet : {vuln}")
        print(f"       Saldırı : {action}")
        grouped = describe_grouped_vulns(action, vulns)
        if grouped:
            print(f"       Acik alt senaryolar : {', '.join(grouped)}")
        print()

    print(f"{Colors.WARNING}{'='*55}{Colors.ENDC}")
    while True:
        try:
            choice = input(f"{Colors.CYAN}  Senaryo seçin (1-{len(available)}): {Colors.ENDC}").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(available):
                vuln, action, label = available[idx]
                
                if action == "CATEGORY_IOT_ATTACKS":
                    print(f"\n{Colors.WARNING}>>> IoT SENSÖR SALDIRI VEKTÖRLERİ:{Colors.ENDC}")
                    iot_options = {}
                    if "UNAUTHENTICATED_SENSOR_API" in vulns:
                        iot_options["A"] = ("ATTACK_SENSOR_SPOOF", "Çapraz Yönlü Zehirleme (Kavşak Kilitleme)")
                    if "IDS_FALSE_ALARM_VULN" in vulns:
                        iot_options["B"] = ("ATTACK_IDS_SPOOF_STOP", "IDS Yanlış Alarm Üretimi (Hız = 0 km/s)")
                    if "IDS_TIMING_VULN" in vulns:
                        iot_options["C"] = ("ATTACK_IDS_SPOOF_SPEED", "Işık Zamanlama Sabotajı (Hız = 150 km/s)")

                    for key, (_, option_label) in iot_options.items():
                        print(f"  [{key}] {option_label}")
                    
                    alt_secim = input(f"{Colors.CYAN}>>> Seçiminiz (A/B/C): {Colors.ENDC}").strip().upper()
                    
                    if alt_secim in iot_options:
                        action, label = iot_options[alt_secim]
                    else:
                        print(f"{Colors.FAIL}❌ Geçersiz veya kapalı senaryo seçimi.{Colors.ENDC}")
                        return None
                # --------------------------------------

                elif action == "CATEGORY_V2X_ATTACKS":
                    print(f"\n{Colors.WARNING}>>> V2X HABERLEŞME AĞI SALDIRILARI:{Colors.ENDC}")
                    v2x_options = {}
                    if "UNAUTHENTICATED_V2V_API" in vulns:
                        v2x_options["A"] = ("ATTACK_V2X_V2V", "V2V Yanlış Bilgi Yayılımı (Zombi Araç ile Kaza)")
                    if "UNAUTHENTICATED_V2I_API" in vulns:
                        v2x_options["B"] = ("ATTACK_V2X_V2I", "V2I Altyapı Zehirlenmesi (Kavşak Kilitleme)")

                    for key, (_, option_label) in v2x_options.items():
                        print(f"  [{key}] {option_label}")
                    
                    alt_secim = input(f"{Colors.CYAN}>>> Seçiminiz (A/B): {Colors.ENDC}").strip().upper()
                    
                    if alt_secim in v2x_options:
                        action, label = v2x_options[alt_secim]
                    else:
                        print(f"{Colors.FAIL}❌ Geçersiz veya kapalı senaryo seçimi.{Colors.ENDC}")
                        return None

                print(f"\n{Colors.GREEN}  ✅ Seçilen senaryo: {label}{Colors.ENDC}\n")
                return action
            else:
                print(f"  Geçersiz seçim. 1-{len(available)} arasında girin.")
        except (ValueError, KeyboardInterrupt):
            print(f"\n{Colors.FAIL}  İptal edildi.{Colors.ENDC}")
            return None

def main():
    parser = argparse.ArgumentParser(description='PENTEZ-AI: Otonom Sızma Testi Aracı')
    parser.add_argument('-t', '--target', type=str, required=True, help='Hedef IP (Örn: localhost)')
    parser.add_argument('-m', '--model',  type=str, default='llama3.1:latest', help='LLM Modeli')
    parser.add_argument('--verbose', action='store_true', help='Detaylı çıktı')
    args = parser.parse_args()

    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()

    print(f"{Colors.HEADER}[*] Hedef   : {args.target}{Colors.ENDC}")
    print(f"{Colors.HEADER}[*] Model   : {args.model}{Colors.ENDC}")
    print(f"{Colors.HEADER}[*] Başlatılıyor...{Colors.ENDC}\n")
    time.sleep(1)

    try:
        bb = Blackboard()
        bb.update_key("target_ip", args.target)

        print(f"{Colors.WARNING}[*] LLM Bağlantısı kontrol ediliyor...{Colors.ENDC}")
        brain             = StrategicAgent(model_name=args.model)
        recon             = ReconAgent()
        web_agent         = WebAnalysisAgent()
        exploit_agent     = ExploitAgent()
        ransomware_agent  = RansomwareAgent()

        print(f"{Colors.GREEN}[+] Blackboard hazır.{Colors.ENDC}")
        print(f"{Colors.GREEN}[+] LLM ({args.model}) aktif.{Colors.ENDC}")
        print(f"{Colors.GREEN}[+] Ajanlar yüklendi: Recon | Web | Exploit | Ransomware{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.FAIL}[!] Başlatma hatası: {e}{Colors.ENDC}")
        sys.exit(1)

    print(f"\n{Colors.BLUE}[INFO] Otonom döngü başlatıldı. Çıkmak için CTRL+C.{Colors.ENDC}\n")

    step_count = 0

    try:
        while True:
            step_count += 1
            print(f"\n{Colors.BOLD}{'='*50}{Colors.ENDC}")
            print(f"{Colors.BOLD}--- ADIM {step_count} ---{Colors.ENDC}")
            print(f"{Colors.BOLD}{'='*50}{Colors.ENDC}")

            # Python seviyesinde mission_status kontrolü (LLM'e güvenme)
            mission = bb.read_state().get("mission_status", "ONGOING")
            if mission in ("SUCCESS", "BLOCKED", "FAIL"):
                msgs = {
                    "SUCCESS": "✅ Görev başarıyla tamamlandı!",
                    "BLOCKED": "🛡️  Saldırı güvenlik sistemi tarafından engellendi.",
                    "FAIL":    "❌ Görev başarısız."
                }
                print(f"\n{Colors.GREEN}[SİSTEM] {msgs[mission]} Döngü kapatılıyor.{Colors.ENDC}")
                break

            # LLM'e sor
            print(f"{Colors.WARNING}[?] LLM Düşünüyor...{Colors.ENDC}")
            summary  = bb.get_summary_for_llm()
            print(f"{Colors.BLUE}[DEBUG] Blackboard: {summary}{Colors.ENDC}")
            decision = brain.decide_next_step(summary)

            if decision['decision'] == "ERROR":
                print(f"{Colors.FAIL}[!] HATA: {decision['reason']}{Colors.ENDC}")
                break

            print(f"{Colors.CYAN}[LLM KARARI] {decision['decision']} → {decision['reason']}{Colors.ENDC}")

            # EXPLOIT fazına ilk kez girildiyse kullanıcıya senaryo seçtir
            # Kullanıcı seçimi LLM kararını override eder
            current_phase = bb.read_state().get("current_phase", "RECON")
            selected      = bb.read_state().get("selected_scenario")

            if current_phase == "EXPLOIT" and not selected:
                # Port 5000 açıksa ve WEB analizi henüz yapılmadıysa otomatik yap
                urls = bb.read_state().get("target_urls", [])
                if not urls and 5000 in bb.read_state().get("open_ports", []):
                    print(f"{Colors.GREEN}>>> WEB ANALİZ AJANI aktif (otomatik)...{Colors.ENDC}")
                    web_agent.run(bb)

                vulns = bb.read_state().get("vulnerabilities", [])
                if vulns:
                    chosen = ask_user_scenario(vulns)
                    if chosen:
                        bb.update_key("selected_scenario", chosen)
                        decision['decision'] = chosen  # LLM kararını override et
                    else:
                        break  # kullanıcı iptal etti

            # Kararı uygula
            if decision['decision'] == "SCAN_PORTS":
                print(f"{Colors.GREEN}>>> RECON AJANI aktif...{Colors.ENDC}")
                recon.run(bb)


            elif decision['decision'] == "ANALYZE_WEB":
                print(f"{Colors.GREEN}>>> WEB ANALİZ AJANI aktif...{Colors.ENDC}")
                web_agent.run(bb)


            elif decision['decision'] == "ATTACK_SQL":
                print(f"{Colors.FAIL}>>> EXPLOIT AJANI aktif (SQL Injection)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_RANSOMWARE":
                print(f"{Colors.FAIL}>>> RANSOMWARE AJANI aktif (SSH Brute Force)...{Colors.ENDC}")
                ransomware_agent.run(bb)

            elif decision['decision'] == "ATTACK_SPEED_SPOOF":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (Speed Spoof — Hız Kontrol Ele Geçirme)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_SENSOR_SPOOF":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (IoT Sensör Zehirleme - Çapraz Yönlü)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_IDS_SPOOF_STOP":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (IDS Yanlış Alarm - Sahte Kaza Üretimi)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_IDS_SPOOF_SPEED":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (Işık Zamanlama Sabotajı - Aşırı Hız)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_V2X_V2V":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (V2X: V2V Yanlış Bilgi Yayılımı)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_V2X_V2I":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (V2X: V2I Altyapı Zehirlenmesi)...{Colors.ENDC}")
                exploit_agent.run(bb)

            # elif decision['decision'] == "ATTACK_MOVEMENT_HACK":
            #     print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (Movement Hack — Rota/Serit Manipülasyonu)...{Colors.ENDC}")
            #     exploit_agent.run(bb)

            elif decision['decision'] == "ATTACK_WEBPANEL_LOCKDOWN":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (Web Panel Lockdown — Araç Kilitleme)...{Colors.ENDC}")
                exploit_agent.run(bb)
            
            elif decision['decision'] == "ATTACK_FAKE_VEHICLE":
                print(f"{Colors.WARNING}>>> EXPLOIT AJANI aktif (Fake Vehicle — Sybil)...{Colors.ENDC}")
                exploit_agent.run(bb)

            elif decision['decision'] == "FINISH":
                print(f"{Colors.GREEN}🎉 GÖREV TAMAMLANDI.{Colors.ENDC}")
                break

            elif decision['decision'] == "WAIT":
                print(f"{Colors.BLUE}[*] Beklemede...{Colors.ENDC}")
                break

            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}[!] Kullanıcı tarafından durduruldu.{Colors.ENDC}")
    
    logs=bb.read_state().get("logs", [])

    if logs:
        print(f"\n{Colors.WARNING}{'='*55}{Colors.ENDC}")
        print(f"{Colors.WARNING}  SİMÜLASYON SONLANDI — RAPORLAMA FAZI{Colors.ENDC}")
        print(f"{Colors.WARNING}{'='*55}{Colors.ENDC}")
        
        cevap = input(f"{Colors.CYAN}>>> PENTEZ-AI Profesyonel Sızma Testi Raporu oluşturulsun mu? (e/h): {Colors.ENDC}").strip().lower()
        
        if cevap == 'e':
            print(f"\n{Colors.GREEN}>>> RAPORLAMA AJANI (LLM) aktif ediliyor...{Colors.ENDC}")
            from agents.reporting_agent import ReportingAgent
            # Ajanı başlat (Kullanıcının başta seçtiği model parametresiyle)
            raportor = ReportingAgent(model_name=args.model)
            raportor.generate_report(bb)
        else:
            print(f"{Colors.BLUE}>>> Rapor oluşturma adımı atlandı.{Colors.ENDC}")
    
    print(f"\n{Colors.HEADER}>>> PENTEZ-AI Kapatılıyor. İyi günler!{Colors.ENDC}")

if __name__ == "__main__":
    main()
