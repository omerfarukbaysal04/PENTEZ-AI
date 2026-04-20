#!/usr/bin/env python3
import time
import os
import socket
import threading

SECURITY_MODE = os.environ.get("SECURITY_MODE", "VULNERABLE").upper()
print("[VEHICLE_CONTROLLER] Araç kontrol servisi başlatıldı.")
print(f"[VEHICLE_CONTROLLER] Güvenlik Modu: {SECURITY_MODE}")
print("[VEHICLE_CONTROLLER] SSH servisi aktif — port 22")

TRAFFIC_MANAGER_HOST = os.environ.get("TRAFFIC_MANAGER_HOST", "host.docker.internal")
TRAFFIC_MANAGER_PORT = 9999

def forward_to_traffic_manager(command):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((TRAFFIC_MANAGER_HOST, TRAFFIC_MANAGER_PORT))
        sock.sendall(command.encode('utf-8'))
        sock.recv(1024)
        sock.close()
        print(f"[VEHICLE_CONTROLLER] traffic_manager'a iletildi: {command}")
        return True
    except Exception as e:
        print(f"[VEHICLE_CONTROLLER] traffic_manager baglanti hatasi: {e}")
        return False

def start_speed_control_server():
    if SECURITY_MODE == "SECURE":
        print("[VEHICLE_CONTROLLER] SECURE mod: Port 444 dinlenmiyor.")
        return

    print("[VEHICLE_CONTROLLER] Port 444 dinleniyor (kimlik dogrulama YOK!)")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 444))
    server.listen(5)

    while True:
        try:
            client, addr = server.accept()
            data = client.recv(1024).decode('utf-8').strip()
            print(f"[VEHICLE_CONTROLLER] Komut alindi ({addr[0]}): {data}")

            if data.startswith("SPEED:"):
                parts = data.split(":")
                if len(parts) == 3:
                    veh_id = parts[1]
                    speed  = parts[2]
                    cmd    = f"SPEED_SPOOF:{veh_id}:{speed}"
                    forward_to_traffic_manager(cmd)
                    client.send(b"OK: Hiz komutu uygulaniyor")
                else:
                    client.send(b"ERR: Format hatasi. Beklenen: SPEED:veh_id:deger")
            elif data.startswith("LANE:"):
                # Format: LANE:veh_id:lane_index — Dogrulama YOK (zafiyet!)
                parts = data.split(":")
                if len(parts) == 3:
                    cmd = f"MOVEMENT_LANE:{parts[1]}:{parts[2]}"
                    forward_to_traffic_manager(cmd)
                    client.send(b"OK: Serit degistirme komutu uygulaniyor")
                else:
                    client.send(b"ERR: Format hatasi. Beklenen: LANE:veh_id:index")

            elif data.startswith("ROUTE:"):
                # Format: ROUTE:veh_id:route_id — Dogrulama YOK (zafiyet!)
                parts = data.split(":")
                if len(parts) == 3:
                    cmd = f"MOVEMENT_ROUTE:{parts[1]}:{parts[2]}"
                    forward_to_traffic_manager(cmd)
                    client.send(b"OK: Rota degistirme komutu uygulaniyor")
                else:
                    client.send(b"ERR: Format hatasi. Beklenen: ROUTE:veh_id:route_id")
            
            elif data == "ATTACK_V2X_V2V":
                # Kurban araç (Zombi), etrafındaki diğer araçlara sahte "KAZA VAR, DURUN!" yayını yapar
                print("[VEHICLE_CONTROLLER] 🚨 ZOMBİ AKTİF: V2V Sybil (Yanlış Bilgi Yayılımı) saldırısı başlatıldı!")
                forward_to_traffic_manager("V2X_SYBIL_V2V")
                client.send(b"OK: V2V sahte acil durum yayini basladi")

            elif data == "ATTACK_V2X_V2I":
                # Kurban araç, altyapıya (kavşağa) içeriden sahte ve aşırı yüksek hız verisi basar
                print("[VEHICLE_CONTROLLER] 🚨 ZOMBİ AKTİF: V2I Altyapı Zehirlenmesi saldırısı başlatıldı!")
                forward_to_traffic_manager("V2X_SPOOF_V2I")
                client.send(b"OK: V2I sahte telemetri verisi basladi")

            else:
                client.send(b"ERR: Bilinmeyen komut")

            client.close()
        except Exception as e:
            print(f"[VEHICLE_CONTROLLER] Port 444 hata: {e}")

t = threading.Thread(target=start_speed_control_server)
t.daemon = True
t.start()

while True:
    print("[VEHICLE_CONTROLLER] Araclar kontrol ediliyor...")
    time.sleep(10)