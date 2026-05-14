#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENTEZ-AI — Zafiyet Yapılandırma Menüsü
calistir.bat tarafından çağrılır, docker-compose.yaml'ı günceller.
"""

import os
import re
import sys

COMPOSE_FILE = "docker-compose.yaml"

ATTACKS = [
    {"id": 1,  "name": "SQL Injection ile Sunucu İhlali",       "category": "Merkezi Sistem",   "env_key": "SQL_INJECTION_ENABLED", "service": "web_panel",          "desc": "Web paneline SQLi ile sızılıp tüm ışıklar yeşile çevrilir"},
    {"id": 2,  "name": "Web Panel Lockdown (Araç Kilitleme)",    "category": "Merkezi Sistem",   "env_key": "WEBPANEL_LOCK_ENABLED", "service": "web_panel",          "desc": "Dashboard üzerinden araç motoru uzaktan kilitlenir"},
    {"id": 3,  "name": "SSH Brute Force & Ransomware",           "category": "Merkezi Sistem",   "env_key": "SSH_ENABLED",           "service": "vehicle_controller", "desc": "Zayıf parola kırılıp dosyalar şifrelenir, fidye notu bırakılır"},
    {"id": 5,  "name": "IoT Sensör Zehirleme (Çapraz Yönlü)",   "category": "IoT / Uç Nokta",   "env_key": "IOT_SENSOR_ENABLED",    "service": "vehicle_controller", "desc": "Kavşak API'sine sahte araç sayısı basılarak ışıklar kilitlenir"},
    {"id": 6,  "name": "IDS Yanlış Alarm (Acil Araç Filosu)",   "category": "IoT / Uç Nokta",   "env_key": "IDS_FALSE_ALARM_ENABLED","service": "vehicle_controller", "desc": "Sahte 0 km/h verisiyle ambulans/polis yanlış yönlendirilir"},
    {"id": 7,  "name": "Işık Zamanlama Sabotajı (Disko Modu)",  "category": "IoT / Uç Nokta",   "env_key": "IDS_TIMING_ENABLED",     "service": "vehicle_controller", "desc": "Her yönden 150 km/h verisiyle kavşak algoritması paniğe sürüklenir"},
    {"id": 4,  "name": "Speed Spoofing (Port 444)",              "category": "V2X / Otonom Araç","env_key": "SPEED_SPOOF_ENABLED",   "service": "vehicle_controller", "desc": "Port 444 üzerinden aracın hız kontrolü manipüle edilir"},
    {"id": 8,  "name": "Fake Vehicle (Hayalet Araç Enjeksiyonu)","category": "V2X / Otonom Araç","env_key": "FAKE_VEHICLE_ENABLED",  "service": "vehicle_controller", "desc": "Hayalet araçlar haritaya duvar gibi dizilip rotalar kilitlenir"},
    {"id": 9,  "name": "V2V Yanlış Bilgi Yayılımı (Şok Dalgası)","category": "V2X / Otonom Araç","env_key": "V2V_ENABLED",           "service": "vehicle_controller", "desc": "Zombi araç 50m çevresine sahte kaza sinyali yayar"},
    {"id": 10, "name": "V2I Altyapı Zehirlenmesi (İçeriden)",   "category": "V2X / Otonom Araç","env_key": "V2I_ENABLED",           "service": "vehicle_controller", "desc": "Zombi OBU içeriden sahte telemetri basarak kavşağı felç eder"},
]

# Unique env key'ler için başlangıç durumu
states = {a["env_key"]: True for a in ATTACKS}


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def read_compose():
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def write_compose(content):
    with open(COMPOSE_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def set_env_in_service(content, service, env_key, value):
    lines      = content.split("\n")
    in_service = False
    in_env     = False
    result     = []
    for line in lines:
        if re.match(rf"  {service}:", line):
            in_service = True
            in_env     = False
        elif re.match(r"  \w[\w_]+:", line) and not re.match(rf"  {service}:", line):
            in_service = False
            in_env     = False
        if in_service and re.match(r"\s+environment:", line):
            in_env = True
        if in_service and in_env and env_key in line:
            indent = len(line) - len(line.lstrip())
            line   = " " * indent + f'{env_key}: "{value}"'
        result.append(line)
    return "\n".join(result)


def get_env_from_service(content, service, env_key):
    lines      = content.split("\n")
    in_service = False
    in_env     = False

    for line in lines:
        if re.match(rf"  {service}:", line):
            in_service = True
            in_env     = False
        elif re.match(r"  \w[\w_]+:", line) and not re.match(rf"  {service}:", line):
            in_service = False
            in_env     = False

        if in_service and re.match(r"\s+environment:", line):
            in_env = True

        if in_service and in_env:
            match = re.match(rf"\s+{env_key}:\s*[\"']?(true|false)[\"']?", line, re.IGNORECASE)
            if match:
                return match.group(1).lower() == "true"

    return None


def load_states_from_compose():
    if not os.path.exists(COMPOSE_FILE):
        return

    content = read_compose()
    for a in ATTACKS:
        value = get_env_from_service(content, a["service"], a["env_key"])
        if value is not None:
            states[a["env_key"]] = value


def apply_to_compose():
    content   = read_compose()
    processed = set()
    for a in ATTACKS:
        key = (a["env_key"], a["service"])
        if key not in processed:
            val     = "true" if states[a["env_key"]] else "false"
            content = set_env_in_service(content, a["service"], a["env_key"], val)
            processed.add(key)
    write_compose(content)


def shared_names(env_key):
    return [a["name"] for a in ATTACKS if a["env_key"] == env_key]


def draw_menu():
    clear()
    print("=" * 68)
    print("   P E N T E Z - A I   —   Zafiyet Yapılandırma Paneli")
    print("=" * 68)
    print(f"  {'#':<4} {'Saldırı':<44} {'Durum'}")
    print("  " + "-" * 62)

    current_cat = ""
    for menu_no, a in enumerate(ATTACKS, start=1):
        if a["category"] != current_cat:
            current_cat = a["category"]
            print(f"\n  ── {current_cat} ──")

        enabled = states[a["env_key"]]
        status  = "[ VULNERABLE ]" if enabled else "[   SECURE   ]"
        shared  = "*" if len(shared_names(a["env_key"])) > 1 else " "
        print(f"  {menu_no:<4} {a['name'] + shared:<44} {status}")

    print()
    print("  * Yıldızlı saldırılar aynı anahtarı paylaşır — birlikte değişir.")
    print("\n" + "=" * 68)
    print("  [1-10] Numarayı girerek aç/kapat")
    print("  [A]    Tümünü VULNERABLE yap")
    print("  [S]    Tümünü SECURE yap")
    print("  [B]    Başlat")
    print("  [Q]    Çıkış")
    print("=" * 68 + "\n")


def toggle(menu_no):
    a       = ATTACKS[menu_no - 1]
    key     = a["env_key"]
    states[key] = not states[key]
    new     = "VULNERABLE" if states[key] else "SECURE"
    names   = shared_names(key)
    if len(names) > 1:
        print(f"\n  ✓ {' + '.join(names)} → {new} (birlikte değişti)")
    else:
        print(f"\n  ✓ {a['name']} → {new}")


def main():
    load_states_from_compose()

    while True:
        draw_menu()
        choice = input("  Seçim: ").strip().upper()

        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= 10:
                toggle(num)
                input("  [Enter] ile devam et...")
            else:
                print("  Geçersiz numara.")
                input("  [Enter]")

        elif choice == "A":
            for k in states:
                states[k] = True
            print("\n  ✓ Tüm açıklar VULNERABLE.")
            input("  [Enter]")
            

        elif choice == "S":
            for k in states:
                states[k] = False
            print("\n  ✓ Tüm açıklar SECURE.")
            input("  [Enter]")

        elif choice == "B":
            apply_to_compose()
            clear()
            print("=" * 68)
            print("  Ayarlar uygulandı.")
            print()
            for menu_no, a in enumerate(ATTACKS, start=1):
                status = "VULNERABLE" if states[a["env_key"]] else "SECURE"
                print(f"  {menu_no:<4} {a['name']:<44} {status}")
            print("=" * 68)
            print("\n  Sistem başlatılıyor...\n")
            sys.exit(0)

        elif choice == "Q":
            print("\n  Çıkılıyor.")
            sys.exit(1)

        else:
            print("  Geçersiz komut.")
            input("  [Enter]")


if __name__ == "__main__":
    main()
