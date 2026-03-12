#!/usr/bin/env python3
"""
vehicle_controller/control.py
Zafiyetli araç kontrol servisi.
SSH ile erişilebilir, şifre: 1234
Port 444: Hız kontrol soketi (doğrulama YOK — zafiyet!)
"""
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
    """Komutu traffic_manager.py'ye ilet"""
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

def start_speed_control_server():
    """Port 444 - Hız kontrol soketi (VULNERABLE modda açık, SECURE modda kapalı)"""

    if SECURITY_MODE == "SECURE":
        print("[VEHICLE_CONTROLLER] 🛡️  SECURE mod: Port 444 dinlenmiyor.")
        return

    print("[VEHICLE_CONTROLLER] ⚠️  Port 444 dinleniyor (kimlik doğrulama YOK!)")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 444))
    server.listen(5)

    while True:
        try:
            client, addr = server.accept()
            data = client.recv(1024).decode('utf-8').strip()
            print(f"[VEHICLE_CONTROLLER] Komut alındı ({addr[0]}): {data}")

            # Doğrulama YOK — gelen her komutu direkt uygula (zafiyet!)
            if data.startswith("SPEED:"):
                # Format: SPEED:veh_id:speed_value
                parts = data.split(":")
                if len(parts) == 3:
                    veh_id = parts[1]
                    speed  = parts[2]
                    cmd    = f"SPEED_SPOOF:{veh_id}:{speed}"
                    forward_to_traffic_manager(cmd)
                    client.send(b"OK: Hiz komutu uygulaniyor")
                else:
                    client.send(b"ERR: Format hatasi. Beklenen: SPEED:veh_id:deger")
            else:
                client.send(b"ERR: Bilinmeyen komut")

            client.close()
        except Exception as e:
            print(f"[VEHICLE_CONTROLLER] Port 444 hata: {e}")

# Port 444'ü ayrı thread'de başlat
t = threading.Thread(target=start_speed_control_server)
t.daemon = True
t.start()

# Ana döngü
while True:
    print("[VEHICLE_CONTROLLER] Araçlar kontrol ediliyor...")
    time.sleep(10)