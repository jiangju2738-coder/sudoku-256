#!/usr/bin/env python3
"""
安装依赖并启动符闔數獨配置器后端
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装必要的 Python 包"""
    print("=" * 60)
    print("安装 Python 依赖")
    print("=" * 60)
    
    packages = ['flask', 'flask-cors', 'ortools']
    
    for pkg in packages:
        print(f"安装 {pkg}...", end=" ")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', pkg, '-q'],
                check=True
            )
            print("✓ 完成")
        except subprocess.CalledProcessError:
            print("✗ 失败")
            return False
    
    print("\n所有依赖安装完成！")
    return True

def check_permissions():
    """检查符闔排列文件"""
    print("\n" + "=" * 60)
    print("检查符闔排列文件")
    print("=" * 60)
    
    work_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"
    
    all_ok = True
    for row in range(1, 17):
        filename = f"A{row}_permutations.json"
        filepath = os.path.join(work_dir, filename)
        if os.path.exists(filepath):
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                perms = json.load(f)
            print(f"  A{row}: {len(perms):,} 排列 ✓")
        else:
            print(f"  A{row}: 文件缺失 ✗")
            all_ok = False
    
    return all_ok

def main():
    print("\n" + "=" * 60)
    print("   符闔數獨配置器 - 环境初始化")
    print("=" * 60 + "\n")
    
    # 步骤 1: 安装依赖
    if not install_dependencies():
        print("\n⚠ 依赖安装失败，请手动运行:")
        print("   pip install flask flask-cors ortools")
        return
    
    # 步骤 2: 检查文件
    if not check_permissions():
        print("\n⚠ 部分符闔排列文件缺失，求解功能可能受限")
        continue_anyway = input("是否继续启动？(y/n): ").strip().lower()
        if continue_anyway != 'y':
            return
    
    # 步骤 3: 启动服务
    print("\n" + "=" * 60)
    print("启动后端服务")
    print("=" * 60)
    print("\n前端页面: http://127.0.0.1:5001")
    print("API 端点: http://127.0.0.1:5001/api")
    print("\n按 Ctrl+C 停止服务\n")
    
    # 切换到工作目录
    work_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"
    os.chdir(work_dir)
    
    # 启动 Flask 服务
    subprocess.run([sys.executable, 'backend_api.py'])

if __name__ == '__main__':
    main()
