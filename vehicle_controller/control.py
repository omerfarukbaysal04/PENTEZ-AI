#!/usr/bin/env python3
import time
import os
import socket
import threading

# ── GÜVENLİK AYARLARI (Saldırı Bazlı) ──────────────────────────────────────
SSH_ENABLED          = os.environ.get("SSH_ENABLED",          "true").lower() == "true"
SPEED_SPOOF_ENABLED  = os.environ.get("SPEED_SPOOF_ENABLED",  "true").lower() == "true"
IOT_SENSOR_ENABLED   = os.environ.get("IOT_SENSOR_ENABLED",   "true").lower() == "true"
IDS_SPOOF_ENABLED    = os.environ.get("IDS_SPOOF_ENABLED",    "true").lower() == "true"
FAKE_VEHICLE_ENABLED = os.environ.get("FAKE_VEHICLE_ENABLED", "true").lower() == "true"
V2X_ENABLED          = os.environ.get("V2X_ENABLED",          "true").lower() == "true"

print("[VEHICLE_CONTROLLER] Araç kontrol servisi başlatıldı.")
print(f"[VEHICLE_CONTROLLER] SSH Zafiyeti       : {'VULNERABLE' if SSH_ENABLED else 'SECURE'}")
print(f"[VEHICLE_CONTROLLER] Speed Spoof        : {'VULNERABLE' if SPEED_SPOOF_ENABLED else 'SECURE'}")
print(f"[VEHICLE_CONTROLLER] IoT Sensör         : {'VULNERABLE' if IOT_SENSOR_ENABLED else 'SECURE'}")
print(f"[VEHICLE_CONTROLLER] IDS Sabotajı       : {'VULNERABLE' if IDS_SPOOF_ENABLED else 'SECURE'}")
print(f"[VEHICLE_CONTROLLER] Fake Vehicle       : {'VULNERABLE' if FAKE_VEHICLE_ENABLED else 'SECURE'}")
print(f"[VEHICLE_CONTROLLER] V2X (V2V/V2I)      : {'VULNERABLE' if V2X_ENABLED else 'SECURE'}")

if SSH_ENABLED:
    print("[VEHICLE_CONTROLLER] SSH servisi aktif — port 22 (zayıf şifre: root:1234)")
else:
    print("[VEHICLE_CONTROLLER] SSH servisi güçlendirildi — brute force koruması aktif")

TRAFFIC_MANAGER_HOST = os.environ.get("TRAFFIC_MANAGER_HOST", "host.docker.internal")
TRAFFIC_MANAGER_PORT = 9999

# ── YARDIMCI ────────────────────────────────────────────────────────────────

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
        print(f"[VEHICLE_CONTROLLER] traffic_manager bağlantı hatası: {e}")
        return False

def blocked_response(client, attack_name):
    msg = f"BLOCKED: {attack_name} guvenlik sistemi tarafindan engellendi."
    print(f"[VEHICLE_CONTROLLER] 🛡️  SECURE MOD: {attack_name} engellendi!")
    client.send(msg.encode('utf-8'))

# ── PORT 444 SUNUCUSU ────────────────────────────────────────────────────────

def start_speed_control_server():
    print("[VEHICLE_CONTROLLER] Port 444 dinleniyor...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 444))
    server.listen(5)

    while True:
        try:
            client, addr = server.accept()
            data = client.recv(1024).decode('utf-8').strip()
            print(f"[VEHICLE_CONTROLLER] Komut alındı ({addr[0]}): {data}")

            # ── SPEED SPOOF ──────────────────────────────────────────────
            if data.startswith("SPEED:"):
                if not SPEED_SPOOF_ENABLED:
                    blocked_response(client, "Speed Spoof")
                else:
                    parts = data.split(":")
                    if len(parts) == 3:
                        cmd = f"SPEED_SPOOF:{parts[1]}:{parts[2]}"
                        forward_to_traffic_manager(cmd)
                        client.send(b"OK: Hiz komutu uygulaniyor")
                    else:
                        client.send(b"ERR: Format hatasi. Beklenen: SPEED:veh_id:deger")

            # ── MOVEMENT HACK ────────────────────────────────────────────
            elif data.startswith("LANE:"):
                if not SPEED_SPOOF_ENABLED:
                    blocked_response(client, "Movement Hack (Lane)")
                else:
                    parts = data.split(":")
                    if len(parts) == 3:
                        forward_to_traffic_manager(f"MOVEMENT_LANE:{parts[1]}:{parts[2]}")
                        client.send(b"OK: Serit degistirme komutu uygulaniyor")
                    else:
                        client.send(b"ERR: Format hatasi. Beklenen: LANE:veh_id:index")

            elif data.startswith("ROUTE:"):
                if not SPEED_SPOOF_ENABLED:
                    blocked_response(client, "Movement Hack (Route)")
                else:
                    parts = data.split(":")
                    if len(parts) == 3:
                        forward_to_traffic_manager(f"MOVEMENT_ROUTE:{parts[1]}:{parts[2]}")
                        client.send(b"OK: Rota degistirme komutu uygulaniyor")
                    else:
                        client.send(b"ERR: Format hatasi. Beklenen: ROUTE:veh_id:route_id")

            # ── IOT SENSOR SPOOF ─────────────────────────────────────────
            elif data == "ATTACK_SENSOR_SPOOF":
                if not IOT_SENSOR_ENABLED:
                    blocked_response(client, "IoT Sensor Zehirleme")
                else:
                    print("[VEHICLE_CONTROLLER] 🚦 IoT Sensör Zehirleme saldırısı yönlendiriliyor...")
                    forward_to_traffic_manager("ATTACK_SENSOR_SPOOF")
                    client.send(b"OK: IoT sensor zehirleme basladi")

            # ── IDS YANLIŞ ALARM (DUR) ───────────────────────────────────
            elif data == "ATTACK_IDS_SPOOF_STOP":
                if not IDS_SPOOF_ENABLED:
                    blocked_response(client, "IDS Yanlis Alarm (Dur)")
                else:
                    print("[VEHICLE_CONTROLLER] 🚨 IDS Yanlış Alarm (Sahte Kaza) yönlendiriliyor...")
                    forward_to_traffic_manager("ATTACK_IDS_SPOOF_STOP")
                    client.send(b"OK: IDS yanlis alarm (sahte kaza) basladi")

            # ── IDS ZAMANLAMA SABOTAJI ───────────────────────────────────
            elif data == "ATTACK_IDS_SPOOF_SPEED":
                if not IDS_SPOOF_ENABLED:
                    blocked_response(client, "IDS Zamanlama Sabotaji")
                else:
                    print("[VEHICLE_CONTROLLER] ⚡ Işık Zamanlama Sabotajı yönlendiriliyor...")
                    forward_to_traffic_manager("ATTACK_IDS_SPOOF_SPEED")
                    client.send(b"OK: Zamanlama sabotaji basladi")

            # ── FAKE VEHICLE ─────────────────────────────────────────────
            elif data == "FAKE_VEHICLE":
                if not FAKE_VEHICLE_ENABLED:
                    blocked_response(client, "Fake Vehicle")
                else:
                    print("[VEHICLE_CONTROLLER] 👻 Fake Vehicle saldırısı yönlendiriliyor...")
                    forward_to_traffic_manager("FAKE_VEHICLE")
                    client.send(b"OK: Fake vehicle injection basladi")

            # ── V2V SYBIL ────────────────────────────────────────────────
            elif data == "ATTACK_V2X_V2V":
                if not V2X_ENABLED:
                    blocked_response(client, "V2V Sybil Saldirisi")
                else:
                    print("[VEHICLE_CONTROLLER] 🚨 ZOMBİ AKTİF: V2V Sybil saldırısı başlatıldı!")
                    forward_to_traffic_manager("V2X_SYBIL_V2V")
                    client.send(b"OK: V2V sahte acil durum yayini basladi")

            # ── V2I ALTYAPI ZEHİRLEME ────────────────────────────────────
            elif data == "ATTACK_V2X_V2I":
                if not V2X_ENABLED:
                    blocked_response(client, "V2I Altyapi Zehirlenmesi")
                else:
                    print("[VEHICLE_CONTROLLER] 🚨 ZOMBİ AKTİF: V2I Altyapı Zehirlenmesi başlatıldı!")
                    forward_to_traffic_manager("V2X_SPOOF_V2I")
                    client.send(b"OK: V2I sahte telemetri verisi basladi")

            # ── STATUS SORGUSU ────────────────────────────────────────────
            elif data == "STATUS":
                import json
                status = {
                    "ssh":          SSH_ENABLED,
                    "speed_spoof":  SPEED_SPOOF_ENABLED,
                    "iot_sensor":   IOT_SENSOR_ENABLED,
                    "ids_spoof":    IDS_SPOOF_ENABLED,
                    "fake_vehicle": FAKE_VEHICLE_ENABLED,
                    "v2x":          V2X_ENABLED,
                }
                client.send(json.dumps(status).encode('utf-8'))



            client.close()

        except Exception as e:
            print(f"[VEHICLE_CONTROLLER] Port 444 hata: {e}")


t = threading.Thread(target=start_speed_control_server)
t.daemon = True
t.start()

while True:
    print("[VEHICLE_CONTROLLER] Araçlar kontrol ediliyor...")
    time.sleep(10)