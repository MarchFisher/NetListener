' -----------------------------------------------------------
' 静默启动器 — 以管理员权限运行 dns_monitor.py，无终端窗口
' 使用方式：右键 -> 以管理员身份运行
' -----------------------------------------------------------

Dim objShell
Set objShell = CreateObject("Shell.Application")

' 获取脚本所在目录
Dim scriptDir
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Python 脚本路径
Dim pyScript
pyScript = scriptDir & "\dns_monitor.py"

' 以管理员权限静默运行 python.exe
' 0 = 隐藏窗口, True = 等待完成
objShell.ShellExecute "python", Chr(34) & pyScript & Chr(34), scriptDir, "runas", 0

Set objShell = Nothing
