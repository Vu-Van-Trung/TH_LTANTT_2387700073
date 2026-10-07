# Buổi 3 – Kết quả thực thi

## 1. SecureChat

### Tạo chứng chỉ – `make-certs.bat`

```
Certificate request self-signature ok
subject=C=VN, ST=HN, L=HN, O=MyOrg, OU=IT Dept, CN=localhost
Certificate request self-signature ok
subject=C=VN, ST=HN, L=HN, O=MyOrg, OU=IT Dept, CN=client

===============================
Cac chung chi da tao xong
- CA:      certs\ca\
- Server:  certs\server\
- Client:  certs\client\
===============================
```

```
certs/
├── ca/      ca.crt  ca.key  ca.srl.bak
├── client/  client.crt  client.csr  client.key
└── server/  server.crt  server.csr  server.key
```

### `python server.py`

```
Server listening on 127.0.0.1:8443
[+] Client connected: ('127.0.0.1', 49983)
[+] Client connected: ('127.0.0.1', 49984)
[trung]: xin chao
[nam]: hello
[trung]: day la ung dung chat ma hoa
[nam]: duoc ma hoa bang ssl
[-] Client disconnected: ('127.0.0.1', 49983)
[-] Client disconnected: ('127.0.0.1', 49984)
```

### `python client.py` – Client 1

```
Username: trung
Type messages (type 'exit' to quit):
xin chao
[nam]: hello
day la ung dung chat ma hoa
[nam]: duoc ma hoa bang ssl
exit
```

### `python client.py` – Client 2

```
Username: nam
Type messages (type 'exit' to quit):
[trung]: xin chao
hello
[trung]: day la ung dung chat ma hoa
duoc ma hoa bang ssl
exit
```

## 2. NetRecon

### `python cli.py --target 127.0.0.1 --ports 21,22,80,135,443,445 --mode all`

```
[+] 135/tcp open
[+] 445/tcp open
Error: nmap not found. Install Nmap and add it to PATH.
21: Failed to grab banner: timed out
22: Failed to grab banner: timed out
80: Failed to grab banner: timed out
135: Failed to grab banner: timed out
443: Failed to grab banner: timed out
445: Failed to grab banner: timed out

Interface: 192.168.62.1 --- 0x6
  Internet Address      Physical Address      Type
  192.168.62.254        00-50-56-e3-5a-cf     dynamic
  192.168.62.255        ff-ff-ff-ff-ff-ff     static
  224.0.0.22            01-00-5e-00-00-16     static
  224.0.0.251           01-00-5e-00-00-fb     static
  224.0.0.252           01-00-5e-00-00-fc     static
  239.255.255.250       01-00-5e-7f-ff-fa     static
  255.255.255.255       ff-ff-ff-ff-ff-ff     static
...

{21: 'FTP - CVE-2015-3306, CVE-2001-0261', 22: 'SSH - CVE-2018-15473', 80: 'HTTP - CVE-2021-41773', 443: 'HTTPS - CVE-2021-3449'}
```

### `python app.py`

```
 * Serving Flask app 'app'
 * Debug mode: on
[+] 135/tcp open
[+] 445/tcp open
[-] Email failed: Connection unexpectedly closed
```

### `http://127.0.0.1:5000/` → Scan (target `127.0.0.1`, ports `22,80,135,445`, mode `All`)

```
GET /      -> 200
POST /scan -> 200

Scan Result:
135/tcp open
445/tcp open

Service Detection:
Error: nmap not found. Install Nmap and add it to PATH.

Banner Grabbing:
  • Port 22: Failed to grab banner: timed out
  • Port 80: Failed to grab banner: timed out
  • Port 135: Failed to grab banner: timed out
  • Port 445: Failed to grab banner: timed out

Network Map:
Interface: 192.168.62.1 --- 0x6
  Internet Address      Physical Address      Type
  192.168.62.254        00-50-56-e3-5a-cf     dynamic
  ...

Vulnerability Check:
  • Port 22: SSH - CVE-2018-15473
  • Port 80: HTTP - CVE-2021-41773
```
