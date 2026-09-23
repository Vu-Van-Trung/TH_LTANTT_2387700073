# Lab 2 – Phân tích điểm yếu của pre-commit hook GitSecure

## Ảnh minh chứng

![Khai thác mục 1 và mục 2 — stage-vs-disk và tên file tiếng Việt](Screenshot%202026-09-23%20201744.png)

| Lệnh (payload) trong ảnh | Điểm yếu khai thác | Kết quả |
|---|---|---|
| `echo 'password = "Secret1"' > a.py; git add a.py; echo 'x=1' > a.py; git commit -m c1` | [Mục 1](#1-quét-file-trên-đĩa-thay-vì-nội-dung-đã-stage) — stage một đằng (`password = "Secret1"`), đĩa một nẻo (`x=1`); kèm [mục 9](#9-né-hook-bằng-file-mã-hoá-utf-16) do PowerShell ghi UTF-16 | `All checks passed` → commit `4ac85b9` |
| `echo 'password = "Secret1"' > "mật khẩu.py"; git add .; git commit -m c2` | [Mục 2](#2-bỏ-qua-file-có-tên-tiếng-việt-hoặc-ký-tự-đặc-biệt) — `core.quotePath` escape tên file thành `"m\341\272\255t kh\341\272\251u.py"` nên `os.path.isfile()` sai, file không được quét | `All checks passed` → commit `f245403` |

![Khai thác mục 9 — file UTF-16 sinh từ PowerShell](Screenshot%202026-09-23%20201755.png)

| Lệnh (payload) trong ảnh | Điểm yếu khai thác | Kết quả |
|---|---|---|
| `echo 'password = "123456"' > a.py; git add a.py; git commit -m c` | [Mục 9](#9-né-hook-bằng-file-mã-hoá-utf-16) — PowerShell `echo` ghi UTF-16LE, mỗi ký tự xen byte `\0` nên regex `password\s*=...` không khớp | `All checks passed` → commit `7fe11e5` |

Có thể kiểm chứng bí mật đã lọt vào lịch sử bằng: `git show 4ac85b9:./a.py`, `git show "f245403:./mật khẩu.py"`, `git show 7fe11e5:./a.py`.

---

## Chuẩn bị môi trường thử nghiệm

Nên thử trong một repo riêng để không làm bẩn repo chính. **Chạy các lệnh trong Git Bash**, không chạy trong PowerShell: `echo ... >` của PowerShell 5.1 ghi file dạng UTF-16 (xem [mục 9](#9-né-hook-bằng-file-mã-hoá-utf-16)).

## 1. Quét file trên đĩa thay vì nội dung đã stage

**Vị trí:** [pre-commit:19-28](.githooks/pre-commit#L19-L28)

```python
def scan_sensitive(file_path):
    try:
        with open(file_path, "r", errors="ignore") as f:   # dòng 21
            content = f.read()
```

**Nguyên nhân:** `open(file_path)` đọc file trong thư mục làm việc (working tree). Nhưng thứ thực sự được commit là nội dung trong index (vùng stage). Hai bản này có thể khác nhau.

**Khai thác:**

```bash
echo 'password = "SuperSecret1"' > a.py
git add a.py                 # index chứa mật khẩu
echo 'x = 1' > a.py          # file trên đĩa sạch
git commit -m "c1"           # GitSecure: All checks passed.
git show HEAD:./a.py         # password = "SuperSecret1"  -> đã lọt vào lịch sử
```


## 2. Bỏ qua file có tên tiếng Việt hoặc ký tự đặc biệt

**Vị trí:** [pre-commit:50-52](.githooks/pre-commit#L50-L52)

```python
files = subprocess.check_output(["git", "diff", "--cached", "--name-only"]).decode().splitlines()
for file in files:
    if not os.path.isfile(file): continue
```

**Nguyên nhân:** khi `core.quotePath` bật (mặc định), `git diff --name-only` bao tên file có ký tự ngoài ASCII trong dấu ngoặc kép và escape từng byte, ví dụ `mật khẩu.py` thành `"m\341\272\255t kh\341\272\251u.py"`. Chuỗi này không phải đường dẫn hợp lệ, nên `os.path.isfile()` trả về `False` và vòng lặp `continue`. File không hề được quét.

**Khai thác:**

```bash
echo 'password = "SuperSecret1"' > "mật khẩu.py"
git add .
git commit -m "c2"               # GitSecure: All checks passed.
git show "HEAD:./mật khẩu.py"    # password = "SuperSecret1"
```

## 3. Né hook bằng file mã hoá UTF-16

**Vị trí:** [pre-commit:21-24](.githooks/pre-commit#L21-L24)

```python
with open(file_path, "r", errors="ignore") as f:
    content = f.read()
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
```

**Nguyên nhân:** hook mở file bằng encoding mặc định của hệ thống (cp1252 trên Windows, UTF-8 trên Linux) kèm `errors="ignore"`. Một file UTF-16 chứa byte `\0` xen giữa mỗi ký tự, nên khi đọc ra chuỗi sẽ thành `p\0a\0s\0s\0w\0o\0r\0d...`. Regex `password\s*=...` vì thế không khớp. Trong khi đó Python vẫn chạy bình thường file UTF-16 có BOM, và các chương trình khác cũng đọc được bí mật trong đó. Git coi file UTF-16 là file nhị phân, nên `git diff` không hiển thị nội dung, bí mật càng khó bị phát hiện khi review.

**Khai thác:** trong PowerShell 5.1, `echo` mặc định ghi file UTF-16LE:

```powershell
echo 'password = "SuperSecret1"' > a.py
git add a.py
git commit -m "c1"          # GitSecure: All checks passed.
git show HEAD --stat        # a.py | Bin 0 -> 56 bytes
```

Đã kiểm chứng: `scan_sensitive()` trả về `None` với file này. Nhưng khi đọc bằng `encoding="utf-16"` thì vẫn lấy được `password = SuperSecret1`.
