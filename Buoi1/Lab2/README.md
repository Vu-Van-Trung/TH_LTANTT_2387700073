# Lab 2 – Phân tích điểm yếu của pre-commit hook GitSecure

Tài liệu này ghi lại các điểm yếu bảo mật trong hook [`.githooks/pre-commit`](.githooks/pre-commit), cách khai thác từng điểm yếu và vị trí đoạn code gây ra lỗi. Mỗi kỹ thuật khai thác đều đã được chạy thử trên một repo thử nghiệm riêng: hook báo `GitSecure: All checks passed.` trong khi nội dung nguy hiểm vẫn được commit.

## Ảnh minh chứng

Các ảnh dưới đây chụp lại quá trình khai thác thực tế trong PowerShell: hook luôn in `GitSecure: All checks passed.` trong khi commit vẫn chứa mật khẩu. Ba commit tương ứng chính là `4ac85b9 c1`, `f245403 c2`, `7fe11e5 c` trong lịch sử repo.

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

Lưu ý: cú pháp `git show HEAD:<đường dẫn>` tính đường dẫn từ **gốc repo**. Nếu đang đứng trong thư mục con (ví dụ `Buoi1/Lab2`), phải thêm `./` phía trước: `git show HEAD:./a.py`.

```bash
mkdir poc && cd poc
git init
git config user.name test && git config user.email test@test
mkdir .githooks
cp ../Buoi1/Lab2/.githooks/pre-commit .githooks/
git config core.hooksPath .githooks
```

## Tổng hợp

| # | Điểm yếu | Vị trí | Mức độ |
|---|---|---|---|
| 1 | Quét file trên đĩa thay vì nội dung đã stage | [pre-commit:21](.githooks/pre-commit#L21) | Cao |
| 2 | Bỏ qua file có tên tiếng Việt hoặc ký tự đặc biệt | [pre-commit:50-52](.githooks/pre-commit#L50-L52) | Cao |
| 3 | Kiểm tra bandit không bao giờ kích hoạt | [pre-commit:41](.githooks/pre-commit#L41) | Cao |
| 4 | Thực thi code tuỳ ý qua module `bandit` giả | [pre-commit:40](.githooks/pre-commit#L40) | Cao |
| 5 | Fail-open: lỗi xảy ra thì cho qua | [pre-commit:26-27](.githooks/pre-commit#L26-L27), [pre-commit:40-46](.githooks/pre-commit#L40-L46) | Trung bình |
| 6 | Regex phát hiện bí mật quá hẹp | [pre-commit:7-13](.githooks/pre-commit#L7-L13) | Trung bình |
| 7 | Bỏ qua hook bằng `--no-verify` / hook không đi theo repo | Cấu hình `core.hooksPath` | Trung bình |
| 8 | Tắt kiểm tra quyền file trên Windows | [pre-commit:31-32](.githooks/pre-commit#L31-L32) | Thấp |
| 9 | Né hook bằng file mã hoá UTF-16 | [pre-commit:21-24](.githooks/pre-commit#L21-L24) | Cao |

---

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

**Khắc phục:** đọc nội dung đã stage thay vì file trên đĩa:

```python
content = subprocess.check_output(["git", "show", f":{file_path}"]).decode(errors="ignore")
```

---

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

**Khắc phục:** dùng `-z` để git trả về tên file nguyên bản, phân tách bằng ký tự NUL:

```python
out = subprocess.check_output(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"])
files = [f for f in out.decode().split("\0") if f]
```

---

## 3. Kiểm tra bandit không bao giờ kích hoạt

**Vị trí:** [pre-commit:41](.githooks/pre-commit#L41)

```python
if "SEVERITY: High" in result.stdout:
```

**Nguyên nhân:** bandit (từ bản 1.7 trở đi, đang dùng 1.9.4) in ra `Severity: High`, còn phép `in` phân biệt hoa thường. Vì vậy điều kiện luôn sai, và lỗi mức High không bao giờ chặn được commit.

**Khai thác:**

```bash
printf 'import subprocess\nsubprocess.call("ls " + input(), shell=True)\n' > b.py
git add b.py
git commit -m "c4"            # GitSecure: All checks passed.
python -m bandit -q b.py      # Severity: High   Confidence: High  (B602 shell=True)
```

**Khắc phục:** dựa vào mã thoát (exit code) thay vì tìm chuỗi. Bandit trả mã khác 0 khi có lỗi ở mức được lọc:

```python
result = subprocess.run([sys.executable, "-I", "-m", "bandit", "-q", "-lll", *py_files],
                        capture_output=True, text=True)
if result.returncode != 0:
    return "Bandit: High severity issues found."
```

---

## 4. Thực thi code tuỳ ý qua module `bandit` giả

**Vị trí:** [pre-commit:40](.githooks/pre-commit#L40)

```python
result = subprocess.run([sys.executable, "-m", "bandit", "-r", "."], ...)
```

**Nguyên nhân:** khi chạy `python -m <module>`, Python đưa thư mục hiện tại lên đầu `sys.path`, và hook luôn chạy từ gốc repo. Nếu trong repo (ví dụ một nhánh hay một pull request của người khác) có package tên `bandit`, Python sẽ import package đó thay vì bandit thật. Code của kẻ tấn công vì thế chạy trên máy của bất kỳ ai commit.

**Khai thác:**

```bash
mkdir bandit
touch bandit/__init__.py
echo 'open("PWNED.txt","w").write("code chay trong hook")' > bandit/__main__.py
echo 'y = 3' > d.py && git add d.py
git commit -m "c6"            # GitSecure: All checks passed.
cat PWNED.txt                 # code chay trong hook
```

Nếu thiếu `__init__.py`, thư mục chỉ được coi là namespace package và thua bandit thật nằm trong `site-packages`, nên phải có file này thì khai thác mới thành công. Với bản gốc gọi `["bandit", ...]`, trên Windows `CreateProcess` cũng tìm `bandit.exe` trong thư mục hiện tại trước PATH, nên rủi ro tương tự vẫn tồn tại.

**Khắc phục:** chạy Python ở chế độ isolated (`-I`) để bỏ thư mục hiện tại khỏi `sys.path`:

```python
subprocess.run([sys.executable, "-I", "-m", "bandit", ...])
```

---

## 5. Fail-open: lỗi xảy ra thì cho qua

**Vị trí:**
- [pre-commit:26-27](.githooks/pre-commit#L26-L27): mọi exception khi quét đều trả về `None`, tức là coi như file sạch.
- [pre-commit:40-46](.githooks/pre-commit#L40-L46): khi gọi qua `python -m bandit` mà bandit chưa cài, Python không ném `FileNotFoundError`. Tiến trình chỉ in `No module named bandit` ra stderr rồi thoát với mã 1. Code không kiểm tra `returncode` hay `stderr`, nên hook vẫn trả về `None` và cho qua.

```python
except Exception:
    return None
```

**Khai thác:**

```bash
pip uninstall -y bandit
git commit -m "..."     # GitSecure: All checks passed.  (không hề có bước kiểm tra bandit)
```

**Khắc phục:** fail-closed. Hễ không quét được thì trả về một finding để chặn commit, và kiểm tra `result.returncode` cùng `result.stderr` của bandit.

---

## 6. Regex phát hiện bí mật quá hẹp

**Vị trí:** [pre-commit:7-13](.githooks/pre-commit#L7-L13)

```python
SENSITIVE_PATTERNS = [
    r"apikey\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
    r"secret\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]",
    r"password\s*=\s*['\"][^'\"]{4,}['\"]",
    r"token\s*=\s*['\"][A-Za-z0-9]{10,}['\"]",
    r"(AKIA|ASIA)[A-Z0-9]{16}"
]
```

**Nguyên nhân:**
- Các mẫu chỉ khớp dạng `key = "value"`, bỏ sót JSON và YAML (`"password": "..."`).
- `apikey` không khớp `api_key` hay `api-key`.
- Mẫu `token` không cho phép `_` và `-`, nên bỏ sót phần lớn token thực tế.
- Không có mẫu cho private key, GitHub token (`ghp_...`), JWT, hay mật khẩu trong connection string.
- Mỗi file chỉ báo mẫu khớp đầu tiên.

**Khai thác:** file sau được commit mà không bị chặn:

```bash
cat > c.json <<'EOF'
{"password": "SuperSecret1"}
api_key = "abcdefghijklmnop1234"
-----BEGIN RSA PRIVATE KEY-----
ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
postgres://admin:SuperSecret1@db:5432/x
EOF
git add c.json
git commit -m "c3"            # GitSecure: All checks passed.
```

**Khắc phục:** mở rộng regex, ví dụ:

```python
r"(api[_-]?key|secret|passw(or)?d|pwd|token)\s*[:=]\s*['\"][^'\"]{4,}['\"]",
r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
r"gh[pousr]_[A-Za-z0-9]{36}",
r"[a-z]+://[^:\s/]+:[^@\s]+@",
```

Tốt hơn nữa là dùng công cụ chuyên dụng như [gitleaks](https://github.com/gitleaks/gitleaks) hoặc [detect-secrets](https://github.com/Yelp/detect-secrets).

---

## 7. Bỏ qua hook bằng `--no-verify` / hook không đi theo repo

**Vị trí:** cơ chế cài hook: `git config core.hooksPath Buoi1/Lab2/.githooks`

**Nguyên nhân:** pre-commit hook chạy ở phía client, nên người dùng hoàn toàn kiểm soát được. `core.hooksPath` lại là cấu hình local, không được lưu trong repo, nên người clone repo về sẽ không có hook.

**Khai thác:**

```bash
echo 'password = "SuperSecret1"' > e.py
git add e.py
git commit --no-verify -m "c7"   # hook không chạy
```

**Khắc phục:** coi hook ở client chỉ là lớp bảo vệ đầu tiên. Cần kiểm tra thêm ở phía server: bật GitHub Secret Scanning / Push Protection, hoặc chạy gitleaks và bandit trong CI (GitHub Actions) để chặn merge.

---

## 8. Tắt kiểm tra quyền file trên Windows

**Vị trí:** [pre-commit:30-36](.githooks/pre-commit#L30-L36)

```python
if platform.system() == "Windows":
    return None
```

**Nguyên nhân:** trên Windows, `os.stat()` luôn trả về mode `0o666` cho file ghi được, nên hook báo nhầm mọi file là world-writable. Để hết báo nhầm, bản sửa tắt hẳn kiểm tra này. Hệ quả là trên Windows chức năng kiểm tra quyền không còn tác dụng gì. Đây là đánh đổi chấp nhận được vì Windows dùng ACL chứ không dùng bit quyền kiểu Unix. Tuy vậy vẫn nên kiểm tra mode mà git sẽ lưu, ví dụ qua `git ls-files -s`.

---

## 9. Né hook bằng file mã hoá UTF-16

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

**Khắc phục:** phát hiện BOM hoặc byte `\0` rồi giải mã lại bằng UTF-16 trước khi quét. Nếu không giải mã được thì chặn commit (fail-closed):

```python
raw = subprocess.check_output(["git", "show", f":{file_path}"])
if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\0" in raw[:1024]:
    try:
        content = raw.decode("utf-16")
    except UnicodeDecodeError:
        return f"Cannot decode {file_path} - blocked"
else:
    content = raw.decode("utf-8", errors="replace")
```

---

## Các điểm yếu khác

- **Bandit quét toàn bộ repo (`-r .`)** ([pre-commit:40](.githooks/pre-commit#L40)): chậm, file không liên quan có thể chặn commit, và quét cả `.venv`. Chỉ nên quét các file `.py` đã stage.
- **Đọc cả file vào bộ nhớ** ([pre-commit:22](.githooks/pre-commit#L22)): file lớn hoặc file nhị phân làm hook chậm. Nên giới hạn kích thước hoặc bỏ qua file nhị phân.
- **Không xử lý bí mật đã nằm trong lịch sử:** nếu một bí mật đã lọt vào commit trước đó, xoá file đi không đủ. Phải thu hồi hoặc đổi bí mật đó, rồi viết lại lịch sử bằng `git filter-repo`.
- **[bad.py](pre-commit-hook-test/bad.py#L3):** `os.environ.get("APP_PASSWORD")` trả về `None` khi thiếu biến môi trường mà không báo lỗi. Nên kiểm tra và dừng chương trình với thông báo rõ ràng.

## Lưu ý khi commit file README này

README chứa các ví dụ mật khẩu dạng chuỗi như ở mục 1, nên chính hook GitSecure sẽ chặn commit file này (một trường hợp báo động giả). Có thể commit bằng `git commit --no-verify`, hoặc thêm cơ chế allowlist vào hook (ví dụ bỏ qua các file `*.md`).
