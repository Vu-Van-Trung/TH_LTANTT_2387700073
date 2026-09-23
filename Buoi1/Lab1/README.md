# Lab1 — Phân tích điểm yếu của SecureValidator

Phân tích các hàm kiểm tra/lọc đầu vào trong [securevalidator/core.py](securevalidator/core.py),
chỉ ra vị trí đoạn code bị lỗi, bản chất lỗi, kỹ thuật dùng để vượt qua bộ lọc và payload minh chứng.

## Ảnh minh chứng

Giao diện web nhập đồng thời 5 payload — tất cả đều **lọt qua bộ lọc** (báo hợp lệ / mã hóa xong):

![Minh chứng các payload vượt qua bộ lọc](Screenshot%202026-09-23%20195810.png)

| Trường | Payload trong ảnh | Kết quả hiển thị |
|---|---|---|
| Email | `trung..cmd@cmd.dkm` | Email hợp lệ |
| URL | `http://0x7f000001` | URL hợp lệ |
| Filename | `file.txt.` | Tên file hợp lệ |
| SQL Input | `1 HAVING 1=1` | Đã lọc: `1 HAVING 1=1` (không bị lọc) |
| HTML Input | `javascript:alert(1)` | Đã mã hóa: `javascript:alert(1)` (không đổi) |

---

## 1. `sanitize_sql_input` — điểm yếu nghiêm trọng nhất

**Vị trí:** [core.py dòng 22–27](securevalidator/core.py#L22-L27)

```python
def sanitize_sql_input(input_str: str) -> str:
    sanitized = re.sub(r"(--|;|'|\"|#)", "", input_str)
    sanitized = re.sub(r"\b(OR|AND|SELECT|INSERT|DELETE|UPDATE|DROP|UNION|WHERE)\b",
                       "", sanitized, flags=re.IGNORECASE)
    return sanitized.strip()
```

**Lỗi:** Dùng danh sách cấm (blacklist) và **thay thế một lần, không đệ quy**; danh sách từ khóa lại thiếu, đồng thời dùng `\b` (ranh giới từ) khiến từ khóa dính liền chữ khác không bị bắt.

**Kỹ thuật vượt qua** (đã kiểm chứng bằng chính hàm — cột kết quả là output thật):

| # | Kỹ thuật | Payload | Kết quả sau lọc |
|---|---|---|---|
| 1 | **Từ khóa ngoài blacklist** (dùng trong ảnh) | `1 HAVING 1=1` | `1 HAVING 1=1` — giữ nguyên |
| 2 | **Từ khóa dính liền chữ khác** — `\b` không khớp nên không xóa | `SELSELECTECT` | `SELSELECTECT` — `SELECT` vẫn còn |
| 3 | Tương tự với OR (không có ranh giới từ) | `1 OORr 1=1` | `1 OORr 1=1` — giữ nguyên |
| 4 | Từ khóa time-based ngoài danh sách | `1 EXEC SLEEP 5 HAVING` | giữ `EXEC`, `SLEEP`, `HAVING` |
| 5 | **Comment inline** không bị chặn | `1/*bypass*/=1` | `1/*bypass*/=1` — còn `/* */` |
| 6 | **Toán tử `\|\|`** không bị chặn | `1 \|\| 1=1` | `1 \|\| 1=1` — giữ nguyên |

> Kỹ thuật ở dòng 2–3: regex ở dòng 25 dùng `\bSELECT\b`, nên khi `SELECT` bị bao
> bởi các chữ cái khác (`SEL` + `ECT`) thì hai ranh giới từ không tồn tại và từ khóa
> **không hề bị xóa** — payload đi qua nguyên vẹn. Ngay cả khi bỏ `\b`, việc thay
> thế một lượt cũng không quét lại chuỗi mới sinh, nên bộ lọc "tìm-và-xóa một lần"
> luôn có thể bị vượt qua.

**Từ khóa nguy hiểm bị bỏ sót:** `EXEC`, `HAVING`, `LIKE`, `SLEEP`, `BENCHMARK`, `INTO`, `LIMIT`, `ORDER`, `CAST`, `CONCAT`, cùng toán tử `||`, backtick `` ` ``, comment `/* */`.

---

## 2. `validate_url` — không thật sự chặn SSRF

**Vị trí:** [core.py dòng 8–14](securevalidator/core.py#L8-L14)

```python
def validate_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)
    except Exception:
        return False
```

**Lỗi:** Chỉ kiểm tra `scheme` và có `netloc`, **không phân giải và kiểm tra host đích thực sự**, nên URL trỏ vào tài nguyên nội bộ đều lọt.

**Kỹ thuật vượt qua:**

| # | Kỹ thuật | Payload | Vì sao nguy hiểm |
|---|---|---|---|
| 1 | **Mã hóa IP dạng hex** (dùng trong ảnh) | `http://0x7f000001` | Chính là `127.0.0.1` |
| 2 | **Mã hóa IP dạng thập phân** | `http://2130706433/` | Chính là `127.0.0.1` |
| 3 | **Mã hóa IP dạng octal** | `http://0177.0.0.1/` | Chính là `127.0.0.1` |
| 4 | **Địa chỉ metadata cloud** | `http://169.254.169.254/` | Lấy credential AWS/GCP |
| 5 | **Đánh lừa bằng userinfo (`@`)** | `http://trang-that.com@trang-gia.com/` | Host thật là `trang-gia.com`, phần trước `@` chỉ để đánh lừa |

---

## 3. `validate_filename` — chặn traversal tốt nhưng còn sót

**Vị trí:** [core.py dòng 16–20](securevalidator/core.py#L16-L20)

```python
def validate_filename(filename: str) -> bool:
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    return os.path.basename(filename) == filename
```

**Lỗi:** Chỉ chặn ký tự đường dẫn; không kiểm tra tên dành riêng và ký tự cuối mà hệ điều hành tự cắt bỏ.

**Kỹ thuật vượt qua:**

| # | Kỹ thuật | Payload | Vì sao nguy hiểm |
|---|---|---|---|
| 1 | **Dấu chấm/khoảng trắng cuối** bị Windows tự cắt (dùng trong ảnh) | `file.txt.` | Windows lưu thành `file.txt` — khác tên đã kiểm tra |
| 2 | **Tên thiết bị dành riêng** | `CON`, `PRN`, `NUL`, `AUX` | Trỏ tới thiết bị hệ thống Windows |
| 3 | Tên cổng thiết bị | `COM1`, `LPT1` | Cổng thiết bị Windows |
| 4 | Tên dành riêng kèm đuôi | `CON.txt` | Windows vẫn coi là thiết bị `CON` |

---

## 4. `validate_email` — regex quá lỏng

**Vị trí:** [core.py dòng 3–6](securevalidator/core.py#L3-L6)

```python
def validate_email(email: str) -> bool:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.fullmatch(pattern, email) is not None
```

**Lỗi:** Cho phép dấu chấm liên tiếp và dấu chấm ở đầu/cuối phần local, nên chấp nhận nhầm chuỗi không phải email hợp lệ.

**Kỹ thuật vượt qua:**

| # | Kỹ thuật | Payload | Vấn đề |
|---|---|---|---|
| 1 | **Hai dấu chấm liên tiếp** (dùng trong ảnh) | `trung..cmd@cmd.dkm` | `..` không hợp lệ theo RFC nhưng vẫn lọt |
| 2 | Dấu chấm ở đầu phần local | `.a@b.c` | Không hợp lệ nhưng regex chấp nhận |
| 3 | Dấu chấm ở cuối phần local | `a.@b.c` | Tương tự |

---

## 5. `sanitize_html_input` — an toàn trong ngữ cảnh text, nhưng lọt ở ngữ cảnh khác

**Vị trí:** [core.py dòng 29–31](securevalidator/core.py#L29-L31)

```python
def sanitize_html_input(html_str: str) -> str:
    return html.escape(html_str)
```

**Phân tích:** `html.escape` mã hóa `& < > " '`. Trong app này kết quả được đặt trong `<code>...</code>` (ngữ cảnh text) nên **an toàn** — payload `<script>alert("XSS")</script>` bị biến thành text vô hại.

**Điểm cần lưu ý (kỹ thuật vượt qua nếu đổi ngữ cảnh):** payload `javascript:alert(1)` (dùng trong ảnh) **không chứa ký tự nào bị escape**, nên nếu chuỗi này được nhét vào thuộc tính `href`/`src` hoặc vào code JS thay vì text, nó sẽ thực thi được. `html.escape` chỉ an toàn cho **ngữ cảnh HTML text**, không đủ cho ngữ cảnh URL/attribute/JavaScript.

---

## Kết luận

Nguyên nhân gốc lặp lại ở nhiều hàm: dùng **blacklist + thay thế một lần** (SQL) và **kiểm tra bề mặt** (URL/filename/email) đều bị vượt qua.

Hướng khắc phục đúng:

- **SQL:** dùng prepared statement / parameterized query thay cho lọc từ khóa.
- **URL:** phân giải host, chuẩn hóa IP, và dùng allowlist; chặn dải nội bộ (loopback, link-local `169.254.0.0/16`, private range).
- **Filename:** dùng allowlist ký tự, chặn tên dành riêng, cắt khoảng trắng/dấu chấm cuối trước khi so sánh.
- **Email:** dùng thư viện validate chuẩn thay cho regex tự viết.
- **HTML:** escape đúng theo ngữ cảnh đầu ra (text / attribute / URL / JS).
