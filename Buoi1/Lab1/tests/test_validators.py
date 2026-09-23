import unittest
from securevalidator import (
    validate_email, validate_url, validate_filename,
    sanitize_sql_input, sanitize_html_input
)

class TestValidators(unittest.TestCase):
    def setUp(self):
        print("\n Running:", self._testMethodName)

    def test_validate_email_valid(self):
        self.assertTrue(validate_email("user@example.com"))

    def test_validate_email_invalid(self):
        self.assertFalse(validate_email("user@@example..com"))

    def test_validate_url_valid(self):
        self.assertTrue(validate_url("https://example.com"))

    def test_validate_url_invalid(self):
        self.assertFalse(validate_url("ftp://example.com"))

    def test_validate_filename_valid(self):
        self.assertTrue(validate_filename("report.pdf"))

    def test_validate_filename_traversal(self):
        self.assertFalse(validate_filename("../../etc/passwd"))

    def test_sanitize_sql_input_injection(self):
        input_str = "' OR 1=1 --"
        sanitized = sanitize_sql_input(input_str)
        self.assertNotIn("'", sanitized)
        self.assertNotIn("--", sanitized)
        self.assertNotIn("OR", sanitized.upper())

    def test_sanitize_sql_input_safe_text(self):
        input_str = "hello world"
        sanitized = sanitize_sql_input(input_str)
        self.assertEqual(sanitized, "hello world")

    def test_sanitize_html_input_script(self):
        input_str = '<script>alert("XSS")</script>'
        sanitized = sanitize_html_input(input_str)
        self.assertEqual(sanitized, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')

    def test_sanitize_html_input_safe_text(self):
        input_str = "Hello World"
        sanitized = sanitize_html_input(input_str)
        self.assertEqual(sanitized, "Hello World")

class TestBypassVulnerabilities(unittest.TestCase):
    """Chứng minh các payload vượt qua bộ lọc hiện tại.

    Mỗi test khẳng định *hành vi yếu hiện tại*: payload nguy hiểm
    vẫn lọt qua. Test PASS = lỗ hổng có thật. Comment ghi rõ một
    bộ lọc an toàn lẽ ra phải xử lý thế nào.
    """

    def setUp(self):
        print("\n Running:", self._testMethodName)

    # --- sanitize_sql_input: thay thế 1 lần, không đệ quy ---

    def test_sql_nested_keyword_survives(self):
        # "SELECT" nằm giữa bị xóa xong ghép lại thành "SELECT" mới.
        result = sanitize_sql_input("SELSELECTECT")
        self.assertIn("SELECT", result.upper())  # lẽ ra phải bị xóa sạch

    def test_sql_nested_or_survives(self):
        # Xóa "OR" ở giữa "OORr" để lại "OR"; "1=1" không bị đụng tới.
        result = sanitize_sql_input("1 OORr 1=1")
        self.assertIn("OR", result.upper())
        self.assertIn("1=1", result)

    def test_sql_keyword_not_in_blacklist(self):
        # EXEC/SLEEP/HAVING... không có trong danh sách cấm.
        result = sanitize_sql_input("1 EXEC SLEEP 5 HAVING")
        self.assertIn("EXEC", result.upper())
        self.assertIn("SLEEP", result.upper())
        self.assertIn("HAVING", result.upper())

    def test_sql_block_comment_survives(self):
        # Chỉ chặn "--" và "#", không chặn comment kiểu /* */.
        result = sanitize_sql_input("1/*bypass*/=1")
        self.assertIn("/*", result)

    # --- validate_url: không thật sự chặn SSRF ---

    def test_url_localhost_passes(self):
        self.assertTrue(validate_url("http://127.0.0.1/"))       # lẽ ra chặn
        self.assertTrue(validate_url("http://localhost/"))       # lẽ ra chặn

    def test_url_cloud_metadata_passes(self):
        # Endpoint metadata của cloud — SSRF kinh điển.
        self.assertTrue(validate_url("http://169.254.169.254/"))

    def test_url_decimal_ip_passes(self):
        # 2130706433 == 127.0.0.1 dạng thập phân.
        self.assertTrue(validate_url("http://2130706433/"))

    def test_url_userinfo_trick_passes(self):
        # Host thật là trang-gia.com, phần trước @ chỉ là userinfo.
        self.assertTrue(validate_url("http://trang-that.com@trang-gia.com/"))

    # --- validate_filename: còn lọt vài loại ---

    def test_filename_windows_reserved_passes(self):
        # Tên thiết bị Windows vẫn được coi là hợp lệ.
        self.assertTrue(validate_filename("CON"))
        self.assertTrue(validate_filename("COM1"))

    # --- validate_email: regex quá lỏng ---

    def test_email_accepts_malformed(self):
        # Các chuỗi không phải email thật vẫn được chấp nhận.
        self.assertTrue(validate_email("a..b@c.d"))
        self.assertTrue(validate_email(".a@b.c"))


if __name__ == "__main__":
    unittest.main()
