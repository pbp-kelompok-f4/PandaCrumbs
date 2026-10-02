# Design system PandaCrumbs

Sumber: [Figma](https://www.figma.com/design/2iKWKXaQK0sTRMc11aJH2J/Untitled). Implementasi memakai template Django dan CSS bersama, bukan komponen React dari hasil ekspor.

| Token | Nilai | Penggunaan |
|---|---|---|
| Cream | `#FAF6EE` | Latar halaman |
| Ink | `#2D1F1F` | Judul dan teks utama |
| Terracotta | `#D97450` | Tombol utama dan status mendekati kedaluwarsa |
| Olive | `#6E7E55` | Brand, autentikasi, status aman |
| Sage | `#DCE6C9` | Filter aktif, chip |
| Dusty pink | `#DFB2BC` | Ringkasan kartu resep |
| Danger | `#AB3737` | Status kedaluwarsa, hapus |
| Gloock | 400 | Judul halaman dan resep |
| Inter | 400–800 | Navigasi, formulir, tombol |
| Poppins | 600 | Kartu pantry |

Sumber token: `main/static/main/css/app.css`. Font disimpan di `main/static/main/fonts/`. Tailwind 2.2.19 disimpan sebagai stylesheet siap pakai dari distribusi resminya, menggantikan runtime CDN landing page awal. Tidak ada langkah build Node untuk menjalankan Django.

Komponen bersama: header/navigation pill, status badge, tombol primary/outline, chip, form field dan error, empty state, toast, account menu, serta footer. Daftar kartu memakai grid tiga kolom di desktop, dua kolom di tablet, satu kolom di ponsel. Navigasi ponsel memakai tombol Menu dengan `aria-expanded`. Form dan aksi utama tetap bekerja dengan POST/GET biasa saat JavaScript dimatikan; AJAX menjadi peningkatan interaksi.

## Pemetaan aset

- Logo `pantryDesign-imgCopySvg12.png`: header, 58 × 67 px desktop.
- Placeholder `pantryDesign-imgImage1.png`: tiga kartu pantry seed, mengikuti crop Figma.
- `recipeDesign-imgImage1.png`: placeholder kartu Nasi Goreng Sayur; file berbeda dari foto pada halaman detail, sesuai frame sumber.
- `recipeDesign-imgTelurDadarWortel.png`, `recipeDesign-imgPudingRotiTawar.png`: foto bulat resep, diameter luar 208 px.
- `recipeDesign-imgRectangle21.svg`: bingkai tombol tambah resep, ukuran intrinsik 250 × 58 px.
- `recipeDesign-imgContainer.svg`: ikon privat. `Container1.svg` dan `Container2.svg`: bookmark aktif/nonaktif. `imgButtonHapusNasi.svg`: hapus chip.
- `39-2897-imgNasiGorengSayur.png`: foto detail resep pertama.
- Aset `1-2-*`: latar/overlay dan maskot landing. `16-47-imgFrame9.png`: latar autentikasi.

Aset asli tidak diganti dengan gambar buatan. Gambar dari URL yang dimasukkan pengguna atau API tetap dinamis. Gambar karakter dan foto telur di atas roti adalah aset yang saat ini ada di Figma, meskipun tidak sesuai nama makanan. Ini utang konten desain yang perlu dibereskan tim.

## Penyesuaian fungsional dari mockup

- Hitungan tab, status kedaluwarsa, nama pembuat, dan isi kartu berasal dari database.
- Pantry privat memerlukan login; mockup menampilkan data pantry bersamaan dengan tombol Sign in, tetapi implementasi mengikuti aturan privasi README.
- Avatar memakai inisial akun asli. Belum ada fitur foto profil.
- Input pencarian pantry dan filter lokasi/kategori ditambahkan agar tombol Cari punya fungsi.
- Label formulir “Save shipping information” diganti menjadi “Simpan Bahan Makanan”.
- Google OAuth, lupa password, dan fitur remember dari mockup belum termasuk scope; kontrol tersebut tidak ditampilkan sebagai tombol palsu.
- Figma belum menyediakan form tambah/edit resep; form memakai komponen bersama dan token yang sama.

Sumber pustaka: [Tailwind CSS MIT](https://github.com/tailwindlabs/tailwindcss/blob/v2.2.19/LICENSE), [Google Fonts](https://fonts.google.com/). Aset Figma mengikuti hak penggunaan yang dimiliki tim terhadap file desain.
