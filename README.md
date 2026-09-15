# Project-PandaCrumbs

## Nama Aplikasi: PandaCrumbs

Kelas: F
Kelompok: 4

Anggota Kelompok:
Muhammad Gathfaan Nur Aziz Suhendar (2506609214)
Malvin Lionard
Rakhel Aqeela hapsari Ariwibowo
Mohammad Adzka Aulia (2506657005)
Fayiz Mahardika Ghulam Afandi (2506617374)

## Deskripsi Aplikasi:

PandaCrumbs adalah platform berbasis web yang berfokus pada pengurangan food waste melalui pengelolaan makanan yang lebih terencana, pemanfaatan bahan sisa, serta pembentukan kebiasaan konsumsi yang lebih berkelanjutan. Aplikasi ini ditujukan terutama bagi mahasiswa, anak kos dan individu yang mengelola makanan sendiri, namun tetap dapat digunakan oleh masyarakat umum. PandaCrumbs membantu pengguna mencatat stok makanan, memantau tanggal kedaluwarsa, menemukan resep dari bahan yang tersedia, mencatat makanan yang terbuang, membagikan makanan berlebih yang masih layak konsumsi, serta mengikuti tantangan zero-waste.  Melalui fitur-fitur tersebut, PandaCrumbs bertujuan membantu pengguna mengurangi jumlah makanan yang terbuang sekaligus meningkatkan kesadaran terhadap dampak finansial dan lingkungan dari food waste.

Dengan menghubungkan proses penyimpanan, pemanfaatan, pencatatan, berbagi dan pembentukan kebiasaan dalam satu platform, PandaCrumbs diharapkan dapat membantu pengguna membangun pola konsumsi makanan yang lebih efesien.

## Daftar Modul Rencana: 

### Modul Smart Pantry & Expiry Tracker (Gathfaan)
Manajemen inventaris makanan dengan fitur tracker kadaluarsa otomatis 

CRUD:
Create
Menambah bahan makanan ke dalam kulkas atau storage melalui formulir input atau menggunakan auto-complete API. 
Read
Menampilkan daftar stok bahan makanan. Daftar stok dikelompokkan berdasarkan lokasi simpan dan status urgensi masa simpan (Aman, Hampir Basi, dan Kadaluarsa)
Update
Memperbaharui atribut-atribut yang terdapat pada bahan makanan, seperti jumlah stok, tanggal kadaluarsa, tanggal dan waktu masuk bahan makanan.
Delete
Menghapus item bahan makanan dengan sekali klik “Tandai Habis Dikonsumsi”. 

Interaktivitas AJAX:
Filter instan kategori tanpa reload halaman
Terdapat tombol quick-consume berbasis AJAX untuk mengurangi kuantitas atau menghapus item.
	Integrasi API: Open Food Facts API untuk metadata bahan makanan secara otomatis
	Filter Autentikasi: Data inventaris hanya bisa diakses dan dikelola oleh pemilik akun
yang telah login. Bersifat strictly private.
	
### Modul Leftover Recipe (Malvin)
Membantu pengguna menemukan cara mengolah bahan yang sudah tersedia melalui resep yang dibuat komunitas.
Data utama: judul resep, daftar bahan dan takaran, langkah memasak, porsi, serta pembuat.
Create: menambahkan resep.
Read: melihat daftar dan detail resep.
Update: mengubah resep milik sendiri.
Delete: menghapus resep milik sendiri.
AJAX: mencari resep berdasarkan bahan yang dipilih dan menambah atau menghapus bookmark.
API: menampilkan pilihan produk Open Food Facts sebagai referensi bahan kemasan, dengan filter kategori. Resep disimpan dalam database aplikasi.
Akses: resep dapat dibaca publik; pembuatan resep dan bookmark memerlukan login. Bookmark bersifat pribadi.


### Modul Food Waste Audit (Fayiz)
Membantu pengguna mengenali makanan yang sering terbuang, penyebabnya, dan perkiraan kerugian uang.
Data utama: makanan, jumlah terbuang, satuan, tanggal, alasan, dan perkiraan nilai kerugian.
Create: menambahkan catatan makanan terbuang.
Read: melihat riwayat dan ringkasan kerugian pribadi.
Update: mengoreksi isi catatan.
Delete: menghapus catatan yang keliru.
AJAX: memfilter catatan berdasarkan periode atau alasan dan memperbarui ringkasan.
API: menampilkan referensi produk Open Food Facts yang dapat difilter menurut kategori saat mencatat makanan kemasan.
Akses: catatan dan ringkasan hanya dapat diakses pemiliknya.


### Modul Community Food Sharing (Adzka)
Mempertemukan pengguna yang memiliki makanan berlebih dengan pengguna yang ingin mengambilnya.
CRUD:
Data utama: nama makanan, deskripsi, jumlah atau porsi, batas waktu pengambilan, lokasi, pemberi, dan status penawaran.
Create: membuat penawaran makanan.
Read: melihat daftar dan detail penawaran.
Update: mengubah informasi serta status penawaran milik sendiri.
Delete: menghapus penawaran yang belum diklaim.
AJAX: mengajukan klaim melalui modal dan memperbarui status ketersediaan.
API: menyediakan referensi produk Open Food Facts dengan filter kategori untuk penawaran makanan kemasan. Peta berbasis OpenStreetMap menjadi fitur tambahan.
Akses: ringkasan penawaran dapat dibaca publik; klaim memerlukan login. Kontak dan detail titik jemput dibatasi kepada pemberi dan penerima yang disetujui.


### Modul Habit Challenge (Rakhel)
Membantu pengguna menjalankan target pribadi, misalnya menghabiskan bahan yang tersedia sebelum membeli kembali.
Data utama: rencana tantangan pribadi, target, kategori makanan sasaran, periode, serta catatan check-in.
Create: membuat rencana tantangan pribadi.
Read: melihat tantangan aktif, riwayat, dan progres.
Update: mengubah target atau periode tantangan.
Delete: menghapus rencana tantangan.
AJAX: melakukan check-in harian dan memperbarui progres serta streak.
API: menampilkan referensi produk Open Food Facts yang difilter berdasarkan kategori makanan sasaran tantangan.
Akses: rencana dan progres hanya dapat dikelola oleh pemiliknya.
Streak dihitung dari check-in; nilainya tidak diubah langsung oleh pengguna.

## Public API yang dipakai:
Open Food Facts API (https://world.openfoodfacts.org/api/v2/)
Kami menggunakan API Open Food Facts di modul “Smart Pantry” untuk fitur auto-complete data produk pangan kemasan lokal.
Saat pengguna mengetik nama bahan makanan atau memindai barcode dari produk mereka, sistem akan mengambil data nama standar, kategori pangan, estimasi umur simpan, serta nilai Eco-Score / Nutri-Score secara asinkron menggunakan AJAX.
OpenStreetMap atau Nominatim API (https://nominatim.openstreetmap.org/) dan Leaflet.js
Kami menggunakan OpenStreetMap di modul “Community Food Sharing & Claim” untuk membantu geocoding alamat dan visualisasi titik jemput.
Nantinya, nama jalan atau alamat penjemputan akan diubah menjadi koordinat latitude dan longitude, dan merender peta interaktif penjemputan donasi makanan.

## Peran Pengguna: 
Aplikasi mengimplementasikan sistem multi-peran dengan batasan hak akses yang jelas:

### Pengguna Terdaftar (Household / Student User): yang sudah memiliki akun dan login di aplikasi/website
Mengelola inventaris dapur pribadi (Smart Pantry).
Menjelajahi, mengunggah, dan menandai resep olahan pangan sisa.
Mencatat dan memantau audit pembuangan makanan rumah tangganya
Membuat penawaran donasi makanan dan melakukan klaim paket makanan komunal
Mengikuti tantangan gaya hidup hijau dan melakukan check-in streak harian.
### Pengguna Publik / Tamu (Unauthenticated User): pengguna guest yang tidak login ke aplikasinya
Menjelajahi katalog resep olahan bahan sisa (dengan menggunakan fitur read-only).
Melihat feed makanan berlebih yang tersedia untuk dibagikan di sekitar.
Melihat papan peringkat (leaderboard) tantangan zero-waste komunitas.
### Administrator:
Memvalidasi laporan postingan makanan berlebih yang mencurigakan.
Mengelola master kategori bahan pangan dan kurasi resep rekomendasi.

