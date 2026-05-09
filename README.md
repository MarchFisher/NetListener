# netlistener - 比赛防作弊 DNS 网络监控系统

## 简介

通过 scapy 嗅探网卡 DNS 流量，自动记录非白名单域名的访问行为，用于竞赛场景下检测选手是否连接外网。

## 运行环境

| 依赖 | 版本 | 说明 |
|------|------|------|
| Windows | 10 / 11 | 操作系统 |
| Python | 3.10+ | 运行时（仅打包时需要） |
| scapy | latest | 流量嗅探库 |
| Npcap | latest | Windows 抓包驱动 |
| PyInstaller | latest | .exe 打包工具（仅打包时需要） |

## 安装步骤

### 1. 安装 Npcap

前往 https://npcap.com 下载安装程序。

> **重要**：安装时必须勾选 **"Install Npcap in WinPcap API-compatible Mode"**，否则 scapy 无法正常工作。

### 2. 安装 Python 依赖

```bash
pip install scapy pyinstaller
```

### 3. 打包为 .exe

```bash
python build.py
```

构建完成后，`dist/netlistener.exe` 即为可分发的独立程序。

## 使用方法

### 方法一：双击 .exe 运行（比赛推荐）

1. 安装好 Npcap 驱动
2. 将 `netlistener.exe` 复制到比赛机器
3. **双击运行**，会自动弹出管理员权限请求（UAC），点击"是"即可
4. 程序将在后台静默运行，选手不会看到任何终端窗口
5. 违规记录自动写入与 .exe 同目录的 `cheat_log.csv`

> 无需安装 Python，.exe 已包含全部运行时。

### 方法二：VBS 静默运行（需 Python 环境）

1. 找到项目目录下的 `run_silent.vbs` 文件
2. **右键** -> **以管理员身份运行**
3. 程序将在后台静默运行，选手不会看到任何终端窗口
4. 违规记录自动写入 `cheat_log.csv`

### 方法三：命令行运行（调试用）

1. 以 **管理员权限** 打开终端（PowerShell / CMD）
2. 进入项目目录
3. 执行：

```bash
python dns_monitor.py
```

终端会实时输出检测到的非白名单域名访问信息。

## 日志输出

违规记录写入与程序同目录的 `cheat_log.csv` 文件，格式如下：

| 时间戳 | 源IP | 目标域名 |
|--------|------|----------|
| 2025-01-01 10:23:45 | 192.168.1.100 | www.example.com |

每次追加写入，不会覆盖历史记录。

## 终止程序

### 方法一：任务管理器

1. 按 `Ctrl + Shift + Esc` 打开任务管理器
2. 切换到 **详细信息** 选项卡
3. 找到以下任一进程并右键 -> **结束任务**：
   - `netlistener.exe`（.exe 方式启动）
   - `python.exe` / `pythonw.exe`（VBS 或命令行方式启动）

### 方法二：命令行终止

以管理员权限打开终端，执行：

```powershell
# 终止 .exe 进程
Stop-Process -Name netlistener -Force -ErrorAction SilentlyContinue

# 终止 Python 进程
Stop-Process -Name python*, pythonw* -Force -ErrorAction SilentlyContinue
```

或使用 CMD：

```cmd
taskkill /F /IM netlistener.exe
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
```

## 白名单配置

编辑 `dns_monitor.py`（或 `launcher.py`）顶部的 `WHITELIST` 列表：

```python
WHITELIST: List[str] = [
    "competition.com",
    "localhost",
    "github.com",
    "api.competition.com",
]
```

> 注意：修改白名单后需重新执行 `python build.py` 重新打包 .exe。

支持子域名匹配（例如白名单中的 `competition.com` 会同时匹配 `www.competition.com`）。

## 注意事项

- **必须以管理员权限运行**，否则无法嗅探网卡流量
- **必须安装 Npcap 驱动**，未安装会报错
- .exe 方式运行时，`cheat_log.csv` 生成在 .exe 所在目录
- VBS / 命令行方式运行时，`cheat_log.csv` 生成在脚本所在目录
- `cheat_log.csv` 为追加模式，多次运行的日志会合并在一起

