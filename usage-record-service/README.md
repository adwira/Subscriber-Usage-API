# Subscriber Usage Record Service (Q1)

Service backend berbasis **FastAPI** dengan penyimpanan **in-memory** untuk mencatat riwayat penggunaan subscriber (panggilan, SMS, data) dan menyajikan ringkasan akumulasi metrik penggunaan.

---

## Fitur Utama
1. **Pencatatan Penggunaan (POST /usages)**: Menyimpan penggunaan user dengan validasi input Pydantic dan timestamp otomatis.
2. **Riwayat Semua Pengguna (GET /usages)**: Mengambil seluruh riwayat penggunaan semua subscriber yang tersimpan.
3. **Detail & Ringkasan Per Pengguna (GET /usages/{subscriberId})**: Menampilkan detail log penggunaan serta kalkulasi akumulasi total durasi telepon, jumlah SMS, dan kuota data dalam MB.
4. **Fungsi Perhitungan Modular**: Masing-masing metrik dihitung oleh fungsi independen tersendiri (`calculate_total_call_minutes`, `calculate_total_sms_count`, `calculate_total_data_usage_mb`).
5. **In-Memory Store**: Struktur data berbasis map `dict[str, list[dict]]` yang sederhana dan efisien.

---

## Struktur Direktori
```text
usage-record-service/
├── app/
│   ├── __init__.py
│   ├── main.py          # Routing FastAPI, Middleware, & Exception Handling
│   ├── models.py        # Pydantic schemas (validasi request & serialization)
│   ├── store.py         # In-memory storage class
│   └── services.py      # Fungsi kalkulasi terpisah untuk call, sms, & data
├── snapshots/           # Direktori tempat file CSV snapshot disimpan
└── pyproject.toml       # Dependensi proyek
```

---

## Cara Menjalankan Service

### 1. Menjalankan Server FastAPI
Pastikan Anda berada di direktori `usage-record-service`:
```bash
# Menggunakan uv (recommended)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Atau menggunakan python virtual environment standar
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Server akan aktif di: `http://localhost:8000`

### 2. Akses Dokumentasi Interaktif (Swagger UI)
Buka browser dan akses:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Spesifikasi API & Desain Endpoint

### 1. `POST /usages`
Mencatat penggunaan subscriber ke dalam in-memory store.

* **Method**: `POST`
* **Path**: `/usages`
* **Request Header**: `Content-Type: application/json`
* **Request Body**:
  ```json
  {
    "subscriberId": "sub-1001",
    "callMinutes": 25,
    "smsCount": 10,
    "dataUsageMB": 512.5
  }
  ```

* **Response Success (`201 Created`)**:
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

* **Response Validation Error (`422 Unprocessable Entity`)**:
  Dihasilkan jika nilai `callMinutes`, `smsCount`, atau `dataUsageMB` bernilai negatif atau tipe data tidak valid.

---

### 2. `GET /usages`
Mengambil seluruh data riwayat penggunaan untuk semua subscriber.

* **Method**: `GET`
* **Path**: `/usages`
* **Response Success (`200 OK`)**:
  ```json
  {
    "sub-1001": [
      {
        "callMinutes": 25,
        "smsCount": 10,
        "dataUsageMB": 512.5,
        "timestamp": "2026-10-16T16:21:08.969771+00:00"
      }
    ],
    "sub-1002": [
      {
        "callMinutes": 60,
        "smsCount": 20,
        "dataUsageMB": 1024.0,
        "timestamp": "2026-10-16T16:21:08.975653+00:00"
      }
    ]
  }
  ```

---

### 3. `GET /usages/{subscriberId}`
Mengambil riwayat penggunaan subscriber tertentu beserta kalkulasi ringkasan (`summary`).

* **Method**: `GET`
* **Path**: `/usages/{subscriberId}`
* **Response Success (`200 OK`)**:
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

* **Response Not Found (`404 Not Found`)**:
  ```json
  {
    "detail": "Subscriber 'unknown-id' not found."
  }
  ```

---

## Fungsi Perhitungan Modular (Summary)
Sesuai instruksi teknis, kalkulasi metrik dipisahkan ke dalam modul `app/services.py`:
- `calculate_total_call_minutes(usages: list[dict]) -> int`
- `calculate_total_sms_count(usages: list[dict]) -> int`
- `calculate_total_data_usage_mb(usages: list[dict]) -> float`
- `calculate_subscriber_summary(usages: list[dict]) -> dict` (Agregator)
