# Thực hành 5.2 — SAST-tool


## Kết quả thực hành

### 1. Cài đặt thư viện

![Cài đặt requirements](ketqua/Screenshot%202026-10-21%20131456.png)

### 2. Chạy Unit Test — 6 tests OK

![Unit test](ketqua/Screenshot%202026-10-21%20132127.png)

### 3. Phân tích `vulnerable_01.py` — 8 issues

![Phân tích vulnerable_01](ketqua/Screenshot%202026-10-21%20132136.png)

Kết quả trong SARIF Viewer: phát hiện `eval()`, hardcoded password, import `pickle` và 5 lỗi flake8.

![SARIF vulnerable_01](ketqua/Screenshot%202026-10-21%20131823.png)

### 4. Phân tích `vulnerable_02.py` — 4 issues

![Phân tích vulnerable_02](ketqua/Screenshot%202026-10-21%20132143.png)

Kết quả trong SARIF Viewer: phát hiện `eval()` và 3 lỗi flake8.

![SARIF vulnerable_02](ketqua/Screenshot%202026-10-21%20131921.png)


