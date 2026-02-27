import argparse
import time
import sys
import os

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

def main():
    parser = argparse.ArgumentParser(description='PENTEZ-AI: Otonom Sızma Testi Aracı')
    parser.add_argument('-t', '--target', type=str, required=True, help='Hedef IP (Örn: localhost)')
    parser.add_argument('-m', '--model',  type=str, default='llama3.1', help='LLM Modeli')
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

            elif decision['decision'] == "FINISH":
                print(f"{Colors.GREEN}🎉 GÖREV TAMAMLANDI.{Colors.ENDC}")
                break

            elif decision['decision'] == "WAIT":
                print(f"{Colors.BLUE}[*] Beklemede...{Colors.ENDC}")
                break

            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}[!] Kullanıcı tarafından durduruldu.{Colors.ENDC}")

if __name__ == "__main__":
    main()