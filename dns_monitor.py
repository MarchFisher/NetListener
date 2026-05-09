# -*- coding: utf-8 -*-
"""DNS 流量监控脚本 — 比赛防作弊系统
通过 scapy 监听网卡 DNS 查询，记录不在白名单内的域名访问。
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

# 白名单域名列表（支持子域名匹配，例如 a.com 匹配 x.a.com）
WHITELIST: List[str] = [
    "domjudge.seucpc.com",
    "oj.seucpc.com",
    "seu.edu.cn",
    "seucpc.com",
    "edge.microsoft.com",
    "localhost",
]

# CSV 日志文件路径（与脚本同目录）
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cheat_log.csv")

# ============================================================
# 日志配置（抑制 scapy 的噪音输出）
# ============================================================
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

try:
    from scapy.all import sniff, DNS, DNSQR, IP, conf
except ImportError:
    print("[错误] 未安装 scapy，请执行: pip install scapy")
    sys.exit(1)


# ============================================================
# 工具函数
# ============================================================

def get_default_interface() -> str:
    """自动识别默认网卡。Windows 下优先返回 conf.iface（scapy 默认网卡）。"""
    try:
        iface = conf.iface
        if iface:
            return iface
    except Exception:
        pass
    return None


def is_whitelisted(domain: str) -> bool:
    """判断域名是否匹配白名单。精确匹配或子域名匹配。"""
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


# ============================================================
# 核心回调：处理每一个捕获的 DNS 包
# ============================================================

def dns_packet_callback(pkt) -> None:
    """scapy 嗅探回调函数，解析 DNS 查询请求。"""
    if not pkt.haslayer(DNS) or not pkt.haslayer(DNSQR):
        return

    # 只处理 DNS 查询（QR=0），忽略响应（QR=1）
    if pkt[DNS].qr != 0:
        return

    # 提取查询的域名
    queried_domain = pkt[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")

    # 白名单放行
    if is_whitelisted(queried_domain):
        return

    # 提取源 IP
    src_ip = pkt[IP].src if pkt.haslayer(IP) else "未知"

    # 生成时间戳
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 记录到 CSV
    write_csv_row(timestamp, src_ip, queried_domain)

    # 控制台输出（静默运行时不可见，调试时有用）
    print(f"[!] 检测到非白名单域名: {queried_domain}  来源: {src_ip}")


# ============================================================
# 主入口
# ============================================================

def main() -> None:
    # 权限检测（Windows 管理员权限）
    if os.name == "nt":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("[错误] 请以管理员身份运行此脚本。")
            print("       右键点击 run_silent.vbs -> 以管理员身份运行")
            sys.exit(1)

    # 自动识别默认网卡
    interface = get_default_interface()
    if interface is None:
        print("[警告] 无法自动识别默认网卡，将使用 scapy 默认网卡。")
    else:
        print(f"[*] 监听网卡: {interface}")

    print(f"[*] 白名单域名: {WHITELIST}")
    print(f"[*] 日志文件: {LOG_FILE}")
    print("[*] 开始监听 DNS 流量... (Ctrl+C 停止)")

    # 开始嗅探：过滤 UDP 53 端口（DNS）
    sniff(
        iface=interface,
        filter="udp port 53",
        prn=dns_packet_callback,
        store=0,
        quiet=True,
    )


if __name__ == "__main__":
    main()
