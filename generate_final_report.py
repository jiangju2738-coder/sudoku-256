#!/usr/bin/env python3
"""
符闔數獨綜合可視化報告 - 最終版
整合所有分析結果，生成交互式HTML報告
"""

import json
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"


def generate_final_html_report():
    """生成最終HTML報告"""
    
    # 加載數據
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    known_digits = config.get("known_digits", [])
    
    with open(f"{BASE_DIR}/perm_overlap_analysis.json") as f:
        overlap_data = json.load(f)
    
    # 加載符闔排列
    perms = {}
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
    
    # 計算過濾統計
    filtering_stats = overlap_data.get("filtering_analysis", [])
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>符闔數獨深度研究報告 - 終極版</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e8e8e8;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        
        header {{
            text-align: center;
            color: #fff;
            margin-bottom: 40px;
            padding: 40px;
            background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(139,92,246,0.3));
            border-radius: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        header h1 {{
            font-size: 2.8em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ font-size: 1.3em; opacity: 0.9; margin-top: 10px; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            background: rgba(255,255,255,0.12);
        }}
        .stat-card .value {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-card .label {{ color: #a0a0a0; margin-top: 8px; }}
        .stat-card.alert .value {{ color: #ef4444; }}
        
        .section {{
            background: rgba(255,255,255,0.06);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{
            color: #8b5cf6;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid rgba(139,92,246,0.3);
            font-size: 1.8em;
        }}
        
        /* Sudoku Grid */
        .sudoku-container {{ text-align: center; }}
        .sudoku-grid {{
            display: inline-grid;
            grid-template-columns: repeat(16, 1fr);
            gap: 1px;
            background: #1a1a2e;
            padding: 4px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .cell {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: bold;
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .cell.known {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
        }}
        .cell.zero {{
            background: rgba(255,255,255,0.05);
            color: #666;
        }}
        .cell.row-conflict {{
            background: rgba(239,68,68,0.3);
            border: 2px solid #ef4444;
        }}
        .cell:hover {{ transform: scale(1.2); z-index: 10; }}
        
        /* Bar Chart */
        .bar-chart {{ margin: 20px 0; }}
        .bar-row {{
            display: flex;
            align-items: center;
            margin: 6px 0;
        }}
        .bar-label {{
            width: 80px;
            font-weight: bold;
            color: #d0d0d0;
        }}
        .bar-container {{
            flex: 1;
            height: 28px;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            overflow: hidden;
            margin-right: 15px;
        }}
        .bar {{
            height: 100%;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-weight: bold;
            font-size: 12px;
            transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .bar.fail {{ background: linear-gradient(90deg, #ef4444, #f97316); }}
        .bar.pass {{ background: linear-gradient(90deg, #10b981, #06b6d4); }}
        .bar-value {{ color: #a0a0a0; min-width: 60px; }}
        
        /* Alert Boxes */
        .alert {{
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            border-left: 4px solid;
        }}
        .alert-danger {{
            background: rgba(239,68,68,0.15);
            border-color: #ef4444;
            color: #fecaca;
        }}
        .alert-warning {{
            background: rgba(251,191,36,0.15);
            border-color: #fbbf24;
            color: #fef08a;
        }}
        .alert-success {{
            background: rgba(16,185,129,0.15);
            border-color: #10b981;
            color: #d1fae5;
        }}
        
        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background: rgba(139,92,246,0.2);
            color: #c4b5fd;
            font-weight: bold;
        }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        
        /* Conclusion Box */
        .conclusion-box {{
            background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(236,72,153,0.2));
            border-radius: 16px;
            padding: 30px;
            margin: 20px 0;
            border: 1px solid rgba(236,72,153,0.3);
        }}
        .conclusion-box h3 {{
            color: #f472b6;
            margin-bottom: 15px;
        }}
        .conclusion-box ul {{
            line-height: 2;
            padding-left: 30px;
        }}
        
        footer {{
            text-align: center;
            color: #888;
            padding: 30px;
            margin-top: 40px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .section {{ animation: fadeIn 0.6s ease; }}
        
        @media (max-width: 900px) {{
            .sudoku-grid {{ transform: scale(0.5); transform-origin: center; }}
            header h1 {{ font-size: 2em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎲 符闔數獨深度研究報告</h1>
            <div class="subtitle">16×16 三重約束系統 | 1,111,494個符闔排列 | DLX精確求解</div>
            <div style="margin-top: 15px; font-size: 0.95em; opacity: 0.8;">
                生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>
        
        <!-- Statistics Overview -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{len(known_digits)}</div>
                <div class="label">已知數字</div>
            </div>
            <div class="stat-card alert">
                <div class="value">0</div>
                <div class="label">DLX解數 ❌</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(known_digits)/256*100:.1f}%</div>
                <div class="label">填滿率</div>
            </div>
            <div class="stat-card">
                <div class="value">{sum(len(perms[r]) for r in range(1, 17)):,}</div>
                <div class="label">符闔排列總數</div>
            </div>
        </div>
        
        <!-- Critical Alert -->
        <div class="section">
            <h2>⚠️ 核心發現</h2>
            <div class="alert alert-danger">
                <strong>❌ 約束系統不可滿足！</strong>
                <p style="margin-top: 10px;">
                    15個行（A1-A15）的符闔排列被完全過濾至0，僅A16保留1,562個排列。
                    這表明92個已知數字與符闔排列存在根本性約束衝突。
                </p>
            </div>
        </div>
        
        <!-- Sudoku Grid -->
        <div class="section">
            <h2>📊 16×16 數獨謎題</h2>
            <div class="sudoku-container">
                <div class="sudoku-grid">
    '''
    
    # 生成網格
    grid_data = [[0]*16 for _ in range(16)]
    for k in known_digits:
        grid_data[k["row"]-1][k["col"]-1] = k["value"]
    
    # 標記衝突行
    conflict_rows = set()
    for stat in filtering_stats:
        if stat["valid"] == 0:
            conflict_rows.add(stat["row"])
    
    for r in range(16):
        for c in range(16):
            val = grid_data[r][c]
            is_known = val != 0
            is_conflict = (r+1) in conflict_rows
            
            cell_class = "cell"
            if is_known:
                cell_class += " known"
            else:
                cell_class += " zero"
            if is_conflict:
                cell_class += " row-conflict"
            
            html += f'<div class="{cell_class}" data-row="{r+1}" data-col="{c+1}">{val if is_known else ""}</div>'
    
    html += '''
                </div>
                <div style="margin-top: 15px; color: #888; font-size: 0.9em;">
                    <span style="display: inline-block; width: 16px; height: 16px; background: linear-gradient(135deg, #6366f1, #8b5cf6); margin-right: 5px; border-radius: 3px;"></span>已知數字
                    <span style="display: inline-block; width: 16px; height: 16px; background: rgba(239,68,68,0.3); border: 2px solid #ef4444; margin-left: 20px; margin-right: 5px; border-radius: 3px;"></span>約束衝突行
                    <span style="display: inline-block; width: 16px; height: 16px; background: rgba(255,255,255,0.05); margin-left: 20px; margin-right: 5px; border-radius: 3px;"></span>空白單元格
                </div>
            </div>
        </div>
        
        <!-- Filtering Analysis -->
        <div class="section">
            <h2>📈 符闔排列過濾分析</h2>
            <div class="bar-chart">
    '''
    
    # 生成過濾條形圖
    max_total = max(s["total"] for s in filtering_stats) if filtering_stats else 1
    
    for stat in filtering_stats:
        width_pct = stat["valid"] / max(stat["total"], 1) * 100
        bar_class = "fail" if stat["valid"] == 0 else "pass"
        
        html += f'''
                <div class="bar-row">
                    <div class="bar-label">行{stat["row"]:2d}</div>
                    <div class="bar-container">
                        <div class="bar {bar_class}" style="width: {width_pct}%">
                            {stat["valid"] if stat["valid"] > 0 else '0'}
                        </div>
                    </div>
                    <div class="bar-value">{stat["valid"]:,}/{stat["total"]:,}</div>
                </div>
                '''
    
    html += f'''
            </div>
            <div style="text-align: center; margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                <strong>過濾統計:</strong> 原始 {sum(s["total"] for s in filtering_stats):,} → 有效 {sum(s["valid"] for s in filtering_stats):,} 
                | 過濾比例 {(sum(s["total"] for s in filtering_stats) - sum(s["valid"] for s in filtering_stats)) / sum(s["total"] for s in filtering_stats) * 100:.2f}%
            </div>
        </div>
        
        <!-- Overlap Analysis -->
        <div class="section">
            <h2>🎯 跨行重疊分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>指標</th>
                        <th>數值</th>
                        <th>說明</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>有效排列總數</td>
                        <td style="font-weight: bold;">1,562</td>
                        <td>僅A16行的排列</td>
                    </tr>
                    <tr>
                        <td>唯一行排列</td>
                        <td>1,562</td>
                        <td>每個排列只出現在一行</td>
                    </tr>
                    <tr>
                        <td>跨行重疊排列</td>
                        <td style="color: #10b981; font-weight: bold;">0</td>
                        <td>無跨行重複</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Deep Conclusion -->
        <div class="section">
            <h2>💡 深度研究結論</h2>
            
            <div class="conclusion-box">
                <h3>🔍 核心發現</h3>
                <ul>
                    <li><strong>約束衝突根源:</strong> 92個已知數字（35.9%填滿率）造成過度約束</li>
                    <li><strong>排列壓縮:</strong> 15個行的排列選擇空間被壓縮至零</li>
                    <li><strong>單源值鎖定:</strong> 列AllDifferent約束與符闔排列約束產生全局衝突</li>
                    <li><strong>不可滿足性:</strong> DLX精確求解確認0解</li>
                </ul>
            </div>
            
            <div class="alert alert-warning" style="margin-top: 20px;">
                <strong>💡 優化建議:</strong>
                <ul style="margin-top: 10px; line-height: 1.8; padding-left: 20px;">
                    <li>將已知數字減少至40-60個（15-23%填滿率）</li>
                    <li>重新設計符闔排列集，確保全局約束相容</li>
                    <li>實施MIS（不可滿足子集）提取定位衝突根源</li>
                    <li>使用CP-SAT進行可行性預檢</li>
                </ul>
            </div>
            
            <div style="margin-top: 25px;">
                <h3 style="color: #8b5cf6; margin-bottom: 15px;">🚀 研究方向</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;">
                    <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                        <h4 style="color: #6366f1; margin-bottom: 10px;">符闔排列理論</h4>
                        <ul style="line-height: 1.8; padding-left: 20px; font-size: 0.9em;">
                            <li>約束相容的排列生成算法</li>
                            <li>排列集密度最優研究</li>
                            <li>單源值分布均衡性</li>
                        </ul>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                        <h4 style="color: #6366f1; margin-bottom: 10px;">求解算法優化</h4>
                        <ul style="line-height: 1.8; padding-left: 20px; font-size: 0.9em;">
                            <li>DLX+CP-SAT混合策略</li>
                            <li>增量約束求解</li>
                            <li>多解空間采样</li>
                        </ul>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                        <h4 style="color: #6366f1; margin-bottom: 10px;">博弈分析</h4>
                        <ul style="line-height: 1.8; padding-left: 20px; font-size: 0.9em;">
                            <li>零和博弈解存在性</li>
                            <li>玩家策略最優響應</li>
                            <li>相變曲線研究</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p style="font-size: 1.1em; margin-bottom: 10px;">🎲 符闔數獨深度研究系統 V3.0</p>
            <p style="opacity: 0.7;">由DLX精確覆蓋算法 | CP-SAT約束規劃 | 符闔排列理論驅動</p>
            <p style="opacity: 0.5; font-size: 0.85em; margin-top: 10px;">
                工作目錄: D:/2026/WPF_Sudoku/Sudoku_256 | 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </footer>
    </div>
    
    <script>
        document.querySelectorAll('.cell').forEach(cell => {{
            cell.addEventListener('click', function() {{
                const row = this.dataset.row;
                const col = this.dataset.col;
                const val = this.textContent || '空白';
                const isConflict = this.classList.contains('row-conflict');
                alert(`位置: 第${{row}}行第${{col}}列\\n值: ${{val}}${{isConflict ? '\\n⚠️ 該行約束衝突' : ''}}`);
            }});
        }});
        
        window.addEventListener('load', function() {{
            document.querySelectorAll('.bar').forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => {{ bar.style.width = width; }}, 200);
            }});
        }});
    </script>
</body>
</html>
'''
    
    output_path = f"{BASE_DIR}/符闔數獨_終極研究報告.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 終極可視化報告已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_final_html_report()
