# Food Waste Audit — Fayiz

Catatan makanan terbuang pribadi di `/waste-audit/`. Semua halaman memerlukan
login. Nama makanan, jumlah, satuan, tanggal, alasan, dan estimasi kerugian
disimpan dalam `FoodWasteLog`. Setiap catatan terhubung ke pemilik akun.

## Perilaku fitur

- Tambah, lihat, ubah, dan hapus catatan milik sendiri. Hapus selalu memerlukan
  konfirmasi; membuka halaman konfirmasi belum menghapus data.
- Cari nama makanan di riwayat melalui **Enter** atau **Terapkan**. Pencarian
  memakai kata utuh tanpa membedakan huruf besar/kecil: `ayam` cocok dengan
  `Ayam goreng` dan `Sup ayam`, tetapi tidak dengan `Bayam`. `goreng` cocok
  dengan `Mi goreng` dan `Ayam goreng`. Beberapa kata harus semuanya ditemukan,
  dengan urutan bebas: `goreng ayam` juga cocok dengan `Ayam goreng`.
  Tanda baca memisahkan kata, misalnya `Ayam-suwir` cocok dengan `ayam`.
  Tidak ada batas tiga hasil pencarian;
  batas tiga hanya berlaku pada peringkat makanan paling sering terbuang.
- Pencarian dapat digabung dengan tanggal awal/akhir (inklusif) dan alasan.
  **Reset filter** membersihkan semua filter. Ringkasan dan peringkat selalu
  mengikuti catatan yang ditampilkan, bukan seluruh pengguna.
- Filter dan CRUD memakai AJAX tanpa memuat ulang halaman. Formulir biasa tetap
  tersedia melalui URL. Validasi gagal mempertahankan isian dan menampilkan error.
- Jumlah harus positif, kerugian tidak negatif, tanggal tidak di masa depan.
  Kerugian kosong berarti belum diketahui, berbeda dari Rp0. Kerugian adalah
  total per catatan; jumlah dengan satuan berbeda tidak dijumlahkan.
- Open Food Facts menjadi referensi makanan kemasan dengan filter kategori.
  Pilihan produk mengisi nama makanan. Input manual tetap tersedia jika API gagal.
  Layanan bersama memakai cache satu jam, timeout, dan pembatasan jeda pencarian.
- Frekuensi makanan dihitung berdasarkan kejadian, bukan berat atau kerugian.
  Modul tidak otomatis mengurangi stok Pantry.

## Peta kode untuk demo

| Berkas | Fungsi |
| --- | --- |
| `waste_audit/models.py` | Struktur data, pemilik, validasi model, constraint database |
| `waste_audit/forms.py` | Form input dan validasi filter termasuk `q` |
| `waste_audit/views.py` | Batas pemilik, pencarian `food_name__iregex` dengan batas kata dan input yang di-escape, CRUD, agregasi |
| `waste_audit/urls.py` | Alamat daftar, tambah, ubah, hapus |
| `waste_audit/templates/waste_audit/` | HTML daftar, formulir, dialog, ringkasan |
| `waste_audit/static/waste_audit/audit.js` | Fetch AJAX, dialog, loading, error, fokus keyboard |
| `waste_audit/static/waste_audit/audit.css` | Tata letak, warna, responsivitas, reduced motion |
| `main/products.py` | Integrasi Open Food Facts bersama, cache dan penanganan kegagalan |

## Menjalankan salinan demo lokal

Jalankan dari terminal PowerShell VS Code. Interpreter dipinjam dari lingkungan
virtual yang sudah tersedia di folder sebelah.

```powershell
cd "$env:USERPROFILE\Downloads\PandaCrumbs-demo"
$auditPython = '..\PandaCrumbs-publish\.venv\Scripts\python.exe'
& $auditPython manage.py check
& $auditPython manage.py runserver 127.0.0.1:8011
```

Buka `http://127.0.0.1:8011/waste-audit/`. Hentikan server dengan Ctrl+C.
Untuk instalasi baru, pasang `requirements-dev.txt` dan jalankan `migrate`.
Data sintetis opsional: `python manage.py seed_audit_demo` (hanya mode DEBUG).

## Pengujian yang dapat diulang

```powershell
& $auditPython manage.py test waste_audit
$env:COVERAGE_FILE = Join-Path $env:TEMP 'pandacrumbs-audit.coverage'
& $auditPython -m coverage run --branch --source=waste_audit --omit='*/test*.py,*/tests/*,*/migrations/*,*/browser_tests.py' manage.py test waste_audit
& $auditPython -m coverage report -m
```

Tes browser terpisah menggunakan Node.js, Playwright, Chrome, server lokal
sementara, dan database tes. Tes ini tidak memakai atau mengubah data akun demo.
Jika Playwright belum tersedia, pasang dalam folder lokal khusus:

```powershell
npm install --prefix .browser-tests --no-save --package-lock=false playwright
$env:NODE_PATH = Join-Path $PWD '.browser-tests\node_modules'
& $auditPython manage.py test waste_audit.browser_tests
```

Chrome harus terpasang. Untuk Edge: `$env:AUDIT_BROWSER_CHANNEL = 'msedge'`.
Jika Node tidak berada di PATH, atur `AUDIT_NODE_BIN` ke lokasi `node.exe`.
Folder `.browser-tests` berisi dependensi lokal; jangan sertakan saat commit.

## Bukti dan batas penilaian

Verifikasi lokal 29 Oktober 2026: **59 tes modul lulus**, cakupan kode Python
aplikasi modul **180 statement dan 40 cabang, seluruhnya tercakup (100%)**.
Pengukuran mengecualikan tes dan migrasi; tidak mengukur cakupan JavaScript/CSS.
Tes browser terpisah juga lulus: pencarian, Enter, reset, privasi riwayat, AJAX
CRUD, validasi server, fokus keyboard, lebar 390/320 px, dan pengalihan tamu.
Tes browser tidak memanggil Open Food Facts; kegagalan/cache API diuji terpisah
di tes aplikasi `main`.

| Rubrik | Bukti yang tersedia / yang perlu disiapkan |
| --- | --- |
| CRUD | Create/read/update/delete, validasi, constraint, dan filter gabungan diuji |
| Interaktivitas | Semua CRUD dan filter AJAX; diuji lewat browser asli |
| Otorisasi | Login, owner server-side, CSRF, dan isolasi antar pengguna diuji |
| Testing | Coverage >90% dan tes fungsional; nilai TDD memerlukan riwayat red–green–refactor nyata |
| Desain | Responsif, fokus keyboard, reduced motion; konsistensi seluruh modul tetap tugas kelompok |
| API | Cache, timeout, kategori, pesan kegagalan; siapkan demo API nyata jika jaringan tersedia |
| Git | Pemilik mengerjakan commit/PR; siapkan bukti review rekan dan checkpoint |
| Deployment | Perlu cek situs publik dan alur modul pada versi yang sudah dideploy |
| Demo | Latih alur request → view → form/model → database → HTML/JSON; nilai tidak dijamin oleh tes |

## Penggunaan AI dan keterbatasan

ChatGPT/Codex membantu analisis, penyusunan kode, perbaikan, dokumentasi, dan
pengujian modul. Prompt membatasi pekerjaan pada modul audit lokal dan meminta
verifikasi perilaku serta akses pemilik. Perbaikan yang dilakukan mencakup
pencarian yang sempat memakai variabel Pantry, field model ganda, serta fokus
keyboard setelah AJAX. Keluaran AI tetap perlu diperiksa dan dipahami pengembang;
coverage penuh tidak membuktikan bebas bug, semua perangkat kompatibel, atau
layanan eksternal selalu tersedia. Commit, review, dan publikasi dilakukan pemilik.
