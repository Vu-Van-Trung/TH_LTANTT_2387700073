import asyncio, logging
from datetime import datetime

logging.basicConfig(filename='netrecon.log', level=logging.INFO)

def log(message):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"[{now}] {message}")

async def scan_port(target, port, semaphore):
    try:
        async with semaphore:
            conn = asyncio.open_connection(target, port)
            reader, writer = await asyncio.wait_for(conn, timeout=1)
            log(f"Port {port} is open on {target}")
            print(f"[+] {port}/tcp open")
            writer.close()
            await writer.wait_closed()
            return port
    except Exception:
        return None

async def async_scan_ports(target, ports, rate_limit=100):
    semaphore = asyncio.Semaphore(rate_limit)
    tasks = [scan_port(target, port, semaphore) for port in ports]
    results = await asyncio.gather(*tasks)
    open_ports = [p for p in results if p is not None]
    return "\n".join(f"{p}/tcp open" for p in open_ports) or "No open ports found"
