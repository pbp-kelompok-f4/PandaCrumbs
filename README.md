# Project-PandaCrumbs

## Nama Aplikasi: PandaCrumbs

## Kelas: F
## Kelompok: 4

## Anggota Kelompok:

1. Muhammad Gathfaan Nur Aziz Suhendar (2506609214)
2. Malvin Lionard (2506591753)
3. Rakhel Aqeela Hapsari Ariwibowo (2506605462)
4. Mohammad Adzka Aulia (2506657005)
5. Fayiz Mahardika Ghulam Afandi (2506617374)

## Deskripsi Aplikasi:

PandaCrumbs adalah platform berbasis web yang berfokus pada pengurangan food waste melalui pengelolaan makanan yang lebih terencana, pemanfaatan bahan sisa, serta pembentukan kebiasaan konsumsi yang lebih berkelanjutan. Aplikasi ini ditujukan terutama bagi mahasiswa, anak kos dan individu yang mengelola makanan sendiri, namun tetap dapat digunakan oleh masyarakat umum. PandaCrumbs membantu pengguna mencatat stok makanan, memantau tanggal kedaluwarsa, menemukan resep dari bahan yang tersedia, mencatat makanan yang terbuang, membagikan makanan berlebih yang masih layak konsumsi, serta mengikuti tantangan zero-waste.  Melalui fitur-fitur tersebut, PandaCrumbs bertujuan membantu pengguna mengurangi jumlah makanan yang terbuang sekaligus meningkatkan kesadaran terhadap dampak finansial dan lingkungan dari food waste.

Dengan menghubungkan proses penyimpanan, pemanfaatan, pencatatan, berbagi dan pembentukan kebiasaan dalam satu platform, PandaCrumbs diharapkan dapat membantu pengguna membangun pola konsumsi makanan yang lebih efesien.

## Daftar Modul Rencana: 

### Modul Smart Pantry & Expiry Tracker (Gathfaan)
Manajemen inventaris makanan dengan fitur tracker kadaluarsa otomatis 

- Data utama: nama makanan, jumlah stok, tanggal kadaluarsa, tanggal masuk penyimpanan, lokasi simpan, dan jenis makanan.
- Create: Menambah bahan makanan ke dalam kulkas atau storage melalui formulir input atau menggunakan auto-complete API.
- Read: Menampilkan daftar stok bahan makanan. Daftar stok dikelompokkan berdasarkan lokasi simpan dan status urgensi masa simpan (Aman, Hampir Basi, dan Kadaluarsa)
- Update: Memperbaharui atribut-atribut yang terdapat pada bahan makanan, seperti jumlah stok, tanggal kadaluarsa, tanggal dan waktu masuk bahan makanan.
- Delete: Menghapus item bahan makanan dengan sekali klik “Tandai Habis Dikonsumsi”.
- Interaktivitas AJAX:
  - Filter instan kategori tanpa reload halaman
  - Terdapat tombol quick-consume berbasis AJAX untuk mengurangi kuantitas atau menghapus item.
- Integrasi API: Open Food Facts API untuk metadata bahan makanan secara otomatis
- Filter Autentikasi: Data inventaris hanya bisa diakses dan dikelola oleh pemilik akun
yang telah login. Bersifat strictly private.
	
### Modul Leftover Recipe (Malvin)
Membantu pengguna menemukan cara mengolah bahan yang sudah tersedia melalui resep yang dibuat komunitas.

- Data utama: judul resep, daftar bahan dan takaran, langkah memasak, porsi, serta pembuat.
- Create: menambahkan resep.
- Read: melihat daftar dan detail resep.
- Update: mengubah resep milik sendiri.
- Delete: menghapus resep milik sendiri.
- AJAX: mencari resep berdasarkan bahan yang dipilih dan menambah atau menghapus bookmark.
- API: menampilkan pilihan produk Open Food Facts sebagai referensi bahan kemasan, dengan filter kategori. Resep disimpan dalam database aplikasi.
- Akses: resep dapat dibaca publik; pembuatan resep dan bookmark memerlukan login. Bookmark bersifat pribadi.


### Modul Food Waste Audit (Fayiz)
Membantu pengguna mengenali makanan yang sering terbuang, penyebabnya, dan perkiraan kerugian uang.

- Data utama: makanan, jumlah terbuang, satuan, tanggal, alasan, dan perkiraan nilai kerugian.
- Create: menambahkan catatan makanan terbuang.
- Read: melihat riwayat dan ringkasan kerugian pribadi.
- Update: mengoreksi isi catatan.
- Delete: menghapus catatan yang keliru.
- AJAX: memfilter catatan berdasarkan periode atau alasan dan memperbarui ringkasan.
- API: menampilkan referensi produk Open Food Facts yang dapat difilter menurut kategori saat mencatat makanan kemasan.
- Akses: catatan dan ringkasan hanya dapat diakses pemiliknya.


### Modul Community Food Sharing (Adzka)
Mempertemukan pengguna yang memiliki makanan berlebih dengan pengguna yang ingin mengambilnya.

- Data utama: nama makanan, deskripsi, jumlah atau porsi, batas waktu pengambilan, lokasi, pemberi, dan status penawaran.
- Create: membuat penawaran makanan.
- Read: melihat daftar dan detail penawaran.
- Update: mengubah informasi serta status penawaran milik sendiri.
- Delete: menghapus penawaran yang belum diklaim.
- AJAX: mengajukan klaim melalui modal dan memperbarui status ketersediaan.
- API: menyediakan referensi produk Open Food Facts dengan filter kategori untuk penawaran makanan kemasan. Peta berbasis OpenStreetMap menjadi fitur tambahan.
- Akses: ringkasan penawaran dapat dibaca publik; klaim memerlukan login. Kontak dan detail titik jemput dibatasi kepada pemberi dan penerima yang disetujui.


### Modul Habit Challenge (Rakhel)
Membantu pengguna menjalankan target pribadi, misalnya menghabiskan bahan yang tersedia sebelum membeli kembali.

- Data utama: rencana tantangan pribadi, target, kategori makanan sasaran, periode, serta catatan check-in.
- Create: membuat rencana tantangan pribadi.
- Read: melihat tantangan aktif, riwayat, dan progres.
- Update: mengubah target atau periode tantangan.
- Delete: menghapus rencana tantangan.
- AJAX: melakukan check-in harian dan memperbarui progres serta streak.
- API: menampilkan referensi produk Open Food Facts yang difilter berdasarkan kategori makanan sasaran tantangan.
- Akses: rencana dan progres hanya dapat dikelola oleh pemiliknya.
Streak dihitung dari check-in; nilainya tidak diubah langsung oleh pengguna.

## Public API yang dipakai:

### Open Food Facts API (https://world.openfoodfacts.org/api/v2/)
- Kami menggunakan API Open Food Facts di modul “Smart Pantry” untuk fitur auto-complete data produk pangan kemasan lokal.
- Implementasi CP2 memakai pencarian eksplisit melalui tombol Cari Produk (AJAX), filter kategori, cache satu jam, dan penanganan API gagal. Nama produk, kategori, barcode, serta foto dapat menjadi referensi. Tanggal kedaluwarsa diisi pengguna dari kemasan, bukan diperkirakan dari API. Autocomplete setiap ketikan dan pemindaian barcode belum diimplementasikan.
### OpenStreetMap atau Nominatim API (https://nominatim.openstreetmap.org/) dan Leaflet.js
- Kami menggunakan OpenStreetMap di modul “Community Food Sharing & Claim” untuk membantu geocoding alamat dan visualisasi titik jemput.
- Nantinya, nama jalan atau alamat penjemputan akan diubah menjadi koordinat latitude dan longitude, dan merender peta interaktif penjemputan donasi makanan.

## Peran Pengguna: 
Aplikasi mengimplementasikan sistem multi-peran dengan batasan hak akses yang jelas:

### Pengguna Terdaftar (Household / Student User): 
yang sudah memiliki akun dan login di aplikasi/website
- Mengelola inventaris dapur pribadi (Smart Pantry).
- Menjelajahi, mengunggah, dan menandai resep olahan pangan sisa.
- Mencatat dan memantau audit pembuangan makanan rumah tangganya
- Membuat penawaran donasi makanan dan melakukan klaim paket makanan komunal
- Mengikuti tantangan gaya hidup hijau dan melakukan check-in streak harian.
### Pengguna Publik / Tamu (Unauthenticated User): 
pengguna guest yang tidak login ke aplikasinya
- Menjelajahi katalog resep olahan bahan sisa (dengan menggunakan fitur read-only).
- Melihat feed makanan berlebih yang tersedia untuk dibagikan di sekitar.
- Melihat papan peringkat (leaderboard) tantangan zero-waste komunitas.
### Administrator:
- Memvalidasi laporan postingan makanan berlebih yang mencurigakan.
- Mengelola master kategori bahan pangan dan kurasi resep rekomendasi.


## Desain dan status CP2 — 1 Oktober 2026

- [Figma PandaCrumbs](https://www.figma.com/design/2iKWKXaQK0sTRMc11aJH2J/Untitled)
- Frame utama: Smart Pantry `27:602`, Leftover Recipe `27:654`, detail resep `39:2897`, formulir pantry `37:1205`.
- Modul 1 dan 2 telah tersedia lokal: CRUD, autentikasi, filter database/AJAX, quick-consume, bookmark pribadi, dan referensi produk Open Food Facts.
- Template bersama: `templates/base.html`, `components/header.html`, `components/footer.html`, `components/fields.html`.
- Modul 3–5 masih rencana. Navigasi modul tersebut belum aktif.
- Deployment PWS: **belum diverifikasi dalam pengerjaan lokal ini**. Host yang sebelumnya tercantum di settings: https://malvin-lionard-pandacrumbs.pws.cs.ui.ac.id/ . Jangan menganggapnya sebagai bukti deployment berhasil.
- Seed CP2 menyediakan **3 bahan + 3 resep**, bukan 50 data utama. Persyaratan data final masih perlu diselesaikan.
- Gambar karakter pada beberapa kartu berasal langsung dari placeholder Figma. Ganti dengan foto makanan yang sesuai sebelum pengumpulan final.

## Menjalankan lokal

Python 3.12+ direkomendasikan; implementasi ini diuji dengan Python 3.14 dan Django 5.2.17.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

`seed_demo` meminta password untuk akun `demo` baru. Akun yang sudah ada tidak diubah passwordnya. Jalankan ulang perintah ini tanpa menduplikasi data. Pada Windows, aktivasi environment memakai `.venv\Scripts\activate`.

- Beranda: http://127.0.0.1:8000/
- Pantry pribadi: http://127.0.0.1:8000/pantry/
- Resep publik: http://127.0.0.1:8000/recipes/
- Pendaftaran akun: http://127.0.0.1:8000/accounts/register/

Foto produk dari API memerlukan internet. Font, stylesheet, JavaScript, dan aset Figma sudah disimpan lokal. Data produk dicari hanya saat pengguna menekan tombol; tidak ada request API per ketikan. Respons API di-cache satu jam dan pencarian baru dibatasi dengan jeda tujuh detik untuk deployment satu host. Untuk beberapa host, gunakan cache bersama dengan rate limiter atomik.

## Pengujian

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
coverage run --source=main,pantry,recipes manage.py test main pantry recipes
coverage report --omit='*/tests.py,*/migrations/*'
python manage.py collectstatic --noinput
```

28 tes backend lulus. Coverage baris Python aplikasi `main`, `pantry`, dan `recipes` sebesar 99% (tes dan migrasi dikecualikan). Angka ini **bukan coverage frontend atau seluruh proyek final**. Uji browser terpisah memeriksa CRUD, filter AJAX, bookmark, data privat, asset loading, dan layout empat lebar layar. Integrasi Open Food Facts juga diuji dengan request nyata.

## Persiapan deployment PWS

1. Gunakan environment baru dari `requirements.txt`. Environment Windows `env/`, bytecode, dan SQLite tidak lagi dilacak Git.
2. Atur secret production yang unik, `DJANGO_DEBUG=false`, host dan origin HTTPS yang benar. Jangan commit `.env`.
3. Bila memakai database ITF, isi `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`; konfigurasi PostgreSQL memakai schema `tugas_kelompok`. Pastikan schema tersedia dan akun DB memiliki izin yang diperlukan.
4. Aktifkan `TRUST_PROXY_HTTPS=true` hanya bila reverse proxy PWS menjamin header `X-Forwarded-Proto` dibersihkan dan diatur oleh proxy.
5. Jalankan `migrate`, `collectstatic --noinput`, dan `check --deploy` di environment deployment. Jalankan WSGI melalui Gunicorn/konfigurasi PWS yang berlaku.
6. Periksa URL PWS dari browser, login, static files, koneksi DB, serta persistensi setelah restart. Baru nyatakan deployment CP2 selesai.

Deployment dikirim langsung ke remote `pws`; tidak ada push atau PR GitHub.

Lihat [rundown CP2](docs/CP2-RUNDOWN.md) dan [design system](docs/DESIGN-SYSTEM.md).

## Lokasi implementasi utama

Hasil CP2 ada di repo asli pada branch `master`. Target deployment: https://mohammad-adzka-pandacrumbs.pws.cs.ui.ac.id/. PWS auto-build menjalankan migrasi dan Gunicorn sendiri, tetapi tidak menjalankan Procfile atau collectstatic. Karena itu WhiteNoise memakai `WHITENOISE_USE_FINDERS=True` dan StaticFilesStorage tanpa manifest, mengikuti Tutorial 01 PBP. Script `scripts/start-pws.sh` tetap tersedia untuk hosting yang mendukung Procfile.

Database masih memakai SQLite sementara bila `DB_HOST` belum diisi. Data dalam container tidak boleh dianggap persisten saat redeploy; konfigurasi database ITF dengan schema `tugas_kelompok` masih diperlukan.
