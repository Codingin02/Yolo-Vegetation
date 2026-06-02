from __future__ import annotations


def main() -> int:
    print("PHASE13 Secure Capture Options")
    print("")
    print("1. LAN HTTP mode")
    print("   URL: http://<IP-LAPTOP>:5000/field-capture")
    print("   Fungsi: upload file/foto dan input manual provisional.")
    print("   Catatan: kamera/GPS otomatis di Chrome HP bisa diblokir karena bukan HTTPS.")
    print("")
    print("2. HTTPS tunnel mode optional")
    print("   Gunakan ngrok/cloudflared manual jika perlu secure context.")
    print("   Jangan simpan token/authtoken/credential ke Git.")
    print("   URL contoh setelah tunnel: https://<subdomain>.ngrok-free.app/field-capture")
    print("")
    print("3. File upload fallback mode")
    print("   Ambil foto dengan kamera HP biasa, lalu upload file di halaman field capture.")
    print("   GPS bisa diisi manual jika browser tidak memberi izin.")
    print("")
    print("Ini tetap halaman Flask field capture, bukan aplikasi mobile/APK/PWA standalone.")
    print("PHASE13_SECURE_CAPTURE_OPTIONS_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
