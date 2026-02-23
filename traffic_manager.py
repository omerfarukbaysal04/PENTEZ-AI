import traci
import time
import socket
import threading
import sys
import os
import signal

# --- AYARLAR ---
SUMO_CMD = ["sumo-gui", "-c", "simulation.sumocfg", "--start"]

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9999

# Fidye notu içeriği
RANSOM_NOTE = """
╔══════════════════════════════════════════════════════════╗
║              !!!  UYARI: SİSTEM ŞİFRELENDİ  !!!         ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Tüm trafik kontrol dosyalarınız şifrelenmiştir.         ║
║  Sistemi geri almak için 48 saat içinde                   ║
║  iletişime geçin: darkweb@ransomgroup.onion              ║
║                                                          ║
║  Ödeme yapılmazsa tüm veriler silinecektir.              ║
║                                                          ║
║  ID: TRF-2026-SUMO-7749                                  ║
╚══════════════════════════════════════════════════════════╝
"""

command_queue = []

# Ransomware tetiklendiğinde True olur — simülasyon döngüsünü kırar
ransomware_triggered = False


def drop_ransom_note():
    """Fidye notunu masaüstü konumuna bırakır"""
    # Windows masaüstü yolu
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    note_path = os.path.join(desktop, "DOSYALARINIZ_SIFRELENDI.txt")

    # Masaüstü yoksa proje klasörüne yaz
    if not os.path.exists(desktop):
        note_path = "DOSYALARINIZ_SIFRELENDI.txt"

    try:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(RANSOM_NOTE)
        print(f"[RANSOMWARE] Fidye notu bırakıldı: {note_path}")
    except Exception as e:
        print(f"[RANSOMWARE] Fidye notu yazılamadı: {e}")


def execute_ransomware():
    """
    Ransomware saldırısını uygular:
    1. SUMO'daki tüm araçları durdurur (kilitler)
    2. Fidye notunu bırakır
    3. traffic_manager sürecini sonlandırır (pkill etkisi)
    """
    global ransomware_triggered
    ransomware_triggered = True

    print("=" * 60)
    print("[RANSOMWARE] SALDIRI BAŞLADI!")
    print("=" * 60)

    # Adım 1: SUMO'daki tüm araçları durdur
    try:
        vehicle_ids = traci.vehicle.getIDList()
        if vehicle_ids:
            for vid in vehicle_ids:
                traci.vehicle.setSpeed(vid, 0)       # Hızı sıfırla
                traci.vehicle.setColor(vid, (139, 0, 255, 255))  # Morya boya (ransomware rengi)
            traci.simulationStep()  # Değişikliği uygula
            print(f"[RANSOMWARE] {len(vehicle_ids)} araç kilitlendi ve mora boyandı.")
        else:
            print("[RANSOMWARE] Sahadaki araç yok, devam ediliyor.")
    except Exception as e:
        print(f"[RANSOMWARE] Araç kilitleme hatası: {e}")

    # Adım 2: Trafik ışıklarını da kapat (kırmızı)
    try:
        tl_ids = traci.trafficlight.getIDList()
        for tl in tl_ids:
            current = traci.trafficlight.getRedYellowGreenState(tl)
            traci.trafficlight.setRedYellowGreenState(tl, "r" * len(current))
        print(f"[RANSOMWARE] {len(tl_ids)} kavşak kırmızıya alındı.")
    except Exception as e:
        print(f"[RANSOMWARE] Işık kilitleme hatası: {e}")

    # Adım 3: Fidye notunu bırak
    drop_ransom_note()

    # Adım 4: Simülasyonu kapat ve süreci öldür
    print("[RANSOMWARE] Sistem kapatılıyor — pkill simülasyonu...")
    time.sleep(1.5)  # Efekt için kısa bekleme

    try:
        traci.close()
    except Exception:
        pass

    print("[RANSOMWARE] traffic_manager.py SONLANDIRILDI.")
    print(RANSOM_NOTE)

    # Süreci sonlandır (pkill etkisi)
    os.kill(os.getpid(), signal.SIGTERM)


def start_socket_server():
    """Arka planda Web Panelinden gelen komutları dinler"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((SERVER_HOST, SERVER_PORT))
    except OSError:
        print(f"[HATA] Port {SERVER_PORT} zaten kullanımda! Eski pencereleri kapat.")
        return

    server.listen(5)
    print(f"[SERVER] Komuta Merkezi dinliyor: port {SERVER_PORT}")

    while True:
        try:
            client, addr = server.accept()
            data = client.recv(1024).decode('utf-8')
            if data:
                print(f">>> [KOMUT ALINDI] Mesaj: {data}")
                command_queue.append(data)
                client.send(b"OK")
            client.close()
        except Exception as e:
            print(f"[HATA] Socket hatası: {e}")
            break


def run_simulation():
    # Dinleme sunucusunu arka planda başlat
    t = threading.Thread(target=start_socket_server)
    t.daemon = True
    t.start()

    print(">>> SUMO Başlatılıyor...")

    try:
        traci.start(SUMO_CMD)
    except Exception as e:
        print(f"HATA: SUMO açılamadı.\nDetay: {e}")
        input("Kapatmak için Enter'a bas...")
        sys.exit(1)

    print(">>> Sistem Aktif. Trafik Akıyor...")
    print(">>> Web Paneli artık bağlanabilir: localhost:5000")

    while True:
        try:
            # Kuyrukta bekleyen komut var mı?
            if command_queue:
                cmd = command_queue.pop(0)

                # --- TRAFİK IŞIĞI SALDIRISI ---
                if cmd == "HACK_LIGHTS":
                    try:
                        current = traci.trafficlight.getRedYellowGreenState("center")
                        traci.trafficlight.setRedYellowGreenState("center", "G" * len(current))
                        print(">>> [UYGULANDI] Tüm ışıklar YEŞİL yapıldı!")
                    except Exception as e:
                        print(f">>> [HATA] HACK_LIGHTS: {e}")

                # --- ARAÇ KİLİTLEME ---
                elif cmd == "HACK_VEHICLE":
                    try:
                        traci.vehicle.setColor("hedef_arac", (128, 0, 128, 255))
                        traci.vehicle.setSpeed("hedef_arac", 0)
                        print(">>> [UYGULANDI] Araç kilitlendi!")
                    except Exception as e:
                        print(f">>> [BASARISIZ] HACK_VEHICLE: {e}")

                # --- RANSOMWARE ---
                elif cmd == "RANSOMWARE":
                    print(">>> [KRİTİK] RANSOMWARE komutu alındı! Saldırı başlıyor...")
                    # Ayrı thread'de çalıştır ki soket cevabı gönderilsin
                    r_thread = threading.Thread(target=execute_ransomware)
                    r_thread.daemon = True
                    r_thread.start()
                    break  # Ana döngüden çık, ransomware halleder

            # Simülasyonu bir adım ilerlet
            traci.simulationStep()
            time.sleep(0.05)

        except traci.FatalTraCIError:
            print(">>> SUMO kapatıldı.")
            break
        except KeyboardInterrupt:
            print(">>> Kullanıcı tarafından durduruldu.")
            break
        except Exception as e:
            if not ransomware_triggered:
                print(f">>> Beklenmedik Hata: {e}")
            break

    if not ransomware_triggered:
        try:
            traci.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_simulation()