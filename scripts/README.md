# Usage Snapshot Automation & Cleanup Scripts (Q2)

Kumpulan skrip otomasi Python untuk mengekspor data penggunaan subscriber ke file CSV secara terjadwal serta membersihkan arsip snapshot yang telah berusia lebih dari 30 hari.

---

##  Berkas dalam Direktori Ini
1. `create_snapshot.py`: Mengambil data dari endpoint `GET /usages` dan menyimpannya sebagai file CSV.
2. `cleanup_snapshots.py`: Memeriksa folder snapshot dan menghapus berkas CSV yang usianya lebih dari 30 hari berdasarkan timestamp pada nama file.
3. `crontab.txt`: Konfigurasi jadwal cron untuk eksekusi 3x sehari (08:00, 12:00, 15:00 WIB) dan pembersihan harian.

---

##  Skrip 1: `create_snapshot.py`

### Deskripsi & Konvensi
* **Format Nama Berkas**: `usages_snapshot_YYYYMMDD_HHMMSS.csv` (Contoh: `usages_snapshot_20261016_232121.csv`)
* **Format Baris CSV**:
  ```csv
  subscriberId,callMinutes,smsCount,dataUsageMB,timestamp
  sub-001,15,3,250.5,2026-10-16T16:21:08.969771+00:00
  sub-001,25,7,350.25,2026-10-16T16:21:08.972894+00:00
  sub-002,60,20,1024.0,2026-10-16T16:21:08.975653+00:00
  ```
* **Dependensi**: Menggunakan Python Standard Library (`urllib`, `csv`, `datetime`, dll), sehingga tidak memerlukan instalasi library tambahan.

### Cara Menjalankan
```bash
# Menjalankan secara langsung dengan opsi default (API di http://localhost:8000/usages):
python create_snapshot.py

# Atau tentukan API URL dan direktori output kustom:
python create_snapshot.py --api-url http://localhost:8000/usages --output-dir ../usage-record-service/snapshots
```

---

##  Skrip 2: `cleanup_snapshots.py`

### Deskripsi & Logika Pembersihan
* Skrip memindai berkas dengan pola `usages_snapshot_YYYYMMDD_HHMMSS.csv`.
* Suffix timestamp diekstrak dan diparsing menjadi objek `datetime`.
* Waktu berkas dibandingkan dengan ambang batas `waktu_sekarang - 30 hari`.
* Jika timestamp berkas lebih lama dari 30 hari, berkas akan dihapus. Berkas lain yang tidak cocok dengan format nama tidak akan disentuh.

### Cara Menjalankan
```bash
# Menjalankan pembersihan berkas > 30 hari:
python cleanup_snapshots.py

# Mode simulasi / pratinjau (Dry-Run) tanpa menghapus file:
python cleanup_snapshots.py --dry-run

# Mengubah ambang batas hari (misal 14 hari):
python cleanup_snapshots.py --days 14
```

---

##  Konfigurasi Crontab (08:00, 12:00, 15:00 WIB)

Untuk menjalankan skrip ini secara otomatis pada server Linux, buka editor crontab:
```bash
crontab -e
```

Tambahkan baris berikut (sesuaikan path absolut ke python dan berkas script):

```cron
# Eksekusi snapshot 3 kali sehari pada pukul 08:00, 12:00, dan 15:00 WIB
0 8,12,15 * * * /usr/bin/python3 /path/to/PMT_test/scripts/create_snapshot.py >> /path/to/PMT_test/scripts/cron_snapshot.log 2>&1

# Pembersihan otomatis snapshot > 30 hari setiap hari pukul 00:00 WIB
0 0 * * * /usr/bin/python3 /path/to/PMT_test/scripts/cleanup_snapshots.py >> /path/to/PMT_test/scripts/cron_cleanup.log 2>&1
```

> **Catatan Penyesuaian Zona Waktu (Jika Server Berjalan di UTC):**
> Waktu Indonesia Barat (WIB) adalah **UTC+7**. Jika server Linux menggunakan UTC:
> - `08:00 WIB` = `01:00 UTC`
> - `12:00 WIB` = `05:00 UTC`
> - `15:00 WIB` = `08:00 UTC`
> 
> Maka sintaks cron di server UTC adalah:
> `0 1,5,8 * * * /usr/bin/python3 /path/to/PMT_test/scripts/create_snapshot.py >> /path/to/PMT_test/scripts/cron_snapshot.log 2>&1`
