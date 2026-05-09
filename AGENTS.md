# AGENTS.md - netlistener

## 项目概述
比赛防作弊网络监控系统。通过 scapy 嗅探 DNS 流量，自动记录非白名单域名访问并写入 CSV 日志。

## 技术栈
- Python 3.10+
- scapy（流量嗅探）
- Npcap（Windows 抓包驱动，替代 WinPcap）
- PyInstaller（打包为 .exe）
- VBScript（备用静默启动器）

## 文件结构
- `dns_monitor.py` — 核心监控脚本（带终端输出，调试用）
- `launcher.py` — 无控制台入口（PyInstaller 打包用）
- `build.py` — 一键构建脚本，编译为 netlistener.exe
- `run_silent.vbs` — 备用静默启动器（需 Python 环境）
- `cheat_log.csv` — 违规记录日志（运行后自动生成）
- `AGENTS.md` — 本文件
- `README.md` — 使用说明

## 运行前准备
1. 安装 Npcap: https://npcap.com （安装时勾选 "Install Npcap in WinPcap API-compatible Mode"）
2. 安装依赖: `pip install scapy pyinstaller`
3. 打包 .exe: `python build.py`
4. 将 `dist/netlistener.exe` 复制到比赛机器，右键以管理员身份运行

## 编码规范
- 中文注释，编码统一 UTF-8
- 函数使用类型注解
- 白名单在 `WHITELIST` 列表中配置（dns_monitor.py 和 launcher.py 各有一份，修改后需同步）

## 注意事项
- 必须以管理员权限运行，否则无法嗅探网卡流量
- 脚本依赖 Npcap 驱动，未安装会导致 scapy 报错
- `cheat_log.csv` 追加写入，不会覆盖历史记录
- 修改白名单后需重新执行 `python build.py` 重新打包 .exe
