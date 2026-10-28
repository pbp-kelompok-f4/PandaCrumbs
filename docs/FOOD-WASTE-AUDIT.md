# Food Waste Audit

Catatan pribadi di /waste-audit/. Login diperlukan untuk seluruh halaman.
Pengguna dapat menambah, melihat, mengedit, dan menghapus catatan miliknya.

Data: nama makanan, jumlah positif, satuan, tanggal terbuang (tidak di masa
depan), alasan, serta perkiraan total kerugian per catatan. Nilai kosong berbeda
dari Rp0. Kuantitas dengan satuan berbeda tidak dijumlahkan.

Filter tanggal inklusif dan alasan memperbarui riwayat serta ringkasan melalui
AJAX. Ringkasan mencakup jumlah kejadian, kerugian yang diketahui, alasan paling
sering, serta makanan paling sering dicatat. Frekuensi dihitung per kejadian.

Open Food Facts memakai endpoint pencarian bersama dan filter kategori.
Memilih produk hanya mengisi nama makanan; input manual tetap tersedia ketika
API gagal. Modul ini tidak mengurangi stok pantry secara otomatis.

Setelah memasang dependensi, jalankan migrate. Data contoh lokal opsional:

```powershell
python manage.py seed_demo
python manage.py seed_audit_demo
```

seed_demo meminta password baru untuk akun demo. seed_audit_demo hanya tersedia
dengan DEBUG aktif. Keduanya menambahkan data sintetis.

Pengujian: python manage.py test waste_audit
