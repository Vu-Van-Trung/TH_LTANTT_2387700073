import tkinter as tk
from tkinter import filedialog, messagebox
from securecrypto import aes_utils

def encrypt():
    file = filedialog.askopenfilename()
    if not file:
        return
    pw = password_entry.get()
    key = aes_utils.encrypt_file_aes(file, pw)
    result_label.config(text=f"Key: {key}")
    # Hien key trong o Entry de co the boi den/copy, dong thoi copy san vao clipboard
    key_entry.delete(0, tk.END)
    key_entry.insert(0, key)
    root.clipboard_clear()
    root.clipboard_append(key)

def decrypt():
    file = filedialog.askopenfilename(filetypes=[("Encrypted", "*.enc"), ("All", "*.*")])
    if not file:
        return
    # decrypt_file_aes can KEY base64 (khong phai mat khau goc)
    key = key_entry.get().strip() or password_entry.get().strip()
    try:
        out = aes_utils.decrypt_file_aes(file, key)
    except Exception as e:
        messagebox.showerror("Lỗi giải mã", f"Key sai hoặc file hỏng: {e!r}")
        return
    result_label.config(text=f"Output: {out}")

root = tk.Tk()
root.title("SecureCrypto GUI")
tk.Label(root, text="Password (dùng khi Encrypt):").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()
tk.Label(root, text="Key base64 (dùng khi Decrypt):").pack()
key_entry = tk.Entry(root, width=50)
key_entry.pack()
tk.Button(root, text="Encrypt", command=encrypt).pack()
tk.Button(root, text="Decrypt", command=decrypt).pack()
result_label = tk.Label(root, text="")
result_label.pack()
root.mainloop()
