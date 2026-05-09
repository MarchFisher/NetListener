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
- `config.json` — 白名单和调试模式配置（唯一需要修改的文件）
- `run_silent.vbs` — 备用静默启动器（需 Python 环境）
- `cheat_log.csv` — 违规记录日志（运行后自动生成）
- `dns_debug.log` — 调试日志（debug=true 时生成）
- `netlistener_error.log` — 启动错误日志（.exe 无控制台模式下的错误记录）
- `AGENTS.md` — 本文件
- `README.md` — 使用说明

## 运行前准备
1. 安装 Npcap: https://npcap.com （安装时勾选 "Install Npcap in WinPcap API-compatible Mode"）
2. 安装依赖: `pip install scapy pyinstaller`
3. 打包 .exe: `python build.py`
4. 将 `dist/netlistener.exe` 和 `config.json` 复制到比赛机器，双击运行

## 配置说明
- 白名单在 `config.json` 的 `whitelist` 数组中配置，修改后无需重新打包
- `debug: true` 开启调试模式，所有 DNS 查询（含白名单命中）记录到 `dns_debug.log`
- .exe 运行时需将 `config.json` 放在与 .exe 同目录

## 编码规范
- 中文注释，编码统一 UTF-8
- 函数使用类型注解

## 注意事项
- 必须以管理员权限运行，否则无法嗅探网卡流量
- 脚本依赖 Npcap 驱动，未安装会导致 scapy 报错
- `cheat_log.csv` 追加写入，不会覆盖历史记录
- .exe 静默运行时，启动错误记录到 `netlistener_error.log`，排查问题时请先检查此文件
