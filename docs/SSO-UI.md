# SSO UI opsional

Halaman /accounts/login/ menyediakan login biasa dan tombol Masuk dengan SSO UI.
Password UI dimasukkan di situs UI; aplikasi memverifikasi tiket CAS 2.0 dengan
python-cas. Username terverifikasi dipetakan ke akun aplikasi melalui UIIdentity.
Akun lokal tidak otomatis digabung berdasarkan username atau email.

SSO aktif otomatis saat DEBUG=true dan mati secara default dalam produksi.
SSO_UI_ENABLED=false pada .env menonaktifkan tombol dan endpoint SSO.
SSO_UI_SERVER_URL dapat mengatur base URL HTTPS pada domain sso.ui.ac.id.
Endpoint contoh https://sso.ui.ac.id/cas2/ menampilkan label DEV saat pemeriksaan
25 Oktober 2026. Konfirmasikan endpoint dan callback yang diizinkan sebelum
mengaktifkannya pada produksi.

Callback: /accounts/sso/ui/callback/?state=... pada host dan port yang dipakai.
Gunakan hostname yang sama selama alur login. State acak berlaku 10 menit,
diperiksa terhadap sesi browser, dan hanya dapat digunakan sekali. Klien tetap
memverifikasi sertifikat TLS serta menolak redirect saat validasi tiket.
User-Agent mengidentifikasi aplikasi PandaCrumbs karena gateway UI menolak
User-Agent bawaan requests dengan HTTP 400 saat pemeriksaan.

Akun SSO memiliki password lokal yang tidak dapat dipakai. Klaim SSO tidak
memberi hak staff/admin. Data domain tetap mengikuti pemilik akun. Sesi PandaCrumbs berakhir setelah 30 menit tanpa permintaan ke aplikasi.
Setiap permintaan aktif memperbarui masa berlaku sesi, termasuk polling jika ada.
Tombol Keluar menerima POST dengan CSRF dan langsung menghapus sesi lokal.
Untuk akun UIIdentity, browser kemudian diarahkan ke endpoint /cas2/logout
pada server UI yang dikonfigurasi. Logout pusat ini dapat memengaruhi layanan
UI lain. Login biasa tetap keluar ke beranda PandaCrumbs.
Jika server UI tidak dapat dijangkau, sesi lokal tetap sudah berakhir, tetapi
sesi pusat UI mungkin belum berakhir. Durasi sesi pusat UI diatur oleh UI;
berakhirnya sesi lokal karena tidak aktif tidak otomatis mengakhiri sesi pusat.
Tidak ada pemaksaan login ulang melalui renew. Setelah logout pusat berhasil,
login SSO berikutnya seharusnya meminta autentikasi kembali.
Restart server lokal setelah mengubah konfigurasi ini. Sesi lama yang masih
aktif akan mengikuti durasi baru setelah permintaan berikutnya.

Pengujian: python manage.py test ui_sso. Respons verifikasi CAS disimulasikan
pada transport HTTP; pengujian ini bukan bukti izin callback produksi.
