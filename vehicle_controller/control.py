#!/usr/bin/env python3
"""
vehicle_controller/control.py
Zafiyetli araç kontrol servisi.
SSH ile erişilebilir, şifre: 1234
"""
import time
import os

print("[VEHICLE_CONTROLLER] Araç kontrol servisi başlatıldı.")
print("[VEHICLE_CONTROLLER] SSH servisi aktif — port 22")
print("[VEHICLE_CONTROLLER] Trafik yönetimi devam ediyor...")

# Simülasyon döngüsü (pkill ile öldürülene kadar çalışır)
while True:
    print("[VEHICLE_CONTROLLER] Araçlar kontrol ediliyor...")
    time.sleep(10)