@echo off
title SIBER GUVENLIK TEZI - CALISTIRMA PANELI
color 0A
cls

echo ========================================================
echo   S I B E R   G U V E N L I K   T E Z   P R O J E S I
echo   [MOD: SUREKLI TRAFIK + SALDIRI API]
echo ========================================================
echo.

:: 1. Docker'ı başlat (Web Sunucusu)
echo [1/4] Web Paneli (Docker) baslatiliyor...
start "Hacker Paneli" docker-compose up --build

:: 2. Bekle (Docker hazırlansın)
echo [2/4] Web sunucusu hazirlaniyor (8 sn)...
timeout /t 8 >nul

@REM :: 3. Tarayıcıyı Aç
@REM echo [3/4] Admin Paneli tarayicida aciliyor...
@REM start http://localhost:5000
@REM @REM Geçici olarak tarayıcı açılmasını iptal ettim, çünkü bazı durumlarda gereksiz olabilir.

:: 4. Trafik Yöneticisini Başlat (SUMO'yu bu açacak)
echo [4/4] Trafik Yoneticisi baslatiliyor (SUMO)...
echo       NOT: Araclarin hareket etmesi icin siteye bir kez baglanti gitmesi gerekebilir.
:: traffic_manager.py'yi çalıştırır. Bu da SUMO'yu açar.
start "Trafik Polisi" py traffic_manager.py

echo.
echo ========================================================
echo   SISTEM CANLI! 
echo   - Web Paneli: localhost:5000
echo   - SUMO: 8813 Portunda dinliyor
echo   - Trafik Yoneticisi: Arkada calisiyor
echo ========================================================
echo.
echo   [ ! ] KAPATMAK ICIN ENTER TUSUNA BASIN [ ! ]
echo.
pause >nul

:: --- KAPATMA BÖLÜMÜ ---
color 0C
cls
echo KAPATILIYOR...

echo [-] SUMO ve Python Yoneticisi kapatiliyor...
taskkill /F /IM sumo-gui.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1

echo [-] Docker temizleniyor...
docker-compose down

echo ISLEM TAMAM.
timeout /t 3
exit