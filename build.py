# -*- coding: utf-8 -*-
"""一键构建脚本 - 将 launcher.py 打包为 netlistener.exe

使用方法：
    python build.py

前提条件：
    pip install pyinstaller scapy

打包选项：
    --onefile      打包为单个 .exe 文件
    --noconsole    无控制台窗口（静默运行）
    --uac-admin    双击时自动请求管理员权限（UAC 提示）
"""

import shutil
import subprocess
import sys
import os


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher = os.path.join(script_dir, "launcher.py")

    if not os.path.isfile(launcher):
        print("[错误] 找不到 launcher.py")
        sys.exit(1)

    print("[*] 开始编译 netlistener.exe ...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",            # 打包为单个 .exe
        "--noconsole",          # 无控制台窗口
        "--uac-admin",          # 双击自动请求管理员权限
        "--name", "netlistener",
        "--clean",
        # scapy 隐藏导入，防止打包遗漏
        "--hidden-import", "scapy.layers.inet",
        "--hidden-import", "scapy.layers.dns",
        "--hidden-import", "scapy.layers.l2",
        "--hidden-import", "scapy.modules",
        launcher,
    ]

    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        exe_path = os.path.join(script_dir, "dist", "netlistener.exe")
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"[+] 构建成功: {exe_path} ({size_mb:.1f} MB)")

        # 将 config.json 复制到 dist 目录，确保 .exe 能找到配置
        config_src = os.path.join(script_dir, "config.json")
        if os.path.isfile(config_src):
            shutil.copy2(config_src, os.path.join(script_dir, "dist", "config.json"))
            print("[+] config.json 已复制到 dist/ 目录")
        else:
            print("[警告] config.json 不存在，请手动复制到 dist/ 目录")

        print("[+] 双击即可运行（自动请求管理员权限，无终端窗口）")
    else:
        print("[错误] 构建失败，请检查 PyInstaller 输出。")
        sys.exit(1)


if __name__ == "__main__":
    main()
