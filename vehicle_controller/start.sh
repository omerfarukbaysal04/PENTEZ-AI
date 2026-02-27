#!/bin/bash
# SSH servisini başlat
service ssh start
echo "[START] SSH servisi başlatıldı — root:1234"

# Araç kontrol scriptini başlat
python3 /app/control.py