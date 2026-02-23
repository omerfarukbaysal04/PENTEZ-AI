import socket
import time
from concurrent.futures import ThreadPoolExecutor

class ReconAgent:
    def __init__(self):
        # Hız kazanmak için sadece kritik portları tarayalım
        # 5000: Bizim Web Paneli
        # 8813: SUMO
        # 80/443: Web
        # 22: SSH
        self.target_ports = [21, 22, 80, 443, 3306, 5000, 8080, 8813]
    
    def scan_port(self, ip, port):
        """Tek bir portu kontrol eder"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5) # 0.5 saniye bekle, cevap yoksa kapalıdır
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return port
        except:
            pass
        return None

    def run(self, blackboard):
        """Ajanın ana çalışma fonksiyonu"""
        state = blackboard.read_state()
        target_ip = state.get("target_ip", "localhost")
        
        print(f"\n🔍 [RECON] Port taramasi baslatiliyor: {target_ip}")
        print(f"🔍 [RECON] Hedef Portlar: {self.target_ports}")
        
        open_ports = []
        
        # Hızlı olması için Threading (Paralel Tarama) kullanıyoruz
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(lambda p: self.scan_port(target_ip, p), self.target_ports)
            
        for port in results:
            if port:
                open_ports.append(port)
                print(f"✅ [RECON] AÇIK PORT BULUNDU: {port}")

        # SONUCU BLACKBOARD'A YAZ
        if open_ports:
            blackboard.update_key("open_ports", open_ports)
            
            # --- BU SATIRI EKLE (KRİTİK HAMLE) ---
            # Fazı 'RECON'dan 'ANALYSIS'e çekiyoruz.
            # Böylece LLM artık geri dönüp tarama yapmayacak.
            blackboard.update_key("current_phase", "ANALYSIS")
            # -------------------------------------
            
            print(f"📋 [RECON] Blackboard guncellendi: Faz -> ANALYSIS")
        else:
            print("❌ [RECON] Hicbir acik port bulunamadi.")

        time.sleep(1) # İşlem bitti simülasyonu