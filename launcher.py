# -*- coding: utf-8 -*-
"""静默启动入口 — 用于 PyInstaller 打包为 .exe（无控制台窗口）

双击 .exe 即可后台运行，选手不会看到任何终端窗口。
白名单由同目录 config.json 管理，修改后无需重新打包。
"""

import os
import sys
import csv
import json
import logging
import datetime
from typing import List


# ============================================================
# 配置加载（兼容 PyInstaller 打包）
# ============================================================

def _get_base_dir() -> str:
    """获取运行时基础目录。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _get_base_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "cheat_log.csv")
DEBUG_LOG = os.path.join(BASE_DIR, "dns_debug.log")
ERROR_LOG = os.path.join(BASE_DIR, "netlistener_error.log")

WHITELIST: List[str] = []
DEBUG_MODE: bool = False


def load_config() -> None:
    """从 config.json 加载白名单和调试模式配置。"""
    global WHITELIST, DEBUG_MODE
    if not os.path.isfile(CONFIG_FILE):
        _log_error(f"config.json not found at: {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    WHITELIST = data.get("whitelist", [])
    DEBUG_MODE = data.get("debug", False)


logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

try:
    from scapy.all import sniff, DNS, DNSQR, IP, conf
except ImportError:
    _log_error("scapy not installed. Run: pip install scapy")
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


def normalize_domain(domain: str) -> str:
    """标准化域名：去尾部点号、转小写、去首尾空格。"""
    return domain.strip().rstrip(".").lower()


def is_whitelisted(domain: str) -> bool:
    """判断域名是否匹配白名单（精确匹配或子域名匹配）。"""
    domain = normalize_domain(domain)
    for allowed in WHITELIST:
        allowed = normalize_domain(allowed)
        if not allowed:
            continue
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


def write_debug_log(msg: str) -> None:
    """调试模式下记录所有 DNS 查询。"""
    if not DEBUG_MODE:
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def dns_packet_callback(pkt) -> None:
    """scapy 嗅探回调函数，解析 DNS 查询请求。"""
    if not pkt.haslayer(DNS) or not pkt.haslayer(DNSQR):
        return
    if pkt[DNS].qr != 0:
        return
    src_ip = pkt[IP].src if pkt.haslayer(IP) else "未知"
    for i in range(pkt[DNS].qdcount):
        try:
            qr = pkt[DNS].qd
            if hasattr(qr, '__iter__') and not isinstance(qr, bytes):
                queried_domain = qr[i].qname.decode("utf-8", errors="ignore").rstrip(".")
            else:
                queried_domain = pkt[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
        except Exception:
            continue
        clean = normalize_domain(queried_domain)
        if not clean:
            continue
        matched = is_whitelisted(clean)
        write_debug_log(
            f"{'[通过]' if matched else '[违规]'} "
            f"域名={clean}  来源={src_ip}  "
            f"白名单匹配={'是' if matched else '否'}"
        )
        if matched:
            continue
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_csv_row(ts, src_ip, clean)


# ============================================================
# 主入口（静默模式，无 print 输出）
# ============================================================

def main() -> None:
    load_config()

    if os.name == "nt":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            _log_error("Not running as Administrator")
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
def _log_error(msg: str) -> None:
    """将启动错误写入日志文件（无控制台模式下唯一的错误输出）。"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}")
        f.write("\n")
