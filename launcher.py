# -*- coding: utf-8 -*-
"""静默启动入口 — 用于 PyInstaller 打包为 .exe（无控制台窗口）

此文件是 dns_monitor.py 的无控制台版本入口。
通过 PyInstaller --noconsole 打包后，双击 .exe 即可后台运行，
选手不会看到任何终端窗口。
"""

import os
import sys
import csv
import logging
import datetime
from typing import List

# ============================================================
# 配置区
# ============================================================

# 白名单域名列表（支持子域名匹配）
WHITELIST: List[str] = [
    "competition.com",
    "localhost",
    "github.com",
    "api.competition.com",
]

# 日志文件路径：与 .exe 同目录
def _get_log_path() -> str:
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，sys.executable 指向 .exe 所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "cheat_log.csv")

LOG_FILE = _get_log_path()

# 抑制 scapy 噪音
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

try:
    from scapy.all import sniff, DNS, DNSQR, IP, conf
except ImportError:
    sys.exit(1)


# ============================================================
# 工具函数
# ============================================================

def get_default_interface() -> str:
    """自动识别默认网卡。"""
    try:
        iface = conf.iface
        if iface:
            return iface
    except Exception:
        pass
    return None


def is_whitelisted(domain: str) -> bool:
    """判断域名是否匹配白名单（精确匹配或子域名匹配）。"""
    domain = domain.rstrip(".").lower()
    for allowed in WHITELIST:
        allowed = allowed.strip().lower()
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False


def write_csv_row(timestamp: str, src_ip: str, domain: str) -> None:
    """将一条违规记录追加写入 CSV 文件。"""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["时间戳", "源IP", "目标域名"])
        writer.writerow([timestamp, src_ip, domain])


def dns_packet_callback(pkt) -> None:
    """scapy 嗅探回调函数，解析 DNS 查询请求。"""
    if not pkt.haslayer(DNS) or not pkt.haslayer(DNSQR):
        return
    if pkt[DNS].qr != 0:
        return
    queried_domain = pkt[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
    if is_whitelisted(queried_domain):
        return
    src_ip = pkt[IP].src if pkt.haslayer(IP) else "未知"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_csv_row(timestamp, src_ip, queried_domain)


# ============================================================
# 主入口（静默模式，无 print 输出）
# ============================================================

def main() -> None:
    # 权限检测
    if os.name == "nt":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            sys.exit(1)

    interface = get_default_interface()

    sniff(
        iface=interface,
        filter="udp port 53",
        prn=dns_packet_callback,
        store=0,
        quiet=True,
    )


if __name__ == "__main__":
    main()
