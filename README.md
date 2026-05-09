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

构建完成后，`dist/` 目录下会生成 `netlistener.exe` 和 `config.json`。

## 配置白名单

编辑 `config.json` 文件：

```json
{
  "whitelist": [
    "domjudge.seucpc.com",
    "oj.seucpc.com",
    "seu.edu.cn",
    "seucpc.com",
    "edge.microsoft.com",
    "localhost"
  ],
  "debug": false
}
```

- `whitelist`: 白名单域名列表，支持子域名匹配（例如 `seucpc.com` 会匹配 `oj.seucpc.com`）
- `debug`: 设为 `true` 开启调试模式，所有 DNS 查询会记录到 `dns_debug.log`（含白名单命中标记）

> 修改 `config.json` 后无需重新打包 .exe，重启程序即可生效。
>
> 若使用 .exe 方式运行，需将 `config.json` 放在与 `netlistener.exe` 同一目录下。

## 使用方法

### 方法一：双击 .exe 运行（比赛推荐）

1. 安装好 Npcap 驱动
2. 将 `dist/` 下的 `netlistener.exe` 和 `config.json` 复制到比赛机器的同一目录
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

## 排查问题

### .exe 运行后没有生成 cheat_log.csv

1. 检查与 .exe 同目录下是否有 `netlistener_error.log`
2. 如果有，查看错误原因（通常是 config.json 缺失或权限不足）
3. 确保 `config.json` 与 `netlistener.exe` 在同一目录
4. 确保以管理员权限运行

### 白名单域名仍被记录

1. 编辑 `config.json`，将 `"debug"` 设为 `true`
2. 运行程序，访问一个白名单域名
3. 查看 `dns_debug.log`，确认实际抓到的域名格式
4. 根据日志中的域名调整白名单

常见问题：
- 域名末尾有多余的 `.`（脚本已自动处理）
- 大小写不一致（脚本已自动转小写）
- 子域名未覆盖（白名单中的 `seucpc.com` 可匹配 `xxx.seucpc.com`）

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
Stop-Process -Name netlistener -Force -ErrorAction SilentlyContinue
Stop-Process -Name python*, pythonw* -Force -ErrorAction SilentlyContinue
```

或使用 CMD：

```cmd
taskkill /F /IM netlistener.exe
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
```

## 注意事项

- **必须以管理员权限运行**，否则无法嗅探网卡流量
- **必须安装 Npcap 驱动**，未安装会报错
- `.exe` 方式运行时，`config.json` 需放在与 .exe 同目录
- `cheat_log.csv` 为追加模式，多次运行的日志会合并在一起
- .exe 静默运行时如遇问题，请查看同目录下的 `netlistener_error.log`
