# Dokumentasi Teknis Layanan: Subscriber Usage & Snapshot Automation

Dokumen ini berisi rangkuman teknis lengkap, desain arsitektur, spesifikasi endpoint, skrip otomasi snapshot, serta instruksi pengujian untuk pengerjaan **Task Q1** dan **Task Q2**.

---

## 📋 Daftar Isi
1. [Ringkasan Solusi](#ringkasan-solusi)
2. [Task Q1: Subscriber Usage Service (FastAPI)](#task-q1-subscriber-usage-service-fastapi)
   - [Desain Arsitektur & In-Memory Store](#desain-arsitektur--in-memory-store)
   - [Fungsi Perhitungan Modular](#fungsi-perhitungan-modular)
   - [Spesifikasi Endpoint & Bentuk Data](#spesifikasi-endpoint--bentuk-data)
   - [Cara Menjalankan Service](#cara-menjalankan-service)
3. [Task Q2: Otomasi Snapshot & Pembersihan (Scripts)](#task-q2-otomasi-snapshot--pembersihan-scripts)
   - [Skrip Snapshot (create_snapshot.py)](#skrip-snapshot-create_snapshotpy)
   - [Skrip Pembersihan (cleanup_snapshots.py)](#skrip-pembersihan-cleanup_snapshotspy)
   - [Konfigurasi Crontab (08:00, 12:00, 15:00 WIB)](#konfigurasi-crontab-0800-1200-1500-wib)

---

## 1. Ringkasan Solusi

| Komponen | Teknologi | Keterangan |
|---|---|---|
| **Framework Backend** | FastAPI + Pydantic v2 | Validasi otomatis, auto OpenAPI / Swagger documentation |
| **Data Store** | In-Memory (`InMemoryUsageStore`) | Thread-safe dictionary dengan struktur `map[subscriberId] -> list[records]` |
| **Automation Scripts** | Python 3 Standard Library | Zero external dependencies (`urllib`, `csv`, `pathlib`, `re`) |
| **Pengujian** | Python `unittest` + `TestClient` | 100% test pass untuk API, fungsi kalkulasi, pembuatan CSV, dan pembersihan file |

---

## 2. Task Q1: Subscriber Usage Service (FastAPI)

### Desain Arsitektur & In-Memory Store
Layanan berada di direktori `usage-record-service/`.
Struktur data penyimpanan in-memory di [store.py] menggunakan `dict[str, list[dict]]`:
```json
{
  "sub-001": [
    {
      "callMinutes": 15,
      "smsCount": 3,
      "dataUsageMB": 250.5,
      "timestamp": "2026-10-16T16:21:08.969771+00:00"
    },
    {
      "callMinutes": 25,
      "smsCount": 7,
      "dataUsageMB": 350.25,
      "timestamp": "2026-10-16T16:21:08.972894+00:00"
    }
  ]
}
```

### Fungsi Perhitungan Modular
Sesuai arahan teknis pada requirement poin 25, setiap metrik dihitung oleh fungsi terpisah di [services.py](file:///d:/project/PMT_test/usage-record-service/app/services.py):
1. `calculate_total_call_minutes(usages: list[dict]) -> int`: Mengakumulasi total menit panggilan.
2. `calculate_total_sms_count(usages: list[dict]) -> int`: Mengakumulasi total SMS terkirim.
3. `calculate_total_data_usage_mb(usages: list[dict]) -> float`: Mengakumulasi total penggunaan data dalam MB (dibulatkan 2 desimal).
4. `calculate_subscriber_summary(usages: list[dict]) -> dict`: Menggabungkan hasil fungsi perhitungan di atas menjadi objek ringkasan tunggal.

### Spesifikasi Endpoint & Bentuk Data

#### A. `POST /usages`
Mencatat penggunaan subscriber.
* **Input Body**:
  ```json
  {
    "subscriberId": "sub-1001",
    "callMinutes": 25,
    "smsCount": 10,
    "dataUsageMB": 512.5
  }
  ```

* **Status Response**: `201 Created`
* **Response Body**:
  ```json
  {
    "message": "Usage recorded successfully",
    "subscriberId": "sub-1001",
    "record": {
      "callMinutes": 25,
      "smsCount": 10,
      "dataUsageMB": 512.5,
      "timestamp": "2026-10-16T16:21:08.969771+00:00"
    }
  }
  ```

#### B. `GET /usages`
Mengambil data riwayat seluruh subscriber.
* **Status Response**: `200 OK`
* **Response Body**:
  ```json
  {
    "sub-1001": [
      {
        "callMinutes": 25,
        "smsCount": 10,
        "dataUsageMB": 512.5,
        "timestamp": "2026-10-16T16:21:08.969771+00:00"
      }
    ]
  }
  ```

#### C. `GET /usages/{subscriberId}`
Mengambil riwayat dan ringkasan penggunaan subscriber tertentu.
* **Status Response**: `200 OK` (atau `404 Not Found` jika ID tidak ditemukan).
* **Response Body**:
  ```json
  {
    "subscriberId": "sub-1001",
    "summary": {
      "totalCallMinutes": 40,
      "totalSmsCount": 20,
      "totalDataUsageMB": 862.75
    },
    "usages": [
      {
        "callMinutes": 15,
        "smsCount": 10,
        "dataUsageMB": 350.25,
        "timestamp": "2026-10-16T16:00:00+00:00"
      },
      {
        "callMinutes": 25,
        "smsCount": 10,
        "dataUsageMB": 512.5,
        "timestamp": "2026-10-16T16:20:00+00:00"
      }
    ]
  }
  ```

### Cara Menjalankan Service
Masuk ke direktori `usage-record-service/`:
```bash
# Menjalankan dev server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger UI otomatis tersedia di: `http://localhost:8000/docs`

---

## 3. Task Q2: Otomasi Snapshot & Pembersihan (Scripts)

Skrip berada di direktori `scripts/`.

### Skrip Snapshot (`create_snapshot.py`)
* Mengambil data dari endpoint `GET /usages`.
* Menyimpan berkas dengan konvensi nama: `usages_snapshot_YYYYMMDD_HHMMSS.csv` di folder `usage-record-service/snapshots/`.
* Kolom CSV: `subscriberId,callMinutes,smsCount,dataUsageMB,timestamp`.
* **Cara Eksekusi**:
  ```bash
  python scripts/create_snapshot.py
  ```

### Skrip Pembersihan (`cleanup_snapshots.py`)
* Mengekstrak timestamp dari akhiran nama file CSV (`usages_snapshot_<YYYYMMDD_HHMMSS>.csv`).
* Menghitung selisih waktu berkas dengan waktu sekarang.
* Jika usia berkas > 30 hari (`waktu_berkas < waktu_sekarang - 30 hari`), berkas akan dihapus.
* **Cara Eksekusi**:
  ```bash
  # Eksekusi langsung
  python scripts/cleanup_snapshots.py

  # Mode simulasi (Dry Run) tanpa menghapus berkas
  python scripts/cleanup_snapshots.py --dry-run
  ```

### Konfigurasi Crontab (08:00, 12:00, 15:00 WIB)
Berkas konfigurasi siap pakai tersedia di [crontab.txt](file:///d:/project/PMT_test/scripts/crontab.txt).

```cron
# Menjalankan snapshot 3x sehari pada 08:00, 12:00, 15:00 WIB (Server Time: WIB / Asia/Jakarta)
0 8,12,15 * * * /usr/bin/python3 /path/to/PMT_test/scripts/create_snapshot.py >> /path/to/PMT_test/scripts/cron_snapshot.log 2>&1

# Menjalankan pembersihan berkas > 30 hari setiap hari pukul 00:00 WIB
0 0 * * * /usr/bin/python3 /path/to/PMT_test/scripts/cleanup_snapshots.py >> /path/to/PMT_test/scripts/cron_cleanup.log 2>&1
```

*(Jika server berbasis UTC, jadwal snapshot dikonversi menjadi `0 1,5,8 * * *`)*

---