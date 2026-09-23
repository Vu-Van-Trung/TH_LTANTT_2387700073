# Lab3 — Phân tích điểm yếu của cơ chế ghi log an toàn (`securelogger`)
## Ảnh minh chứng

![Payload làm lộ mật khẩu trong secure.log](Screenshot%202026-09-23%20202845.png)

Trong ảnh: gửi payload `{"email":"a@b.com","password":"SuperSecret123"}` bằng lệnh

```powershell
'{"email":"a@b.com","password":"SuperSecret123"}' | Out-File -Encoding ascii body.json
curl.exe -X POST http://127.0.0.1:5000/validate -H "Content-Type: application/json" --data-binary "@body.json"
```

thì dòng ghi vào `secure.log` (dòng 5 trong ảnh) chứa **nguyên văn mật khẩu**:

```
"data": "{'email': '<email_masked>', 'password': 'SuperSecret123'}"
```

Email bị che (`<email_masked>`) nhưng **mật khẩu thì không** — bộ lọc che PII đã bị vượt qua.

---

## 1. Che PII bị vượt qua — mật khẩu lọt vào log

**Vị trí:**
- Bộ lọc: [securelogger/logger.py:10-18](securelogger/logger.py#L10-L18) — `PII_PATTERNS` và `mask_pii`.
- Áp dụng: [securelogger/logger.py:36](securelogger/logger.py#L36) — `mask_pii(str(record.data))`.
- Nguồn dữ liệu: [app.py:28-29](app.py#L28-L29) — `extra={"data": data}` (log cả body).

```python
PII_PATTERNS = {
    "email": r'[\w\.-]+@[\w\.-]+\.\w+',
    "token": r'(?i)(token|apikey|key|password)\s*=\s*["\']?[\w\-]{8,}["\']?',
}
```

**Lỗi:** Regex `token` chỉ khớp dạng `key=value` (dấu **`=`**). Nhưng `str(dict)` của Python
sinh ra dạng `'password': 'SuperSecret123'` — dùng dấu **`:`** và **nháy đơn**, không có `=`.
Vì vậy mẫu không khớp và mật khẩu **không bị che**.

**Kỹ thuật vượt qua & payload** (đã kiểm chứng bằng `mask_pii`):

| # | Kỹ thuật | Payload (đầu vào `mask_pii`) | Kết quả |
|---|---|---|---|
| 1 | **Đổi dấu phân tách** `=` → `:` (định dạng dict) | `{'password': 'SuperSecret123'}` | `{'password': 'SuperSecret123'}` — **lọt** |
| 2 | So sánh: đúng dạng `key=value` thì mới bị che | `password=SuperSecret123` | `<token_masked>` |

> Kỹ thuật: chỉ cần dữ liệu nhạy cảm nằm trong một `dict` (đúng như luồng thật ở
> `app.py`, JSON body được log dưới dạng `str(dict)`), dấu phân tách sẽ là `: ` thay vì
> `=`, đủ để trượt khỏi regex. Không cần thủ thuật gì thêm — **định dạng mặc định của
> `str(dict)` chính là payload**.

---
