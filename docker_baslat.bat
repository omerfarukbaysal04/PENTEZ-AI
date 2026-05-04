@echo off
title Hacker Paneli
cd /d "%~dp0"

echo ========================================================
echo   PENTEZ-AI Docker servisleri baslatiliyor
echo ========================================================
echo.
echo Calisma dizini: %cd%
echo.

echo [1/5] Docker CLI kontrol ediliyor...
docker --version
echo.

echo [2/5] Docker Compose kontrol ediliyor...
docker-compose --version
echo.

echo [3/5] Docker daemon baglantisi kontrol ediliyor...
docker info
if %errorlevel% neq 0 (
    echo.
    echo [HATA] Docker daemon'a baglanilamadi.
    echo Docker Desktop acik mi, sol altta "Engine running" gorunuyor mu kontrol edin.
    echo.
    pause
    exit /b 1
)
echo.

echo [4/5] Compose dosyasi dogrulaniyor...
docker-compose config
if %errorlevel% neq 0 (
    echo.
    echo [HATA] docker-compose.yaml dogrulanamadi.
    echo Yukaridaki hata mesajini kontrol edin.
    echo.
    pause
    exit /b 1
)
echo.

echo [5/5] Container'lar baslatiliyor...
docker-compose up --build --remove-orphans

echo.
echo [Docker] Komut sonlandi. Hata varsa yukaridaki mesaja bak.
echo [Docker] Pencereyi kapatmak icin bir tusa basin.
pause >nul
