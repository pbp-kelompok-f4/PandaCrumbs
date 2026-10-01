# Rundown pengerjaan CP2

Tanggal: 1 Oktober 2026 (WIB). Fokus: modul 1 Smart Pantry dan modul 2 Leftover Recipe.

## Lokasi dan batas pekerjaan

Pekerjaan awal dibuat di salinan lokal dari commit `84f4ebb`. Atas permintaan lanjutan pengguna, hasil implementasi sudah diterapkan ke repo asli `/Users/adzka/Collage/S3/PBP/PandaCrumbs/` pada branch `main`. Tidak ada commit/push atau pull request. Proyek PWS baru `mohammad.adzka/pandacrumbs-cp2` sudah dibuat, tetapi belum menerima deployment.

Perubahan belum di-commit. Penghapusan file environment/bytecode/database dari pelacakan Git berada di staging; kode implementasi masih berupa perubahan lokal. Review keduanya sebelum membuat commit. Konfigurasi remote repo asli tidak diubah.

## Urutan yang dikerjakan

1. **Audit repo dan tugas.** Membaca README, struktur Django, settings, serta panduan tugas yang dilampirkan. Repo awal berisi landing page dengan formulir autentikasi tanpa pemrosesan backend. Ada 6.199 file environment Windows yang dilacak Git, database SQLite kosong, dan requirements berformat UTF-16.
2. **Ambil desain Figma.** Membaca struktur file, context desain dan screenshot Smart Pantry, Leftover Recipe, detail resep, formulir pantry, landing, serta autentikasi. Mengunduh aset asli dan font untuk penggunaan lokal. Tidak mengubah file Figma.
3. **Fondasi bersama.** Memecah base template, header, footer, field form, pencarian produk, dan tombol bookmark. Menambahkan token warna, tipografi, layout responsif, menu mobile, indikator fokus, state kosong, dan pesan aksi.
4. **Autentikasi.** Registrasi, login, logout POST, validasi password bawaan Django, CSRF, dan redirect setelah login. Avatar memakai inisial akun. Tidak menyediakan tombol Google login atau reset password yang belum memiliki implementasi.
5. **Smart Pantry.** Model milik pengguna, migrasi, tambah/baca/edit/hapus, filter nama/kategori/lokasi/status, tanggal dan stok tervalidasi, quick-consume AJAX. Stok satu yang dikonsumsi dihapus; stok lebih besar dikurangi dengan operasi database. Semua endpoint memeriksa pemilik akun.
6. **Leftover Recipe.** Model resep dan bookmark, CRUD milik penulis, daftar/detail publik, pencarian nama/bahan, filter kombinasi bahan, tab semua/tersimpan/milik sendiri, serta bookmark AJAX yang privat dan idempotent.
7. **Open Food Facts.** Pencarian produk melalui backend dengan filter kategori, timeout, cache satu jam, dan jeda pencarian baru. Pilihan produk mengisi nama/barcode/foto pantry atau menambah referensi bahan resep. Tanggal kedaluwarsa tidak ditebak API.
8. **Konfigurasi lokal/deploy.** Requirements UTF-8, `.env.example`, `.gitignore`, static files melalui WhiteNoise, Gunicorn, mode produksi tanpa hardcoded secret, dan opsi PostgreSQL schema `tugas_kelompok`. Environment Windows, bytecode dan SQLite dikeluarkan dari pelacakan Git pada salinan ini.
9. **Data demo dan verifikasi.** Menambahkan seed idempotent tiga bahan dan tiga resep, 28 tes backend, uji browser alur nyata, pengecekan static files/migrasi, dan screenshot desktop/mobile.

## Hasil pengujian

| Pemeriksaan | Hasil |
|---|---|
| `manage.py check` | Lulus, 0 masalah |
| `makemigrations --check --dry-run` | Tidak ada migrasi tertinggal |
| Migrasi database lokal | Lulus |
| 28 tes backend | Seluruhnya lulus |
| Coverage Python main/pantry/recipes | 99%; tes dan migrasi dikecualikan |
| Pantry lintas akun | Baca dibatasi; edit/hapus/consume pengguna lain menghasilkan 404 |
| Resep lintas akun | Publik dapat membaca; edit/hapus pengguna lain ditolak |
| CSRF dan perubahan lewat GET | Diuji; aksi mutasi dilindungi |
| Bookmark berulang | Tidak membuat duplikasi; bookmark tetap privat |
| API timeout/response invalid/cache/throttle | Diuji dengan mock deterministik |
| Open Food Facts langsung | Berhasil mengembalikan produk |
| Uji browser CRUD pantry/resep | Lulus |
| Uji browser consume, filter AJAX, bookmark | Lulus |
| Lebar 1440, 768, 390, 320 px | Tidak ada overflow horizontal pada halaman yang diperiksa |
| Aset gambar lokal | Terbaca; tidak ada gambar rusak pada halaman yang diperiksa |
| Error JavaScript saat uji | Tidak ditemukan |
| `collectstatic` | Lulus |
| `check --deploy` dengan konfigurasi produksi sementara | Lulus, 0 masalah; bukan bukti deployment PWS |

Coverage tersebut hanya mengukur kode Python yang dikerjakan. Itu tidak membuktikan semua browser, keadaan jaringan, beban paralel, modul 3–5, atau konfigurasi PWS sudah benar.

## Rundown presentasi CP2 — sekitar 8 menit

| Waktu | Demonstrasi | Hal yang dijelaskan |
|---|---|---|
| 0:00–0:45 | Landing dan Figma | Sasaran mahasiswa/anak kos, masalah food waste, pilihan warna/font bersama |
| 0:45–1:30 | Login akun demo | Autentikasi nyata dan perbedaan data publik/pribadi |
| 1:30–3:00 | Smart Pantry | Tambah bahan, filter status/lokasi, update, quick-consume; tunjukkan perubahan tanpa reload |
| 3:00–4:00 | Form pantry | Cari produk Open Food Facts, pilih hasil, isi tanggal dari kemasan |
| 4:00–5:30 | Leftover Recipe | Cari bahan, buka detail, simpan bookmark, cek tab tersimpan |
| 5:30–6:30 | Tambah/edit resep | Form lengkap, data database, hanya penulis yang dapat mengubah |
| 6:30–7:15 | Tampilan mobile dan tes | Grid responsif, menu mobile, ringkasan 28 tes |
| 7:15–8:00 | Status CP2 | Tunjukkan deployment PWS **hanya setelah benar-benar berhasil**; jelaskan sisa kerja |

Akun baru memiliki pantry kosong, sesuai privasi. Gunakan akun demo hasil `seed_demo` bila ingin menampilkan kartu contoh. Jangan menganggap data demo sebagai data milik semua pengguna.

## Yang masih harus diselesaikan

**Untuk menutup CP2:** deploy ke PWS dan verifikasi URL, static files, database, login, serta persistensi. Implementasi lokal dan pemeriksaan konfigurasi belum menggantikan langkah ini. Pastikan tim menyepakati design system, bukan hanya ada file CSS.

**Sebelum pengumpulan akhir:** selesaikan modul 3–5, siapkan minimal 50 data utama yang layak, integrasikan seluruh modul, uji ulang dengan database deployment, perbarui README dengan URL deployment yang sudah diverifikasi, dan ganti aset placeholder makanan di Figma/kode. Kontribusi individu tetap perlu bisa dijelaskan dan diuji oleh pemilik modul.

**Batas implementasi saat ini:** pencarian API melalui tombol, belum barcode scanner/autocomplete; foto memakai URL, belum upload berkas; daftar belum dipaginasi; cache/rate gate ditujukan untuk satu host dan belum menjadi rate limiter atomik lintas server; login belum diberi throttling khusus; Google OAuth dan reset password belum tersedia. Uji concurrency PostgreSQL/PWS belum dilakukan.

**Koreksi asumsi README:** Open Food Facts adalah referensi metadata produk; jangan menjanjikan estimasi kedaluwarsa otomatis untuk setiap produk. Dokumentasi API juga melarang search-as-you-type terhadap endpoint pencarian karena pembatasan request. [Dokumentasi resmi Open Food Facts](https://openfoodfacts.github.io/openfoodfacts-server/api/).
