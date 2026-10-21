# Thực hành 5.4 — DAST-tool


## Kết quả thực hành

### 1. Cài đặt thư viện

![Cài đặt requirements](ketqua/Screenshot%202026-10-21%20132632.png)

### 2. Chạy Unit Test — 5 tests OK

![Unit test](ketqua/Screenshot%202026-10-21%20132640.png)

### 3. Chạy `main.py`

Memory Leaks rỗng, Overflow Test `True`, phát hiện `['os.system', 'eval', 'exec']`, sandbox in ra `Hello Sandbox`.

![main.py](ketqua/Screenshot%202026-10-21%20132651.png)

### 4. Chạy Flask API

![Flask server](ketqua/Screenshot%202026-10-21%20132658.png)

### 5. Kiểm tra các API

Gọi `/api/monitor`, `/api/memory`, `/api/network` bằng PowerShell:

![API monitor, memory, network](ketqua/Screenshot%202026-10-21%20132855.png)

Gọi `/api/security` bằng PowerShell:

![API security](ketqua/Screenshot%202026-10-21%20132858.png)

Gọi `/api/security` và `/api/network` trên trình duyệt:

![API security - trình duyệt](ketqua/Screenshot%202026-10-21%20132904.png)

![API network - trình duyệt](ketqua/Screenshot%202026-10-21%20132915.png)

Log của server: tất cả request đến API, kể cả `POST /api/sandbox`, đều trả về 200:

![Log server](ketqua/Screenshot%202026-10-21%20132926.png)
