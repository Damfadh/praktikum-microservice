# Laporan Praktikum Arsitektur Microservice

**Mata kuliah:** Sistem Terdistribusi  
**Topik:** REST API mahasiswa dan mata kuliah dengan Flask, MySQL, PostgreSQL, Nginx, dan Docker Compose  
**Tanggal penyusunan:** 3 November 2026  
**Status:** Sepuluh skenario integrasi terverifikasi lulus berdasarkan keluaran terminal dan screenshot yang diberikan.

## Anggota Kelompok

- Damar Fadhil Widyadhana - 320240401009
- Syahira Febiana Satoto - 320240401028
- Hamzah Khaled Ismail Moghrabi - 320240401013

## 1. Tujuan

Praktikum ini membangun sistem akademik sederhana yang memisahkan layanan mahasiswa dan mata kuliah. Setiap layanan memiliki database sendiri. Nginx menjadi pintu masuk untuk dashboard dan API, sedangkan Docker Compose menjalankan aplikasi dan database sebagai container.

## 2. Arsitektur

```text
Browser / curl
      |
      v
Nginx API Gateway :8080
      |                         |
      v                         v
Mahasiswa Service :5000       Mata Kuliah Service :5000
      |                         |
      v                         v
MySQL mahasiswa_db            PostgreSQL matkul_db
```

Dashboard dan API diakses melalui gateway pada port 8080. Port 5001 dan 5002 dipetakan untuk uji mandiri service. Mahasiswa Service menyimpan data KRS lokal berupa NIM dan kode mata kuliah, lalu meminta detail mata kuliah melalui HTTP ke Mata Kuliah Service. Tidak ada foreign key lintas database.

## 3. Implementasi

- **Mahasiswa Service:** endpoint CRUD mahasiswa dan KRS, validasi data, respons JSON untuk error, pencegahan NIM/KRS duplikat, dan koneksi ke MySQL.
- **Mata Kuliah Service:** endpoint CRUD mata kuliah, validasi data, respons 404 untuk kode yang tidak ditemukan, data awal IF301–IF303, dan koneksi ke PostgreSQL.
- **API Gateway:** routing `/mahasiswa` dan `/matkul` ke service yang sesuai serta penyajian dashboard.
- **Docker Compose:** menjalankan gateway, kedua service, MySQL, dan PostgreSQL; volume database mempertahankan data saat container dimulai ulang.

## 4. Bukti dan Status Pengujian

### 4.1 Bukti screenshot yang tersedia

Screenshot praktikum diindeks pada [evidence/README.md](evidence/README.md). Screenshot Compose menunjukkan image selesai dibangun dan container dibuat, sementara Docker Desktop memperlihatkan grup container praktikum aktif. Log memperlihatkan permintaan `GET /mahasiswa` dan `GET /matkul` berhasil dengan HTTP 200; Nginx menerima permintaan dashboard. Screenshot tambahan merekam hasil skenario 1–10, termasuk `201`, `409`, `404`, `204`, `503`, serta data yang tetap tersedia setelah container dihentikan dan dijalankan kembali.

Satu permintaan `GET /favicon.ico` menghasilkan 404 karena file favicon tidak disediakan. Hal ini tidak mengganggu dashboard atau API. Screenshot dashboard awal memperlihatkan data mahasiswa masih kosong saat gambar diambil.

Pemeriksaan awal pada [evidence/preflight.txt](evidence/preflight.txt) merekam keadaan sebelum WSL selesai disiapkan: Docker Engine belum dapat dihubungi dan `wsl --status` ditolak. Screenshot berikutnya memperlihatkan instalasi WSL selesai dan Docker Desktop aktif, lalu pengujian integrasi dapat dilanjutkan.

Log terminal yang dibagikan kemudian memperlihatkan Mata Kuliah Service sempat gagal pada pemanggilan `db.session.rollback()` di luar application context. Setelah itu log mencatat `Database mata kuliah siap`, Flask aktif, dan `GET /matkul` berstatus 200. Ini membuktikan service akhirnya dapat melayani pembacaan; traceback awal tetap perlu dibersihkan dari kode/image agar startup tidak bergantung pada restart container. Transkripnya ada di [evidence/matkul-service-startup.txt](evidence/matkul-service-startup.txt).

### 4.2 Status pengujian integrasi

Hasil terminal pada screenshot menunjukkan kesepuluh skenario mendapat respons yang diharapkan. Skenario hapus mahasiswa mendapat `204`, lalu query MySQL tidak menemukan baris KRS untuk NIM tersebut. Bukti terminal disimpan pada folder [evidence/](evidence/README.md). Percobaan POST pertama dari CMD memakai kutip tunggal dan menghasilkan `400`; setelah body JSON diperbaiki, tambah mahasiswa berhasil dengan `201`.

Jalankan perintah dari root repositori di CMD. JSON pada `--data-raw` memakai escape backslash dan tanda kutip agar format JSON sampai ke API dengan benar.

| No. | Skenario dan perintah | Hasil yang diharapkan | Hasil aktual |
|---:|---|---|---|
| 1 | `curl.exe -i -X POST http://localhost:8080/mahasiswa -H "Content-Type: application/json" --data-raw "{\"nim\":\"2210001\",\"nama\":\"Budi\"}"` | `201 Created` | **Lulus** — respons `201` dan data Budi diterima; lihat [bukti POST](evidence/test-post-mahasiswa-cmd.txt). |
| 2 | Ulangi perintah skenario 1 | `409 Conflict` karena NIM duplikat | **Lulus** — mendapat `409 Conflict` dan pesan NIM sudah terdaftar. |
| 3 | `curl.exe -i -X POST http://localhost:8080/matkul -H "Content-Type: application/json" --data-raw "{\"kode\":\"IF399\",\"nama\":\"Pengujian Sistem\",\"sks\":3,\"semester\":5}"` | `201 Created` | **Lulus** — mata kuliah IF399 dibuat dengan `201 Created`. |
| 4 | `curl.exe -i -X POST http://localhost:8080/mahasiswa/2210001/matkul -H "Content-Type: application/json" --data-raw "{\"kode_mk\":\"IF301\"}"` | `201 Created` | **Lulus** — KRS IF301 dibuat dengan `201 Created`. |
| 5 | Kirim POST seperti skenario 4 dengan `kode_mk` bernilai `XX999` | `404 Not Found` | **Lulus** — kode XX999 ditolak dengan `404 Not Found`. |
| 6 | Ulangi perintah skenario 4 | `409 Conflict` karena KRS sudah ada | **Lulus** — KRS duplikat ditolak dengan `409 Conflict`. |
| 7 | `curl.exe -i http://localhost:8080/mahasiswa/2210001/matkul` | `200 OK`, daftar KRS memuat detail mata kuliah | **Lulus** — GET KRS memberi `200 OK` dan detail IF301. |
| 8 | `curl.exe -i -X DELETE http://localhost:8080/mahasiswa/2210001` | `204 No Content`; KRS mahasiswa ikut terhapus | **Lulus** — DELETE mendapat `204`; query `SELECT nim, kode_mk FROM krs WHERE nim='2210001'` tidak menemukan baris. Lihat [bukti query](evidence/18-scenario-8-krs-row-removed.png). |
| 9 | Buat kembali mahasiswa `2210001`, jalankan `docker compose stop matkul-service`, lalu kirim POST pengambilan KRS seperti skenario 4 | `503 Service Unavailable`, bukan crash | **Lulus** — saat Matkul Service dihentikan, pengambilan KRS mendapat `503`; service kemudian dinyalakan kembali. |
| 10 | Pastikan ada data mahasiswa dan mata kuliah, jalankan `docker compose down`, lalu `docker compose up -d`; periksa kembali `GET /mahasiswa` dan `GET /matkul` | Data tetap ada karena volume tidak dihapus | **Lulus** — setelah `docker compose down` lalu `up -d`, GET mahasiswa dan GET IF398 sama-sama mendapat `200 OK`. |

Untuk melengkapi skenario 9, setelah merekam respons, hidupkan kembali service dengan `docker compose start matkul-service`. Untuk skenario 10, jangan menambahkan `-v` pada perintah `docker compose down`, karena opsi tersebut menghapus volume database.

## 5. Analisis

### 5.1 Mengapa KRS hanya menyimpan `kode_mk` tanpa foreign key ke mata kuliah?

Data mahasiswa/KRS dan data mata kuliah berada di database milik service yang berbeda. Foreign key relasional tidak dapat menjaga referensi lintas kedua database tanpa menggabungkan kepemilikan data. Karena itu, Mahasiswa Service menyimpan kode mata kuliah sebagai referensi dan meminta detailnya melalui API.

Jika mata kuliah dihapus, baris KRS dapat tetap menyimpan kode yang sudah tidak ditemukan. Pembacaan KRS tetap dapat menampilkan kodenya, tetapi detail mata kuliah tidak tersedia. Solusi yang dapat dipilih adalah soft delete atau status arsip pada mata kuliah, atau meminta Mata Kuliah Service mengirim event penghapusan agar service mahasiswa membersihkan/menandai referensi terkait. Penghapusan langsung lintas service sebaiknya dihindari.

### 5.2 Apa yang terjadi ketika Mata Kuliah Service mati?

Pengambilan KRS baru gagal divalidasi dan seharusnya mengembalikan `503`. Pembacaan daftar KRS masih dapat mengembalikan kode yang tersimpan, dengan catatan bahwa detailnya tidak tersedia. Pemanggilan REST sinkron menciptakan coupling saat runtime: satu operasi bergantung pada ketersediaan service lain. Jika semua permintaan masuk hanya melalui satu instance gateway, gateway juga dapat menjadi single point of failure. Replikasi gateway dan service serta pemeriksaan kesehatan dapat mengurangi risiko tersebut.

### 5.3 Kelebihan dan kekurangan database terpisah

Database per service membatasi akses langsung, memberi tiap service kebebasan memilih skema dan mengatur kapasitasnya sendiri, serta mengurangi dampak perubahan tabel pada service lain. Kekurangannya meliputi biaya operasi lebih tinggi, pemantauan dan backup yang lebih rumit, serta tidak tersedianya foreign key atau transaksi tunggal lintas service. Memakai satu database bersama lebih sederhana untuk operasional awal dan pelaporan lintas entitas, tetapi memperbesar ketergantungan antarservice dan membuat batas kepemilikan data lebih kabur.

### 5.4 Peran API Gateway dan fungsi tambahan

Gateway menyediakan satu alamat masuk, merutekan path ke service tujuan, dan menyajikan dashboard pada origin yang sama. Fungsi tambahan yang dapat diterapkan antara lain autentikasi, rate limiting, load balancing, pencatatan akses, dan terminasi TLS.

### 5.5 Service mana yang di-scale jika jumlah mahasiswa meningkat?

Scale service berdasarkan metrik beban dan bottleneck. Jika permintaan daftar/detail mahasiswa atau KRS mendominasi, Mahasiswa Service dapat dijalankan dalam beberapa replika karena proses API bersifat stateless dan data berada di MySQL. Nginx dapat membagi permintaan ke beberapa replika. Jika bottleneck berada di database, menambah replika aplikasi saja tidak cukup; kapasitas query, indeks, koneksi, dan opsi read replica MySQL perlu ditinjau. Karena KRS memanggil Mata Kuliah Service secara sinkron, beban validasi KRS juga dapat meningkatkan beban service tersebut.

### 5.6 REST sinkron dibanding komunikasi asinkron

REST sinkron cocok ketika klien membutuhkan hasil langsung, seperti validasi kode mata kuliah sebelum KRS disimpan. Implementasinya mudah dipahami, tetapi pemanggil harus menunggu dan ikut terdampak jika service tujuan lambat atau mati. Message broker seperti RabbitMQ lebih cocok untuk pekerjaan latar belakang, notifikasi, atau proses yang dapat diproses belakangan. Cara asinkron mengurangi ketergantungan waktu nyata, tetapi menambah kompleksitas antrean, retry, duplikasi pesan, dan konsistensi eventual.

## 6. Cara Menjalankan

Dari root repositori:

```powershell
docker compose up --build
```

Dashboard tersedia di `http://localhost:8080`. Untuk menghentikan container tanpa menghapus data:

```powershell
docker compose down
```

## 7. Kesimpulan

Implementasi tiga peran berhasil dijalankan bersama melalui Docker Compose. Bukti yang disediakan memverifikasi seluruh 10 skenario integrasi, termasuk validasi data, komunikasi antarservice, penghapusan KRS saat mahasiswa dihapus, respons saat service dimatikan, dan persistensi volume.
