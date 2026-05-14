@echo off
title PENTEZ-AI
color 0A
cls
cd /d "%~dp0"

echo.
echo  ======================================================================
echo   PPPP   EEEEE  N   N  TTTTT  EEEEE  ZZZZZ       AAAAA  III
echo   P   P  E      NN  N    T    E         Z        A   A   I
echo   PPPP   EEEE   N N N    T    EEEE     Z         AAAAA   I
echo   P      E      N  NN    T    E       Z          A   A   I
echo   P      EEEEE  N   N    T    EEEEE  ZZZZZ       A   A  III
echo  ======================================================================
echo   CALISTIRMA ORKESTRATORU  ^|  Merkezi Zafiyet Sistemi + SUMO + Pentest
echo  ======================================================================
echo.
echo   Sistem akisi:
echo     1. Zafiyetleri sec
echo     2. Docker ve trafik servislerini baslat
echo     3. Web dashboard uzerinden sistemi izle
echo     4. Pentest aracini calistir ve raporu ac
echo.

:: 1. Zafiyet ayarlarini uygula
echo  ----------------------------------------------------------------------
echo   [01/04] MERKEZI ZAFIYET MATRISI
echo  ----------------------------------------------------------------------
echo   Zafiyet menusu aciliyor...
echo.
py zafiyet_menu.py

:: Menuden cikis kodu: 0 = Baslat, 1 = Cikis
if %errorlevel% neq 0 (
    echo.
    echo  ----------------------------------------------------------------------
    echo   Sistem baslatilmadi. Cikis yapiliyor...
    echo  ----------------------------------------------------------------------
    timeout /t 2 >nul
    exit
)

:: 2. Docker'i baslat (Web Paneli + Vehicle Controller)
echo.
echo  ----------------------------------------------------------------------
echo   [02/04] DOCKER SERVISLERI
echo  ----------------------------------------------------------------------
echo   Web Paneli ve Vehicle Controller baslatiliyor...
echo   Pencere: Hacker Paneli
echo.
start "Hacker Paneli" "%~dp0docker_baslat.bat"

:: 3. Bekle (Docker hazirlansin)
echo  ----------------------------------------------------------------------
echo   [03/04] WEB DASHBOARD
echo  ----------------------------------------------------------------------
echo   Web sunucusu hazirlaniyor. Lutfen bekleyin: 8 sn
timeout /t 8 >nul
echo   Dashboard tarayicida aciliyor: http://localhost:5000
start http://localhost:5000

:: 4. Trafik Yoneticisini Baslat (SUMO'yu bu acacak)
echo.
echo  ----------------------------------------------------------------------
echo   [04/04] SUMO TRAFIK SIMULASYONU
echo  ----------------------------------------------------------------------
echo   Trafik Yoneticisi baslatiliyor...
echo   Pencere: Trafik Polisi
echo   Not: Araclarin hareket etmesi icin dashboard'a ilk baglanti gerekebilir.
echo.
start "Trafik Polisi" "%~dp0trafik_baslat.bat"

echo.
echo  ======================================================================
echo   SISTEM CANLI
echo  ======================================================================
echo.
echo   +----------------------+------------------------------+
echo   ^| Web Dashboard        ^| http://localhost:5000       ^|
echo   ^| SSH / Ransomware     ^| localhost:2222              ^|
echo   ^| Attack Command API   ^| localhost:444               ^|
echo   ^| SUMO / TraCI         ^| localhost:8813              ^|
echo   ^| Pentest Araci        ^| attacker klasoru / py main.py^|
echo   +----------------------+------------------------------+
echo.
echo  ======================================================================
echo   KAPATMAK ICIN ENTER TUSUNA BASIN
echo  ======================================================================
echo.
pause >nul

:: --- KAPATMA BOLUMU ---
color 0C
cls
echo.
echo  ======================================================================
echo   PENTEZ-AI KAPATILIYOR
echo  ======================================================================
echo.

echo   [01/05] Canli pentest log dosyasi temizleniyor...
del /F /Q "%~dp0attacker\live_pentest.log" >nul 2>&1
echo           OK

echo   [02/05] SUMO ve Python yoneticileri kapatiliyor...
taskkill /F /IM sumo-gui.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM py.exe /T >nul 2>&1
echo           OK

echo   [03/05] Docker servisleri durduruluyor...
docker-compose down >nul 2>&1
taskkill /F /IM docker-compose.exe /T >nul 2>&1
taskkill /F /IM docker.exe /T >nul 2>&1
echo           OK

echo   [04/05] Yardimci CMD pencereleri kapatiliyor...
taskkill /F /T /FI "WINDOWTITLE eq Hacker Paneli*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq Trafik Polisi*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq *Hacker Paneli*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq *Trafik Polisi*" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and ($_.CommandLine -like '*docker_baslat.bat*' -or $_.CommandLine -like '*trafik_baslat.bat*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
echo           OK

echo   [05/05] Kapanis tamamlandi.
echo.
echo  ======================================================================
echo   CALISMA ORTAMI TEMIZLENDI
echo  ======================================================================
timeout /t 3 >nul
exit
