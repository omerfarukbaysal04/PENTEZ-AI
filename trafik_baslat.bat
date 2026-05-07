@echo off
title Trafik Polisi
cd /d "%~dp0"

echo ========================================================
echo   PENTEZ-AI Trafik Yoneticisi / SUMO baslatiliyor
echo ========================================================
echo.
echo Calisma dizini: %cd%
echo.

py traffic_manager.py

echo.
echo [Trafik] Komut sonlandi. Hata varsa yukaridaki mesaja bak.
timeout /t 1 >nul
