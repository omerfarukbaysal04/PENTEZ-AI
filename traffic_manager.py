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

def spawn_emergency_fleet(victim_veh=None):
    """Acil durum anında olay yerine Polis, İtfaiye ve Ambulansın TÜMÜNÜ sevk eder."""
    import time
    import traci

    try:
        # 1. Rotayı Belirle (Kurbanın rotası)
        if victim_veh:
            target_route = traci.vehicle.getRouteID(victim_veh)
        else:
            target_route = traci.route.getIDList()[0] 
            
        # 2. SUMO'nun Desteklediği Acil Durum Araçları Kataloğu
        emergency_types = [
            {"type": "POLICE", "shape": "police", "color": (0, 0, 255, 255)},       # Mavi Polis
            {"type": "AMBULANCE", "shape": "emergency", "color": (255, 0, 0, 255)}, # Kırmızı Ambulans
            {"type": "FIRETRUCK", "shape": "firebrigade", "color": (200, 50, 50, 255)} # Koyu Kırmızı İtfaiye
        ]
        
        # 3. RASTGELELİĞİ KALDIRDIK: 3 aracı da aynı anda sevk et!
        selected_fleet = emergency_types
        
        timestamp = int(time.time())
        first_veh_id = None
        
        for i, veh_data in enumerate(selected_fleet):
            veh_id = f"{veh_data['type']}_{timestamp}_{i}"
            if i == 0:
                first_veh_id = veh_id # Kamerayı ilk fırlayan araca (Polise) kilitle
                
            # Aracı haritaya ekle
            traci.vehicle.add(
                vehID=veh_id,
                routeID=target_route,
                typeID="DEFAULT_VEHTYPE",
                depart="now",
                departSpeed="max"
            )
            
            # MUTASYON: Aracı acil durum tipine dönüştür
            traci.vehicle.setColor(veh_id, veh_data['color'])
            traci.vehicle.setShapeClass(veh_id, veh_data['shape'])
            traci.vehicle.setVehicleClass(veh_id, "emergency") 
            traci.vehicle.setMaxSpeed(veh_id, 45.0)            
            traci.vehicle.setSpeedFactor(veh_id, 1.5)
            
            # Çakarları aç ve kuralları ez
            traci.vehicle.setSignals(veh_id, 1)    
            traci.vehicle.setSpeedMode(veh_id, 0)  
            
            print(f"🚨 [SİSTEM] {veh_id} olay yerine sevk edildi!")

        # --- KAMERAYI LİDER ARACA KİLİTLE ---
        try:
            if first_veh_id:
                traci.gui.trackVehicle("View #0", first_veh_id)
                traci.gui.setZoom("View #0", 1500)
        except:
            pass
            
    except Exception as e:
        print(f"❌ [IDS] Acil Durum Filosu spawn hatası: {e}")

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
                        
                        print(f"!!! DEBUG: Kavşak Işık Uzunluğu: {length} karakter !!!")

                        # --- OTONOM KEŞİF VE MANİPÜLASYON ---
                        # 1. Kavşağa bağlı tüm şeritlerin (linklerin) haritasını çekiyoruz
                        links = traci.trafficlight.getControlledLinks(tl_id)
                        
                        # 2. Önce tüm ışıkları Kırmızı ('r') olarak ayarlıyoruz (Listeye çevirerek)
                        hacked_state_list = ["r"] * length
                        
                        # 3. İndeksleri tarayıp hedef yolumuzu ("otoban_sag_2") buluyoruz
                        for i in range(length):
                            if links[i]: # Eğer bu indekste bir bağlantı varsa
                                incoming_lane = links[i][0][0] # O ışığın kontrol ettiği gelen şerit
                                
                                # Eğer şerit adı bizim hedef (boş) yolumuzsa, ışığını Yeşil ('G') yap
                                if incoming_lane.startswith("otoban_sag_2"):
                                    hacked_state_list[i] = "G"
                        
                        # 4. Listeyi tekrar string'e çeviriyoruz (örn: "rrrrrGGGrrrr")
                        hacked_state = "".join(hacked_state_list)
                        
                        print(f"!!! DEBUG: Otonom hedefleme başarılı. Yeni ışık fazı: {hacked_state}")

                        # 5. Sahte ışık dizilimini kavşağa dayat ve süresiz dondur
                        traci.trafficlight.setRedYellowGreenState(tl_id, hacked_state)
                        traci.trafficlight.setPhaseDuration(tl_id, 99999)
                        
                        print(f">>> [TAMAMLANDI] Akıllı kavşak algoritması çöktü! Işıklar sahte sensör verisiyle donduruldu.")
                        print(f">>> [ETKİ] Çapraz Yönlü Zehirleme başarıyla uygulandı. Ana arter felç oldu.")
                        
                    except Exception as e:
                        print(f">>> [HATA] ATTACK_SENSOR_SPOOF: {e}")
                
                elif cmd == "ATTACK_IDS_SPOOF_STOP":
                    print(f"!!! DEBUG: IDS SAHTE ALARM (KAZA) KOMUTU ALINDI !!!")
                    try:
                        vehicles = traci.vehicle.getIDList()
                        if vehicles:
                            victim_veh = vehicles[0]
                            
                            print(f">>> [SİBER SALDIRI] IoT Hız Sensörü Manipüle Ediliyor...")
                            print(f">>> [POISONING] Sensöre {victim_veh} aracı için 'Hız = 0 km/s' verisi gönderiliyor.")
                            
                            # 1. SUMO'nun çarpışma önleme sistemini kapat! (Anında durması için)
                            traci.vehicle.setSpeedMode(victim_veh, 0)
                            
                            traci.vehicle.setSpeed(victim_veh, 0.0)
                            traci.vehicle.setColor(victim_veh, (255, 128, 0, 255))
                            
                            # --- MAVİ TAKIM (IDS) KONTROLÜ ---
                            # Saldırgan API'ye 0 değerini bastığı için IDS bu sahte veriyi okur
                            spoofed_speed = 0.0 
                            
                            if spoofed_speed <= 0.1:
                                print(f"🚨 [IDS ALARM] KRİTİK KAZA TESPİT EDİLDİ! {victim_veh} konumunda ani duruş.")
                                
                                # Ambulansı kurbanın bilgisiyle çağır ve kamerayı kilitle!
                                spawn_emergency_fleet(victim_veh)
                                
                                print(f">>> [SONUÇ] Saldırı başarılı! IDS sistemi sahte veriyle kandırıldı.")
                        else:
                            print(">>> [HATA] Sahnede kurban edilecek araç bulunamadı.")
                            
                    except Exception as e:
                        print(f">>> [HATA] ATTACK_IDS_SPOOF_STOP: {e}")
                
                elif cmd == "ATTACK_IDS_SPOOF_SPEED":
                    print(f"!!! DEBUG: KAVŞAK SABOTAJI (AŞIRI HIZ) KOMUTU ALINDI !!!")
                    try:
                        print(f">>> [SİBER SALDIRI] IoT Sensör Ağlarına Hayalet Araç Verisi Basılıyor...")
                        print(f">>> [POISONING] Tüm yönlerden yaklaşan araçların hızı sahte olarak '150 km/s' gösteriliyor.")
                        
                        tl_ids = traci.trafficlight.getIDList()
                        if tl_ids:
                            tl_id = tl_ids[0]

                            current_state = traci.trafficlight.getRedYellowGreenState(tl_id)
                            length = len(current_state)
                            
                            state_green = "G" * length  # Herkese aynı anda Yeşil
                            state_red   = "r" * length  # Herkese aynı anda Kırmızı
                            state_yellow = "y" * length # Herkese aynı anda Sarı

                            phases = [
                                traci.trafficlight.Phase(1.0, state_green),
                                traci.trafficlight.Phase(1.0, state_red),
                                traci.trafficlight.Phase(1.0, state_yellow)
                            ]
                            
                            malicious_logic = traci.trafficlight.Logic("hacked_disco", 0, 0, phases=phases)
                            
                            traci.trafficlight.setProgramLogic(tl_id, malicious_logic)
                            traci.trafficlight.setProgram(tl_id, "hacked_disco")
                            
                            print(f"🚥 [SİSTEM ALARMI] Sensörlerde anormal hız (150 km/s) tespit edildi!")
                            print(f"🚥 [KAVŞAK ÇÖKTÜ] Orijinal algoritma silindi, 1 saniyelik kaotik döngü yüklendi.")
                            
                            try:
                                tl_x, tl_y = traci.junction.getPosition(tl_id)
                                traci.gui.setOffset("View #0", tl_x, tl_y)
                                traci.gui.setZoom("View #0", 1200)
                            except:
                                pass
                                
                            print(f">>> [SONUÇ] Saldırı başarılı! Işıklar disko moduna girdi, trafik akışı yok edildi.")
                        else:
                            print(">>> [HATA] Sahnede müdahale edilecek trafik ışığı bulunamadı.")
                            
                    except Exception as e:
                        print(f">>> [HATA] ATTACK_IDS_SPOOF_SPEED: {e}")

                elif cmd == "ATTACK_V2X_V2V":
                    print(f"!!! DEBUG: V2V SİNYAL ENJEKSİYONU (SYBIL) KOMUTU İŞLENİYOR !!!")
                    try:
                        import math # Mesafe hesabı için
                        
                        active_vehs = traci.vehicle.getIDList()
                        # Zombi aracımız hedef_arac olsun, yoksa sahadaki ilk aracı seç
                        zombie_veh = "hedef_arac" if "hedef_arac" in active_vehs else (active_vehs[0] if active_vehs else None)
                        
                        if zombie_veh:
                            # 1. Zombi aracı ZEHİR YEŞİLİ yap
                            traci.vehicle.setColor(zombie_veh, (0, 255, 0, 255))
                            
                            # 2. Zombinin anlık X, Y koordinatlarını al
                            zx, zy = traci.vehicle.getPosition(zombie_veh)
                            
                            # 3. KAMERA DÜZELTMESİ: Tam o X,Y noktasına odaklan, zoom'u genişlet ve takibe al!
                            try:
                                traci.gui.setOffset("View #0", zx, zy)  # Kamerayı tam aracın üstüne oturt
                                traci.gui.setZoom("View #0", 750)       # 50m yarıçapı görmek için daha geniş açı (1500'den 750'ye düştü)
                                traci.gui.trackVehicle("View #0", zombie_veh) # Şimdi takibe başla
                            except Exception as cam_err:
                                print(f"Kamera hizalama hatası: {cam_err}")

                            print(f">>> [ZOMBİ AKTİF] {zombie_veh} aracı etrafına sahte V2V kaza sinyali yayıyor!")
                            
                            affected_count = 0
                            
                            # 4. ŞOK DALGASI: 50 metre yarıçapındaki tüm araçları bul
                            for v in active_vehs:
                                if v == zombie_veh:
                                    continue # Zombi kendi yalanına kanmaz, yola devam eder!
                                
                                vx, vy = traci.vehicle.getPosition(v)
                                dist = math.hypot(zx - vx, zy - vy) 
                                
                                if dist <= 50.0:
                                    # Kurbanlar V2V mesajını "gerçek" sanıp kazık fren yapar
                                    traci.vehicle.setSpeedMode(v, 0) 
                                    traci.vehicle.setSpeed(v, 0.0)
                                    traci.vehicle.setColor(v, (255, 0, 0, 255)) # Kaza yapanları KIRMIZI yap
                                    affected_count += 1
                                    
                            print(f">>> [SONUÇ] Şok Dalgası: {affected_count} masum araç sahte sinyale kanıp kaza yaptı!")
                            
                        else:
                            print(">>> [HATA] Sahnede zombi yapılacak araç bulunamadı.")
                            
                    except Exception as e:
                        print(f">>> [HATA] ATTACK_V2X_V2V: {e}")

                elif cmd == "ATTACK_V2X_V2I":
                    print(f"!!! DEBUG: V2I ALTYAPI ZEHİRLEMESİ KOMUTU ALINDI !!!")
                    try:
                        active_vehs = traci.vehicle.getIDList()
                        zombie_veh = "hedef_arac" if "hedef_arac" in active_vehs else (active_vehs[0] if active_vehs else None)
                        
                        if zombie_veh:
                            # Zombi aracı yeşile boya
                            traci.vehicle.setColor(zombie_veh, (0, 255, 0, 255))
                            print(f">>> [ZOMBİ AKTİF] {zombie_veh} aracı içeriden kavşağa sahte telemetri (V2I) basıyor!")
                            
                            # Kavşağı bul ve V2I verisine güvenerek kilitle!
                            tl_ids = traci.trafficlight.getIDList()
                            if tl_ids:
                                tl_id = tl_ids[0]
                                # Güvenilir araçtan (OBU) geldiği için sistem sorgulamadan ışıkları dondurur
                                traci.trafficlight.setPhaseDuration(tl_id, 9999)
                                
                                print(f"🚥 [KAVŞAK ÇÖKTÜ] Kendi aracından gelen sahte veriye güvenen sistem kilitlendi!")
                                
                                # Kamerayı zombiye kilitle
                                try:
                                    traci.gui.trackVehicle("View #0", zombie_veh)
                                    traci.gui.setZoom("View #0", 1200)
                                except:
                                    pass
                            else:
                                print(">>> [HATA] Haritada trafik ışığı bulunamadı.")
                        else:
                            print(">>> [HATA] Sahnede zombi yapılacak araç bulunamadı.")
                            
                    except Exception as e:
                        print(f">>> [HATA] V2X_SPOOF_V2I: {e}")

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