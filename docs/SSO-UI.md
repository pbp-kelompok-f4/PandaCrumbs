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
memberi hak staff/admin. Data domain tetap mengikuti pemilik akun. Logout
aplikasi mengakhiri sesi PandaCrumbs saja, bukan sesi pusat SSO UI.

Pengujian: python manage.py test ui_sso. Respons verifikasi CAS disimulasikan
pada transport HTTP; pengujian ini bukan bukti izin callback produksi.
