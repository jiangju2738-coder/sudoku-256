#!/usr/bin/env python3
"""
SAT 求解器環境檢查與安裝方案
檢查 sharpSAT, Cachet, Kissat, Glucose, MiniSat 等求解器可用性
"""

import subprocess
import os
import sys

# SAT 求解器檢查清單
SAT_SOLVERS = {
    'sharpSAT': {
        'cmd': ['sharpSAT', '--version'],
        'download': 'https://github.com/marcthurley/sharpSAT/releases',
        'purpose': '精確計數 (#SAT)'
    },
    'Cachet': {
        'cmd': ['cachet', '--version'],
        'download': 'https://github.com/MeelGroup/Cachet',
        'purpose': '精確計數 (#SAT)'
    },
    'Kissat': {
        'cmd': ['kissat', '--version'],
        'download': 'https://sat.inesc-id.pt/~mkissat/',
        'purpose': '單解驗證 (SAT)'
    },
    'glucose': {
        'cmd': ['glucose', '--version'],
        'download': 'https://www.labri.fr/perso/lsimon/glucose/',
        'purpose': '單解驗證 (SAT)'
    },
    'minisat': {
        'cmd': ['minisat', '--version'],
        'download': 'https://github.com/niklasso/minisat',
        'purpose': '單解驗證 (SAT)'
    },
    'c2d': {
        'cmd': ['c2d', '--version'],
        'download': 'https://reasoning.cs.ucla.edu/c2d/',
        'purpose': 'd-DNNF 編譯 (計數)'
    },
    'GANAK': {
        'cmd': ['ganak', '--version'],
        'download': 'https://github.com/meelgroup/GANAK',
        'purpose': '近似計數 (#SAT)'
    }
}

def check_solver(name: str, info: dict) -> dict:
    """檢查求解器是否可用"""
    try:
        result = subprocess.run(
            info['cmd'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            'installed': True,
            'output': result.stdout[:500] if result.stdout else result.stderr[:500],
            'version': result.stdout[:100].strip() if result.stdout else 'unknown'
        }
    except FileNotFoundError:
        return {
            'installed': False,
            'output': None,
            'download': info['download'],
            'purpose': info['purpose']
        }
    except Exception as e:
        return {
            'installed': False,
            'error': str(e),
            'download': info['download'],
            'purpose': info['purpose']
        }

def main():
    print("="*70)
    print("SAT 求解器環境檢查")
    print("="*70)
    
    results = {}
    for name, info in SAT_SOLVERS.items():
        print(f"\n檢查 {name} ({info['purpose']}):")
        result = check_solver(name, info)
        results[name] = result
        
        if result['installed']:
            print(f"  ✅ 已安裝 - 版本: {result.get('version', 'unknown')}")
        else:
            print(f"  ❌ 未安裝")
            print(f"     下載地址: {result.get('download', 'N/A')}")
    
    print("\n" + "="*70)
    print("環境狀態總結")
    print("="*70)
    
    installed = [n for n, r in results.items() if r['installed']]
    not_installed = [n for n, r in results.items() if not r['installed']]
    
    print(f"\n已安裝 ({len(installed)}): {', '.join(installed) if installed else '無'}")
    print(f"未安裝 ({len(not_installed)}): {', '.join(not_installed)}")
    
    # 推薦安裝方案
    print("\n" + "="*70)
    print("推薦安裝方案")
    print("="*70)
    
    print("\n【方案 1】安裝 sharpSAT (推薦用於精確計數)")
    print("sharpSAT 是目前效率最高的 #SAT 求解器，適用於大型結構化問題。")
    print("  下載: https://github.com/marcthurley/sharpSAT")
    print("  使用: ./sharpSAT sudoku_dimacs.cnf")
    print("  輸出: 精確解數量")
    
    print("\n【方案 2】使用 OR-Tools CP-SAT (已可用)")
    print("CP-SAT 已安裝，可通過 Solution Pool 進行完整枚舉。")
    print("  使用: python sat_counter.py")
    print("  優點: 無需額外安裝，Python 直接調用")
    print("  限制: 對於超大型問題可能比專用的 #SAT 求解器慢")
    
    print("\n【方案 3】安裝 Kissat + Kissat Count")
    print("Kissat 是 2020 SAT 競賽冠軍，性能優異。")
    print("  下載: https://sat.inesc-id.pt/~mkissat/")
    print("  使用: ./kissat sudoku_dimacs.cnf")
    
    # 輸出到文件
    report_path = os.path.join(os.path.dirname(__file__), "sat_solver_check_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("SAT 求解器環境檢查報告\n")
        f.write("="*70 + "\n\n")
        
        for name, result in results.items():
            status = "✅ 已安裝" if result['installed'] else "❌ 未安裝"
            f.write(f"{name}: {status}\n")
            if result['installed']:
                f.write(f"  版本: {result.get('version', 'unknown')}\n")
            else:
                f.write(f"  下載: {result.get('download', 'N/A')}\n")
            f.write("\n")
        
        f.write("\n推薦方案:\n")
        f.write("1. sharpSAT - 精確計數 (#SAT)\n")
        f.write("2. CP-SAT - 已安裝，可直接使用\n")
        f.write("3. Kissat - 單解驗證與計數\n")
    
    print(f"\n檢查報告已保存至: {report_path}")
    return results


if __name__ == "__main__":
    main()
