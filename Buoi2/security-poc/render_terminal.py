"""Render output PoC thanh anh terminal (nen toi) de chen vao README."""
from PIL import Image, ImageDraw, ImageFont
import os

BG = (13, 17, 23)
FG = (215, 220, 230)
DIM = (123, 132, 148)
GREEN = (76, 208, 138)
RED = (255, 122, 125)
CYAN = (127, 212, 255)
YELLOW = (255, 210, 87)

PAD = 20
LH = 24
FS = 16

def load_font():
    for p in [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\CascadiaMono.ttf",
        r"C:\Windows\Fonts\lucon.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, FS)
    return ImageFont.load_default()

FONT = load_font()

def color_for(line):
    s = line.strip()
    if s.startswith(">>>"):
        low = s.lower()
        if any(k in low for k in ["bi ghi de", "qua mat", "lo key", "that bai"]):
            return RED
        if "go thu hoi" in low or "mat toan bo" in low or "cach sua" in low:
            return RED
        return YELLOW
    if s.startswith("==="):
        return DIM
    if s.startswith("[+]") or s.startswith("[i]"):
        return CYAN
    if "= True" in line or "revoked = True" in line:
        # highlight True/False handled per-line below; keep base
        return FG
    return FG

def render(lines, out_path, title):
    # title bar + content
    width_chars = max((len(l) for l in lines), default=40)
    W = PAD * 2 + int(width_chars * FS * 0.60) + 20
    W = max(W, 620)
    H = PAD * 2 + LH * (len(lines) + 2)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, W, 34], fill=(30, 36, 46))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([14 + i * 20, 12, 26 + i * 20, 24], fill=c)
    d.text((90, 9), title, font=FONT, fill=DIM)
    y = 44
    for line in lines:
        col = color_for(line)
        # highlight True (red) / False depending on context words already colored
        d.text((PAD, y), line, font=FONT, fill=col)
        y += LH
    img.save(out_path)
    print("saved", out_path, img.size)

# ---- PoC CA ----
ca_lines = [
    "> python poc_ca.py",
    "",
    "=== PoC 2 - common_name ghi de khoa Root CA ===",
    "Khoa Root truoc/sau co giong nhau khong? False",
    ">>> KET QUA: BI GHI DE (khoa Root da bi thay!)",
    "",
    "=== PoC 3 - Chuoi tin cay gia mao (khong trust anchor) ===",
    "verify_certificate_chain(cert gia, chuoi ke tan cong) = True",
    ">>> KET QUA: QUA MAT (chap nhan cert gia mao!)",
    "",
    "=== PoC 4 - 'Go thu hoi' bang cach thay CRL ===",
    "Sau khi thu hoi:       revoked = True",
    "Sau khi thay CRL gia:  revoked = False",
    ">>> KET QUA: cert da thu hoi gio lai bao 'Hop le'",
]

# ---- PoC AES ----
aes_lines = [
    "> python poc_aes.py",
    "",
    "[+] App IN RA key (bi mat bi lo):",
    "    PeWRrMgM2JCWRvoSLeNeyll/eW2at2ZWADUxC4an7Qo=",
    "",
    "=== LOI A: chi can KEY (mat khau bo trong) ===",
    "Ke tan cong doc duoc: Thong tin bi mat - HUTECH",
    ">>> Lo KEY = mat toan bo bao mat.",
    "",
    "=== LOI B: dua MAT KHAU vao ham decrypt ===",
    ">>> That bai: Error  (ham doi KEY, khong phai mat khau)",
]

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINI = os.path.join(BASE, "mini-ca", "anh")
CRYP = os.path.join(BASE, "crypto-toolkit", "anh")

# Anh gop
render(ca_lines, os.path.join(MINI, "poc_ket_qua_terminal.png"), "PoC ket qua - mini-ca")
render(aes_lines, os.path.join(CRYP, "poc_ket_qua_terminal.png"), "PoC ket qua - crypto-toolkit")

# --- Anh rieng tung lo hong (mini-ca) ---
render([
    "> python poc_ca.py    # PoC 2",
    "=== common_name ghi de khoa Root CA ===",
    "Khoa Root truoc/sau co giong nhau khong? False",
    ">>> KET QUA: BI GHI DE (khoa Root da bi thay!)",
], os.path.join(MINI, "poc2_ghi_de_khoa.png"), "PoC 2 - ghi de khoa CA")

render([
    "> python poc_ca.py    # PoC 3",
    "=== Chuoi tin cay gia mao (khong trust anchor) ===",
    "verify_certificate_chain(cert gia, chuoi ke tan cong) = True",
    ">>> KET QUA: QUA MAT (chap nhan cert gia mao!)",
], os.path.join(MINI, "poc3_chuoi_gia_mao.png"), "PoC 3 - chuoi gia mao")

render([
    "> python poc_ca.py    # PoC 4",
    "=== 'Go thu hoi' bang cach thay CRL ===",
    "Sau khi thu hoi:       revoked = True",
    "Sau khi thay CRL gia:  revoked = False",
    ">>> KET QUA: cert da thu hoi gio lai bao 'Hop le'",
], os.path.join(MINI, "poc4_bypass_crl.png"), "PoC 4 - bypass CRL")

# --- Anh rieng tung lo hong (crypto-toolkit) ---
render([
    "> python poc_aes.py    # LOI A",
    "[+] App IN RA key (bi mat bi lo):",
    "    PeWRrMgM2JCWRvoSLeNeyll/eW2at2ZWADUxC4an7Qo=",
    "=== Chi can KEY (mat khau bo trong) ===",
    "Ke tan cong doc duoc: Thong tin bi mat - HUTECH",
    ">>> Lo KEY = mat toan bo bao mat.",
], os.path.join(CRYP, "poc_lo_key.png"), "PoC - lo key")

render([
    "> python poc_aes.py    # LOI B",
    "=== Dua MAT KHAU vao ham decrypt ===",
    ">>> That bai: Error  (ham doi KEY, khong phai mat khau)",
    "Salt nam trong file nhung KHONG duoc dung.",
], os.path.join(CRYP, "poc_decrypt_sai.png"), "PoC - decrypt bo salt")
