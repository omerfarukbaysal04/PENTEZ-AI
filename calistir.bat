@echo off
title SIBER GUVENLIK TEZI - CALISTIRMA PANELI
color 0A
cls
cd /d "%~dp0"

echo ========================================================
echo   S I B E R   G U V E N L I K   T E Z   P R O J E S I
echo   [MOD: SUREKLI TRAFIK + SALDIRI API]
echo ========================================================
echo.

:: 1. Zafiyet ayarlarini uygula
echo [1/4] Zafiyet menusu aciliyor...
py zafiyet_menu.py

:: Menuden cikis kodu: 0 = Baslat, 1 = Cikis
if %errorlevel% neq 0 (
    echo.
    echo Cikis yapildi.
    timeout /t 2 >nul
    exit
)

:: 2. Docker'i baslat (Web Paneli + Vehicle Controller)
echo [2/4] Web Paneli ve Vehicle Controller (Docker) baslatiliyor...
start "Hacker Paneli" "%~dp0docker_baslat.bat"

:: 3. Bekle (Docker hazırlansın)
echo [2/4] Web sunucusu hazirlaniyor (8 sn)...
timeout /t 8 >nul


@REM :: 3.5 Tarayıcıyı Aç
@REM echo [3/4] Admin Paneli tarayicida aciliyor...
@REM start http://localhost:5000
@REM @REM Geçici olarak tarayıcı açılmasını iptal ettim, çünkü bazı durumlarda gereksiz olabilir.

:: 4. Trafik Yoneticisini Baslat (SUMO'yu bu acacak)
echo [4/4] Trafik Yoneticisi baslatiliyor (SUMO)...
echo       NOT: Araclarin hareket etmesi icin siteye bir kez baglanti gitmesi gerekebilir.
start "Trafik Polisi" "%~dp0trafik_baslat.bat"

echo.
echo ========================================================
echo   SISTEM CANLI!
echo   - Web Paneli        : localhost:5000
echo   - SSH/Ransomware    : localhost:2222
echo   - Komuta Portu      : localhost:444
echo   - SUMO              : 8813 portunda dinliyor
echo   - Pentest Araci     : attacker klasorunde py main.py
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
