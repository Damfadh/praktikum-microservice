# Indeks Bukti Screenshot Praktikum

Screenshot disalin dari gambar yang diberikan untuk mendokumentasikan progres praktikum.

| File | Keterangan |
|---|---|
| [01-wsl-ubuntu-setup.png](01-wsl-ubuntu-setup.png) | WSL dan Ubuntu selesai dipasang. |
| [02-compose-created-containers.png](02-compose-created-containers.png) | Compose membuat network, volume, dan container; database mulai inisialisasi. |
| [03-compose-build-images.png](03-compose-build-images.png) | Image gateway dan kedua service berhasil dibangun. |
| [04-docker-desktop-running.png](04-docker-desktop-running.png) | Docker Desktop memperlihatkan grup container praktikum aktif. |
| [05-dashboard-courses-and-krs.png](05-dashboard-courses-and-krs.png) | Dashboard menampilkan data awal mata kuliah dan bagian form KRS. |
| [06-dashboard-home.png](06-dashboard-home.png) | Dashboard berhasil dibuka; tabel mahasiswa masih kosong saat screenshot diambil. |
| [07-service-logs-http-200.png](07-service-logs-http-200.png) | Log menunjukkan GET `/mahasiswa` dan GET `/matkul` berstatus 200; permintaan favicon berstatus 404. |
| [08-compose-configuration.png](08-compose-configuration.png) | Tampilan konfigurasi Docker Compose dan volume database. |
| [matkul-service-startup.txt](matkul-service-startup.txt) | Log startup yang menunjukkan traceback rollback di luar application context, lalu service aktif dan `GET /matkul` mengembalikan 200. |
| [test-post-mahasiswa-cmd.txt](test-post-mahasiswa-cmd.txt) | Percobaan POST awal dari CMD mendapat 400 karena kutip tunggal; percobaan ulang mendapat 201 dan berhasil membuat mahasiswa. |
| [09-scenario-1-create-mahasiswa.png](09-scenario-1-create-mahasiswa.png) | Percobaan POST awal mendapat 400; percobaan ulang membuat Budi dengan status 201. |
| [10-scenario-2-duplicate-nim.png](10-scenario-2-duplicate-nim.png) | NIM duplikat ditolak dengan status 409. |
| [11-scenarios-3-to-5-course-and-krs.png](11-scenarios-3-to-5-course-and-krs.png) | Mata kuliah IF399 berhasil dibuat (201), KRS IF301 berhasil dibuat (201), kode XX999 ditolak (404). |
| [12-scenarios-4-to-6-krs-results.png](12-scenarios-4-to-6-krs-results.png) | KRS IF301 berhasil dibuat; kode tidak ada mendapat 404; pengambilan duplikat mendapat 409. |
| [13-scenarios-6-to-7-krs-list.png](13-scenarios-6-to-7-krs-list.png) | KRS duplikat mendapat 409 dan daftar KRS menampilkan detail IF301 dengan status 200. |
| [14-scenario-8-delete-mahasiswa.png](14-scenario-8-delete-mahasiswa.png) | Daftar KRS berhasil dibaca (200), kemudian mahasiswa dihapus (204). |
| [15-scenario-9-service-unavailable.png](15-scenario-9-service-unavailable.png) | Ketika Matkul Service dihentikan, permintaan KRS mendapat 503; service lalu dinyalakan kembali. |
| [16-scenario-10-persistence-restart.png](16-scenario-10-persistence-restart.png) | Data mahasiswa/mata kuliah disiapkan lalu container dihentikan dan dinyalakan tanpa menghapus volume. |
| [17-scenario-10-persistence-verified.png](17-scenario-10-persistence-verified.png) | Setelah startup ulang, GET mahasiswa 2210003 dan mata kuliah IF398 sama-sama mendapat 200. |
| [18-scenario-8-krs-row-removed.png](18-scenario-8-krs-row-removed.png) | Query MySQL untuk NIM 2210001 tidak mengembalikan baris KRS setelah mahasiswa dihapus. |

Screenshot dan log di atas membuktikan setup, build/startup, dashboard, CRUD/KRS, respons saat service tidak tersedia, dan persistensi data setelah restart.
