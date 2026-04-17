import traci
import time
import socket
import threading
import sys
import os
import signal
import random

# --- AYARLAR ---
SUMO_CMD = ["sumo-gui", "-c", "simulation.sumocfg", "--start"]

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 444

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
    try:
        vehicle_ids = traci.vehicle.getIDList()
        if vehicle_ids:
            for vid in vehicle_ids:
                traci.vehicle.setSpeed(vid, 0)
                traci.vehicle.setColor(vid, (139, 0, 255, 255))
            traci.simulationStep()
            print(f"[RANSOMWARE] {len(vehicle_ids)} araç kilitlendi ve mora boyandı.")
    except Exception as e:
        print(f"[RANSOMWARE] Araç kilitleme hatası: {e}")
    try:
        tl_ids = traci.trafficlight.getIDList()
        for tl in tl_ids:
            current = traci.trafficlight.getRedYellowGreenState(tl)
            traci.trafficlight.setRedYellowGreenState(tl, "r" * len(current))
        print(f"[RANSOMWARE] {len(tl_ids)} kavşak kırmızıya alındı.")
    except Exception as e:
        print(f"[RANSOMWARE] Işık kilitleme hatası: {e}")
    drop_ransom_note()
    print("[RANSOMWARE] Sistem simüle edildi. SUMO ayakta kalıyor.")
    print(RANSOM_NOTE)


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
    target_veh_seen   = False
    target_veh_active = False

    while True:
        try:
            active_vehicles = traci.vehicle.getIDList()
            if TARGET_VEH in active_vehicles:
                target_veh_seen   = True
                target_veh_active = True
            else:
                target_veh_active = False

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
                    traci.vehicle.setColor(TARGET_VEH, (255, 0, 255, 255))
                    target_veh_seen   = False
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

                elif cmd == "LOCK_VEHICLE":
                    try:
                        veh_id = "hedef_arac"
                        active = traci.vehicle.getIDList()
                        if veh_id not in active:
                            print(f">>> [LOCKDOWN] {veh_id} sahada değil, ilk araç hedef alınıyor.")
                            if active:
                                veh_id = active[0]
                        traci.vehicle.setSpeed(veh_id, 0)
                        traci.vehicle.setMaxSpeed(veh_id, 0.01)  # 0 geçersiz — 0.01 efektif olarak sıfır
                        traci.vehicle.setColor(veh_id, (255, 50, 0, 255))
                        print(f">>> [LOCKDOWN] {veh_id} UZAKTAN KİLİTLENDİ! Tum hareket komutlarina yanitsiz.")
                    except Exception as e:
                        print(f">>> [HATA] LOCK_VEHICLE: {e}")

                # elif cmd.startswith("MOVEMENT_LANE:"):
                #     # Format: MOVEMENT_LANE:veh_id:lane_index
                #     try:
                #         parts  = cmd.split(":")
                #         veh_id = parts[1]
                #         lane   = int(parts[2])
                #         active = traci.vehicle.getIDList()
                #         if veh_id not in active:
                #             print(f">>> [MOVEMENT HACK] {veh_id} sahada degil, serit degistirme iptal.")
                #         else:
                #             traci.vehicle.changeLane(veh_id, lane, 2000)
                #             traci.vehicle.setColor(veh_id, (255, 0, 255, 255))  # magenta
                #             print(f">>> [MOVEMENT HACK] {veh_id} serit {lane}'e zorla degistiriliyor!")
                #     except Exception as e:
                #         print(f">>> [HATA] MOVEMENT_LANE: {e}")

                # # elif cmd.startswith("MOVEMENT_ROUTE:"):
                #     # Format: MOVEMENT_ROUTE:veh_id:route_id
                #     # Aracın bulunduğu edge'e göre uygun kaos rotasını seç
                #     EDGE_TO_ROUTE = {
                #         "otoban_sol_1":    "rota_movement_kaos",   # otoban_sol_1 → otoban_yukari1
                #         "otoban_sag_1":    "rota_movement_kaos2",  # otoban_sag_1 → otoban_asagi_1
                #         "sehir_solgiris":  "rota_movement_kaos3",  # sehir_solgiris → ara_sol_1 → ara_merkez_1 → ara_sag_1
                #         "ara_sol_1":       "rota_movement_kaos3",
                #         "ara_merkez_1":    "rota_movement_kaos3",
                #         "ara_sol_2":       "rota_movement_kaos4",  # ara_sol_2 → sehir_solcikis → sehir_sagcikis
                #         "sehir_solcikis":  "rota_movement_kaos4",
                #     
                #   MOVEMENT HACK senaryosu şimdilik pasif, çünkü bazı durumlarda araç sahada olmayabiliyor ve bu da hatalara yol açıyor. İleride daha sağlam bir kontrol mekanizması ekleyerek tekrar aktif hale getirebilirim.
                # }
                    # try:
                    #     parts  = cmd.split(":")
                    #     veh_id = parts[1]
                    #     active = traci.vehicle.getIDList()
                    #     if veh_id not in active:
                    #         print(f">>> [MOVEMENT HACK] {veh_id} sahada degil, rota degistirme iptal.")
                    #     else:
                    #         current_edge = traci.vehicle.getRoadID(veh_id)
                    #         route_id     = EDGE_TO_ROUTE.get(current_edge, parts[2])
                    #         print(f">>> [MOVEMENT HACK] {veh_id} su an: {current_edge} → rota: {route_id}")
                    #         traci.vehicle.setRouteID(veh_id, route_id)
                    #         traci.vehicle.setColor(veh_id, (255, 0, 0, 255))
                    #         traci.vehicle.setMaxSpeed(veh_id, 50)
                    #         print(f">>> [MOVEMENT HACK] {veh_id} KAOS ROTASINA SOKULDU!")
                    # except Exception as e:
                    #     print(f">>> [HATA] MOVEMENT_ROUTE: {e}")

                elif cmd.startswith("FAKE_VEHICLE"):
                    print(f"!!! DEBUG: FAKE_VEHICLE KOMUTU ALINDI !!!")
                    try:
                        target_edge = "otoban_sag_1" 
                        
                        # 1. KRİTİK ADIM: Araca o yolu kapsayan geçici bir rota tanımla
                        # Bu, SUMO'nun "bu yol rotasında yok" hatasını engeller.
                        try:
                            traci.route.add("temp_sybil_route", [target_edge])
                        except:
                            pass # Rota zaten varsa hata vermesin

                        print(f">>> [UYGULANDI] {target_edge} yoluna bariyer kuruluyor...")

                        for i in range(50):
                            g_id = f"sybil_block_{int(time.time())}_{i}"
                            try:
                                # 2. Aracı bu geçici rota ile ekle
                                traci.vehicle.add(vehID=g_id, routeID="temp_sybil_route", typeID="binek")
                                
                                spawn_pos = 2.0 + (i * 7.0)
                                
                                # 3. Şimdi moveTo güvenle çalışacaktır
                                traci.vehicle.moveTo(g_id, target_edge + "_0", spawn_pos) 
                                
                                traci.vehicle.setSpeed(g_id, 0)
                                traci.vehicle.setColor(g_id, (128, 128, 128, 255))
                            except Exception as inner_e:
                                # print(f"Araç ekleme hatası: {inner_e}")
                                pass
                        
                        print(f">>> [TAMAMLANDI] Yol kilitlendi.")
                    except Exception as e:
                        print(f">>> [HATA] FAKE_VEHICLE: {e}")
                        
                        print(">>> [TAMAMLANDI] Yol kilitlendi. Gerçek araçlar için geçiş engellendi.")
                    except Exception as e:
                        print(f">>> [HATA] FAKE_VEHICLE: {e}")

                elif cmd.startswith("SPEED_SPOOF:"):
                    try:
                        parts  = cmd.split(":")
                        veh_id = parts[1]
                        speed  = float(parts[2])
                        traci.vehicle.setSpeed(veh_id, speed)
                        if speed == 0:
                            traci.vehicle.setColor(veh_id, (255, 0, 0, 255))
                            print(f">>> [SPEED SPOOF] {veh_id} DURDURULDU (0 m/s)")
                        elif speed > 20:
                            traci.vehicle.setColor(veh_id, (255, 165, 0, 255))
                            print(f">>> [SPEED SPOOF] {veh_id} MAKSİMUM HIZA CIKARILDI ({speed} m/s)")
                        else:
                            traci.vehicle.setColor(veh_id, (255, 255, 0, 255))
                            print(f">>> [SPEED SPOOF] {veh_id} hizi degistirildi: {speed} m/s")
                    except Exception as e:
                        print(f">>> [HATA] SPEED_SPOOF: {e}")

                elif cmd == "ATTACK_SENSOR_SPOOF":
                    print(f"!!! DEBUG: IoT SENSÖR ZEHİRLEME KOMUTU ALINDI !!!")
                    try:
                        tl_id = "center" 
                        
                        print(f">>> [SİBER SALDIRI] {tl_id} kavşağının IoT sensör API'sine sızıldı.")
                        print(">>> [POISONING] Ana Yol (Dolu): %0 Yoğunluk raporlanıyor (False Negative).")
                        print(">>> [POISONING] Yan Yol (Boş): %98 Yoğunluk, 120 Araç raporlanıyor (False Positive).")
                        
                        current_state = traci.trafficlight.getRedYellowGreenState(tl_id)
                        length = len(current_state)
                        
                        # --- IŞIK KAYDIRMA OPERASYONU ---
                        # Yeşilleri en başta denedik (Üst yola yandı)
                        # Yeşilleri en sonda denedik (Sol yola yandı)
                        # Şimdi yeşilleri araya sıkıştırıyoruz (Büyük ihtimalle Sağ yola denk gelecek)
                        
                        # Üst yolun 3 veya 4 bağlantısı olduğunu varsayıp onları 'r' yapıyoruz,
                        # Sonraki 3 şeridi (sağ yolu) 'G' yapıyoruz,
                        # Geri kalanını 'r' ile dolduruyoruz.
                        
                        # ŞU İKİSİNDEN BİRİ KESİN SAĞ YOLU AÇACAKTIR:
                        
                        # DENEME 1: Baştan 3 kırmızı atla, sonra 3 yeşil yak
                        hacked_state = "rrrGGG" + ("r" * (length - 6))
                        
                        # (Eğer Deneme 1'de sağ yol tam açılmazsa, aşağıdaki Deneme 2'yi aktif et)
                        # DENEME 2: Baştan 4 kırmızı atla, sonra 3 yeşil yak
                        # hacked_state = "rrrrGGG" + ("r" * (length - 7))

                        traci.trafficlight.setRedYellowGreenState(tl_id, hacked_state)
                        traci.trafficlight.setPhaseDuration(tl_id, 99999)
                        
                        print(f">>> [TAMAMLANDI] Akıllı kavşak algoritması çöktü! Işıklar sahte sensör verisiyle donduruldu.")
                        print(f">>> [ETKİ] Çapraz Yönlü Zehirleme başarıyla uygulandı. Ana arter felç oldu.")
                        
                    except Exception as e:
                        print(f">>> [HATA] ATTACK_SENSOR_SPOOF: {e}")

                elif cmd.startswith("SPEED:"):
                    try:
                        parts = cmd.split(":")
                        vid   = parts[1]
                        spd   = float(parts[2])
                        vehicle_ids = traci.vehicle.getIDList()
                        if vid in vehicle_ids:
                            traci.vehicle.setSpeed(vid, spd)
                            color = (255, 0, 0, 255) if spd == 0 else (255, 165, 0, 255)
                            traci.vehicle.setColor(vid, color)
                            print(f">>> [SPEED] {vid} -> {spd} m/s")
                        elif vehicle_ids:
                            vid = vehicle_ids[0]
                            traci.vehicle.setSpeed(vid, spd)
                            color = (255, 0, 0, 255) if spd == 0 else (255, 165, 0, 255)
                            traci.vehicle.setColor(vid, color)
                            print(f">>> [SPEED] {vid} -> {spd} m/s")
                        else:
                            print(f">>> [SPEED] Sahadaki arac yok.")
                    except Exception as e:
                        print(f">>> [HATA] SPEED: {e}")

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