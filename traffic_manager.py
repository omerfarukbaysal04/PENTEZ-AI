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

RANSOM_NOTE = """
╔══════════════════════════════════════════════════════════╗
║              !!!  UYARI: SİSTEM ŞİFRELENDİ  !!!         ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Tüm trafik kontrol dosyalarınız şifrelenmiştir.         ║
║  Sistemi geri almak için 48 saat içinde                  ║
║  iletişime geçin: darkweb@ransomgroup.onion              ║
║                                                          ║
║  Ödeme yapılmazsa tüm veriler silinecektir.              ║
║                                                          ║
║  ID: TRF-2026-SUMO-7749                                  ║
╚══════════════════════════════════════════════════════════╝
"""

command_queue = []
ransomware_triggered = False


def drop_ransom_note():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    note_path = os.path.join(desktop, "DOSYALARINIZ_SIFRELENDI.txt")
    if not os.path.exists(desktop):
        note_path = "DOSYALARINIZ_SIFRELENDI.txt"
    try:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(RANSOM_NOTE)
        print(f"[RANSOMWARE] Fidye notu bırakıldı: {note_path}")
    except Exception as e:
        print(f"[RANSOMWARE] Fidye notu yazılamadı: {e}")


def execute_ransomware():
    global ransomware_triggered
    ransomware_triggered = True

    print("=" * 60)
    print("[RANSOMWARE] SALDIRI BAŞLADI!")
    print("=" * 60)

    # Adım 1: Tüm araçları durdur ve mora boya
    try:
        vehicle_ids = traci.vehicle.getIDList()
        if vehicle_ids:
            for vid in vehicle_ids:
                traci.vehicle.setSpeed(vid, 0)
                traci.vehicle.setColor(vid, (139, 0, 255, 255))
            traci.simulationStep()
            print(f"[RANSOMWARE] {len(vehicle_ids)} araç kilitlendi ve mora boyandı.")
        else:
            print("[RANSOMWARE] Sahadaki araç yok.")
    except Exception as e:
        print(f"[RANSOMWARE] Araç kilitleme hatası: {e}")

    # Adım 2: Tüm ışıkları kırmızıya al
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

    # Adım 4: Ekrana bas, SUMO ayakta kalıyor
    print("[RANSOMWARE] Sistem simüle edildi. SUMO ayakta kalıyor.")
    print(RANSOM_NOTE)
    # os.kill(os.getpid(), signal.SIGTERM)  # Devre dışı


def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((SERVER_HOST, SERVER_PORT))
    except OSError:
        print(f"[HATA] Port {SERVER_PORT} zaten kullanımda!")
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
    print(">>> Web Paneli: localhost:5000")

    TARGET_VEH = "hedef_arac"
    target_veh_seen   = False  # Araç en az bir kez sahadaydı mı?
    target_veh_active = False  # Şu an sahada mı?

    while True:
        try:
            # hedef_arac takibi
            active_vehicles = traci.vehicle.getIDList()
            if TARGET_VEH in active_vehicles:
                target_veh_seen   = True
                target_veh_active = True
            else:
                target_veh_active = False

            # Daha önce sahadaydı ama şimdi yok → rotayı tamamladı, yeniden ekle
            if target_veh_seen and not target_veh_active:
                try:
                    traci.vehicle.add(
                        TARGET_VEH,
                        routeID="rota_kurban",
                        typeID="binek",
                        depart="now",
                        departPos="base",
                        departSpeed="max"
                    )
                    traci.vehicle.setColor(TARGET_VEH, (255, 0, 255, 255))  # magenta
                    target_veh_seen   = False  # Sıfırla — tekrar görünmesini bekle
                    target_veh_active = False
                    print(f">>> [SISTEM] hedef_arac yeniden eklendi.")
                except Exception:
                    pass

            if command_queue:
                cmd = command_queue.pop(0)

                if cmd == "HACK_LIGHTS":
                    try:
                        current = traci.trafficlight.getRedYellowGreenState("center")
                        traci.trafficlight.setRedYellowGreenState("center", "G" * len(current))
                        print(">>> [UYGULANDI] Tüm ışıklar YEŞİL yapıldı!")
                    except Exception as e:
                        print(f">>> [HATA] HACK_LIGHTS: {e}")

                elif cmd == "HACK_VEHICLE":
                    try:
                        traci.vehicle.setColor("hedef_arac", (128, 0, 128, 255))
                        traci.vehicle.setSpeed("hedef_arac", 0)
                        print(">>> [UYGULANDI] Araç kilitlendi!")
                    except Exception as e:
                        print(f">>> [BASARISIZ] HACK_VEHICLE: {e}")

                elif cmd == "RANSOMWARE":
                    print(">>> [KRİTİK] RANSOMWARE komutu alındı!")
                    r_thread = threading.Thread(target=execute_ransomware)
                    r_thread.daemon = True
                    r_thread.start()
                    # break kaldırıldı — simülasyon devam ediyor

                elif cmd.startswith("SPEED_SPOOF:"):
                    # Format: SPEED_SPOOF:veh_id:speed
                    try:
                        parts   = cmd.split(":")
                        veh_id  = parts[1]
                        speed   = float(parts[2])
                        traci.vehicle.setSpeed(veh_id, speed)
                        if speed == 0:
                            traci.vehicle.setColor(veh_id, (255, 0, 0, 255))   # Kırmızı — dur
                            print(f">>> [SPEED SPOOF] {veh_id} DURDURULDU (0 m/s)")
                        elif speed > 20:
                            traci.vehicle.setColor(veh_id, (255, 165, 0, 255)) # Turuncu — tehlikeli hız
                            print(f">>> [SPEED SPOOF] {veh_id} MAKSİMUM HIZA ÇIKARILDI ({speed} m/s = ~{speed*3.6:.0f} km/h)")
                        else:
                            traci.vehicle.setColor(veh_id, (255, 255, 0, 255)) # Sarı
                            print(f">>> [SPEED SPOOF] {veh_id} hızı değiştirildi: {speed} m/s")
                    except Exception as e:
                        print(f">>> [HATA] SPEED_SPOOF: {e}")

                elif cmd.startswith("SPEED:"):
                    # Format: SPEED:veh1:50
                    try:
                        parts = cmd.split(":")
                        vid   = parts[1]
                        spd   = float(parts[2])
                        vehicle_ids = traci.vehicle.getIDList()
                        if vid in vehicle_ids:
                            traci.vehicle.setSpeed(vid, spd)
                            if spd == 0:
                                traci.vehicle.setColor(vid, (255, 0, 0, 255))   # Kırmızı — dur
                                print(f">>> [SPEED SPOOF] {vid} DURDURULDU (0 m/s) 🛑")
                            else:
                                traci.vehicle.setColor(vid, (255, 165, 0, 255)) # Turuncu — hızlandı
                                print(f">>> [SPEED SPOOF] {vid} hızı → {spd} m/s ({spd*3.6:.0f} km/h) 💨")
                        else:
                            # İlk mevcut aracı hedef al
                            if vehicle_ids:
                                vid = vehicle_ids[0]
                                traci.vehicle.setSpeed(vid, spd)
                                color = (255, 0, 0, 255) if spd == 0 else (255, 165, 0, 255)
                                traci.vehicle.setColor(vid, color)
                                print(f">>> [SPEED SPOOF] {vid} hızı → {spd} m/s ({spd*3.6:.0f} km/h)")
                            else:
                                print(f">>> [SPEED SPOOF] Sahadaki araç yok.")
                    except Exception as e:
                        print(f">>> [HATA] SPEED komutu: {e}")

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