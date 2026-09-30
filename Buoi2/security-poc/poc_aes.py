"""
PoC 5 - Lo KEY & thiet ke giai ma sai trong securecrypto/aes_utils.py

Su that ky thuat:
  - encrypt_file_aes(path, password): derive key tu password+salt, ma hoa,
    ghi salt+nonce+ct ra file, roi TRA VE key (base64).
  - decrypt_file_aes(enc, key_base64): DOC salt tu file nhung KHONG dung,
    ma nhan thang KEY nguoi goi dua vao.

Hai loi that su:
  (A) App PHOI BAY key (in ra CLI, tra trong JSON API, hien tren GUI).
      => Ai nhat duoc key (tu log/response/clipboard) la giai ma duoc,
         KHONG can biet mat khau.
  (B) Ham decrypt bo qua salt va doi KEY chu khong phai mat khau.
      => Dua mat khau vao (dung nhu ten tham so --password goi y) -> THAT BAI.

Chay:
    cd D:\\TH_LTANTT_2387700073\\Buoi2\\security-poc
    python poc_aes.py
"""
import os
import sys
import tempfile

CT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crypto-toolkit")
sys.path.insert(0, CT)

from securecrypto import aes_utils


def line(t):
    print("\n" + "=" * 60 + f"\n{t}\n" + "=" * 60)


work = tempfile.mkdtemp(prefix="aes_poc_")
target = os.path.join(work, "secret.txt")
with open(target, "w", encoding="utf-8") as f:
    f.write("Thong tin bi mat - HUTECH")

key = aes_utils.encrypt_file_aes(target, "MatKhauDung")
print(f"[+] Ma hoa 'secret.txt' voi mat khau 'MatKhauDung'")
print(f"[+] App IN RA key nay cho nguoi dung (day chinh la bi mat bi lo):")
print(f"    {key}")

line("LOI A: Chi can KEY (mat khau bo trong) van giai ma duoc")
# Nguoi tan cong khong biet mat khau, chi nhat duoc 'key' tu log/API/clipboard.
out = aes_utils.decrypt_file_aes(target + ".enc", key)
print("Ke tan cong doc duoc:", open(out, encoding="utf-8").read())
print(">>> Lo KEY = mat toan bo bao mat, mat khau khong con y nghia bao ve.")

line("LOI B: Dua MAT KHAU vao ham decrypt (nhu ten --password) -> THAT BAI")
try:
    aes_utils.decrypt_file_aes(target + ".enc", "MatKhauDung")
    print(">>> Giai ma duoc (bat ngo)")
except Exception as e:
    print(f">>> That bai: {type(e).__name__}")
    print(">>> Ham decrypt doi KEY base64, KHONG phai mat khau.")
    print("    Tham so CLI '--password' khi giai ma la gay hieu nham.")

line("Chung minh: ham decrypt DOC salt nhung KHONG dung")
raw = open(target + ".enc", "rb").read()
salt_trong_file = raw[:16].hex()
print(f"Salt nam trong file (16 byte dau): {salt_trong_file}")
print("Dang le decrypt phai: doc salt -> derive key tu MAT KHAU -> giai ma.")
print("Thuc te decrypt: bo qua salt, dung thang key nguoi goi dua vao.")
print("=> Cach sua: decrypt nhan MAT KHAU, tu derive lai key tu salt, KHONG lo key.")

print(f"\n[i] Thu muc tam: {work}")
