# -*- coding: utf-8 -*-
"""DNS 流量监控脚本 — 比赛防作弊系统

通过 scapy 监听网卡 DNS 查询，记录不在白名单内的域名访问。
白名单由同目录 config.json 管理，无需修改代码。
"""

import os
import sys
import csv
import json
import logging
import datetime
from typing import List

# ============================================================
# 配置区
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "cheat_log.csv")
DEBUG_LOG = os.path.join(SCRIPT_DIR, "dns_debug.log")

WHITELIST: List[str] = []
DEBUG_MODE: bool = False


def load_config() -> None:
    """从 config.json 加载白名单和调试模式配置。"""
    global WHITELIST, DEBUG_MODE
    if not os.path.isfile(CONFIG_FILE):
        print(f"[错误] 找不到配置文件: {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    WHITELIST = data.get("whitelist", [])
    DEBUG_MODE = data.get("debug", False)

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


def normalize_domain(domain: str) -> str:
    """标准化域名：去尾部点号、转小写、去首尾空格。"""
    return domain.strip().rstrip(".").lower()


def is_whitelisted(domain: str) -> bool:
    """判断域名是否匹配白名单。精确匹配或子域名匹配。"""
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
    """调试模式下记录所有 DNS 查询到 debug 日志。"""
    if not DEBUG_MODE:
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


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

    src_ip = pkt[IP].src if pkt.haslayer(IP) else "未知"

    # 遍历包中所有 DNS 查询记录（一个包可能包含多个查询）
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

        # 调试模式：记录所有查询（含白名单命中）
        write_debug_log(
            f"{'[通过]' if matched else '[违规]'} "
            f"域名={clean}  来源={src_ip}  "
            f"白名单匹配={'是' if matched else '否'}"
        )

        # 白名单放行
        if matched:
            continue

        # 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 记录到 CSV
        write_csv_row(timestamp, src_ip, clean)

        # 控制台输出（静默运行时不可见，调试时有用）
        print(f"[!] 检测到非白名单域名: {clean}  来源: {src_ip}")


# ============================================================
# 主入口
# ============================================================

def main() -> None:
    # 加载配置
    load_config()

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

    print(f"[*] 白名单 ({len(WHITELIST)} 个): {WHITELIST}")
    print(f"[*] 调试模式: {'开启' if DEBUG_MODE else '关闭'}")
    print(f"[*] 日志文件: {LOG_FILE}")
    if DEBUG_MODE:
        print(f"[*] 调试日志: {DEBUG_LOG}")
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
