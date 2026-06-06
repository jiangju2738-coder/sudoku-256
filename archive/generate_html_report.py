#!/usr/bin/env python3
"""
符闔數獨可視化研究報告 - HTML版本
生成交互式16×16數獨可視化、約束強度條形圖、排列重疊分析
"""

import json
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"


def generate_html_report():
    """生成HTML可視化報告"""
    
    # 加載數據
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    
    known_digits = config.get("known_digits", [])
    
    # 加載符闔排列
    perms = {}
    total_perms = 0
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
        total_perms += len(perms[r])
    
    # 計算約束強度
    row_counts = [0] * 16
    col_counts = [0] * 16
    box_counts = [0] * 16
    
    for k in known_digits:
        row_counts[k["row"]-1] += 1
        col_counts[k["col"]-1] += 1
        box_counts[(k["row"]-1)//4 * 4 + (k["col"]-1)//4] += 1
    
    # 檢查衝突
    conflicts = []
    row_vals = [set() for _ in range(16)]
    col_vals = [set() for _ in range(16)]
    box_vals = [set() for _ in range(16)]
    
    for k in known_digits:
        r, c, v = k["row"]-1, k["col"]-1, k["value"]
        row_vals[r].add(v)
        col_vals[c].add(v)
        box_vals[(r//4)*4 + (c//4)].add(v)
    
    for r in range(16):
        if len(row_vals[r]) != row_counts[r]:
            conflicts.append(f"行{r+1}有重複值")
    for c in range(16):
        if len(col_vals[c]) != col_counts[c]:
            conflicts.append(f"列{c+1}有重複值")
    for b in range(16):
        if len(box_vals[b]) != box_counts[b]:
            conflicts.append(f"宮{b+1}有重複值")
    
    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>符闔數獨深度研究報告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card .value {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stat-card .label {{
            color: #666;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .section {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        /* Sudoku Grid Styles */
        .sudoku-grid {{
            display: grid;
            grid-template-columns: repeat(16, 1fr);
            gap: 2px;
            max-width: 600px;
            margin: 20px auto;
            background: #333;
            padding: 3px;
            border-radius: 10px;
        }}
        
        .cell {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: bold;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.2s ease;
            border-radius: 2px;
        }}
        
        .cell:hover {{
            background: #667eea;
            color: white;
            transform: scale(1.1);
        }}
        
        .cell.known {{
            background: #667eea;
            color: white;
        }}
        
        .cell.zero {{
            color: #ccc;
        }}
        
        /* Box boundaries */
        .cell:nth-child(4n) {{
            border-right: 3px solid #333;
        }}
        
        .cell:nth-child(16n) {{
            border-right: none;
        }}
        
        .sudoku-grid .cell:nth-child(n+65):nth-child(-n+80),
        .sudoku-grid .cell:nth-child(n+113):nth-child(-n+128) {{
            border-bottom: 3px solid #333;
        }}
        
        /* Bar Chart Styles */
        .bar-chart {{
            margin: 20px 0;
        }}
        
        .bar-row {{
            display: flex;
            align-items: center;
            margin: 8px 0;
        }}
        
        .bar-label {{
            width: 60px;
            font-weight: bold;
            color: #333;
        }}
        
        .bar-container {{
            flex: 1;
            height: 25px;
            background: #eee;
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }}
        
        .bar {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-weight: bold;
            font-size: 12px;
            transition: width 1s ease;
        }}
        
        .bar-value {{
            margin-left: 10px;
            color: #666;
        }}
        
        /* Conflict Alert */
        .alert {{
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .alert-success {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            color: #155724;
        }}
        
        .alert-warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }}
        
        .alert-danger {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }}
        
        /* Table Styles */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #667eea;
            color: white;
        }}
        
        tr:hover {{
            background: #f5f5f5;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            color: white;
            padding: 30px;
            margin-top: 40px;
            opacity: 0.9;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .section {{
            animation: fadeIn 0.6s ease;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .sudoku-grid {{
                transform: scale(0.6);
                transform-origin: center;
            }}
            
            header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎲 符闔數獨深度研究報告</h1>
            <div class="subtitle">16×16 三重約束系統 | 1,111,494個符闔排列 | DLX精確求解</div>
            <div style="margin-top: 15px; font-size: 0.9em;">
                生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>
        
        <!-- Statistics Overview -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{len(known_digits)}</div>
                <div class="label">已知數字</div>
            </div>
            <div class="stat-card">
                <div class="value">{256 - len(known_digits)}</div>
                <div class="label">空白單元格</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(known_digits)/256*100:.1f}%</div>
                <div class="label">填滿率</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_perms:,}</div>
                <div class="label">符闔排列總數</div>
            </div>
        </div>
        
        <!-- Conflict Status -->
        <div class="section">
            <h2>🔍 約束衝突檢測</h2>
            {f'<div class="alert alert-success">✅ 三重約束（行/列/宮）無內部衝突</div>' if not conflicts else f'<div class="alert alert-danger">❌ 發現約束衝突: {", ".join(conflicts)}</div>'}
        </div>
        
        <!-- Sudoku Grid Visualization -->
        <div class="section">
            <h2>📊 16×16 數獨謎題</h2>
            <div class="sudoku-grid" id="sudokuGrid">
                '''
    
    # 生成網格
    grid_data = [[0]*16 for _ in range(16)]
    for k in known_digits:
        grid_data[k["row"]-1][k["col"]-1] = k["value"]
    
    for r in range(16):
        for c in range(16):
            val = grid_data[r][c]
            is_known = val != 0
            cell_class = "cell"
            if is_known:
                cell_class += " known"
            else:
                cell_class += " zero"
            
            html += f'<div class="{cell_class}" data-row="{r+1}" data-col="{c+1}">{val if is_known else ""}</div>'
    
    html += '''
            </div>
            <div style="text-align: center; margin-top: 15px; color: #666;">
                <span style="display: inline-block; width: 20px; height: 20px; background: #667eea; margin-right: 5px;"></span>已知數字
                <span style="display: inline-block; width: 20px; height: 20px; background: #f8f9fa; margin-left: 20px; margin-right: 5px;"></span>空白單元格
            </div>
        </div>
        
        <!-- Row Constraint Strength -->
        <div class="section">
            <h2>📈 行約束強度分佈</h2>
            <div class="bar-chart">
                '''
    
    max_row = max(row_counts) if row_counts else 1
    for r in range(16):
        width_pct = row_counts[r] / max(max_row, 1) * 100
        html += f'''
                <div class="bar-row">
                    <div class="bar-label">行{r+1:2d}</div>
                    <div class="bar-container">
                        <div class="bar" style="width: {width_pct}%">{row_counts[r]}</div>
                    </div>
                    <div class="bar-value">{row_counts[r]}個已知</div>
                </div>
                '''
    
    html += '''
            </div>
        </div>
        
        <!-- Column Constraint Strength -->
        <div class="section">
            <h2>📈 列約束強度分佈</h2>
            <div class="bar-chart">
                '''
    
    max_col = max(col_counts) if col_counts else 1
    for c in range(16):
        width_pct = col_counts[c] / max(max_col, 1) * 100
        html += f'''
                <div class="bar-row">
                    <div class="bar-label">列{c+1:2d}</div>
                    <div class="bar-container">
                        <div class="bar" style="width: {width_pct}%">{col_counts[c]}</div>
                    </div>
                    <div class="bar-value">{col_counts[c]}個已知</div>
                </div>
                '''
    
    html += '''
            </div>
        </div>
        
        <!-- Box Constraint Strength -->
        <div class="section">
            <h2>📈 宮格約束強度分佈</h2>
            <div class="bar-chart">
                '''
    
    max_box = max(box_counts) if box_counts else 1
    for b in range(16):
        width_pct = box_counts[b] / max(max_box, 1) * 100
        html += f'''
                <div class="bar-row">
                    <div class="bar-label">宮{b+1:2d}</div>
                    <div class="bar-container">
                        <div class="bar" style="width: {width_pct}%">{box_counts[b]}</div>
                    </div>
                    <div class="bar-value">{box_counts[b]}個已知</div>
                </div>
                '''
    
    html += '''
            </div>
        </div>
        
        <!-- Fuhe Permutations Analysis -->
        <div class="section">
            <h2>🎯 符闔排列分佈分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>行號</th>
                        <th>排列數量</th>
                        <th>占比</th>
                        <th>約束強度</th>
                    </tr>
                </thead>
                <tbody>
                    '''
    
    total = sum(len(perms[r]) for r in range(1, 17))
    for r in range(1, 17):
        count = len(perms[r])
        pct = count / total * 100
        strength = "緊" if count < 1000 else "中" if count < 100000 else "鬆"
        html += f'''
                    <tr>
                        <td>行{r:2d}</td>
                        <td>{count:,}</td>
                        <td>{pct:.2f}%</td>
                        <td>{strength}</td>
                    </tr>
                    '''
    
    html += f'''
                </tbody>
            </table>
        </div>
        
        <!-- Deep Analysis Conclusion -->
        <div class="section">
            <h2>💡 深度研究結論</h2>
            
            <div class="alert alert-warning">
                <strong>⚠️ 關鍵發現:</strong> 當前92個已知數字的實例可能存在約束衝突
            </div>
            
            <h3 style="margin: 20px 0 15px; color: #667eea;">分析要點:</h3>
            <ul style="line-height: 2; padding-left: 30px;">
                <li><strong>約束密度:</strong> 35.9%的填滿率在16×16數獨中屬於高密度</li>
                <li><strong>符闔約束:</strong> 1,111,494個排列需與92個已知數字相容</li>
                <li><strong>列約束:</strong> 每列16個值需來自16個不同行</li>
                <li><strong>潛在衝突:</strong> 單源值鎖定鏈可能導致全局不可滿足</li>
            </ul>
            
            <h3 style="margin: 20px 0 15px; color: #667eea;">優化建議:</h3>
            <ul style="line-height: 2; padding-left: 30px;">
                <li>建議將已知數字減少至40-60個（15-23%填滿率）</li>
                <li>重新設計符闔排列集，確保全局約束相容</li>
                <li>實施約束衝突根源分析（MIS提取）</li>
                <li>使用DLX精確計數验证解的存在性</li>
            </ul>
            
            <h3 style="margin: 20px 0 15px; color: #667eea;">研究方向:</h3>
            <ul style="line-height: 2; padding-left: 30px;">
                <li>符闔排列生成算法（約束相容）</li>
                <li>多解空間分析與相變曲線</li>
                <li>博弈均衡分析（零和博弈下的解存在性）</li>
                <li>約束衝突自動識別與修復</li>
            </ul>
        </div>
        
        <footer>
            <p>🎲 符闔數獨深度研究系統 V3.0</p>
            <p>由DLX精確覆蓋算法 | CP-SAT約束規劃 | 符闔排列理論驅動</p>
            <p style="margin-top: 10px; font-size: 0.8em;">
                工作目錄: D:/2026/WPF_Sudoku/Sudoku_256
            </p>
        </footer>
    </div>
    
    <script>
        // Add interactivity
        document.querySelectorAll('.cell').forEach(cell => {{
            cell.addEventListener('click', function() {{
                const row = this.dataset.row;
                const col = this.dataset.col;
                const val = this.textContent;
                alert(`位置: 第${{row}}行第${{col}}列\\n值: ${{val || '空白'}}`);
            }});
        }});
        
        // Animate bars on load
        window.addEventListener('load', function() {{
            document.querySelectorAll('.bar').forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 100);
            }});
        }});
    </script>
</body>
</html>
'''
    
    # 保存HTML
    output_path = f"{BASE_DIR}/超級大數獨_可視化報告.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ HTML可視化報告已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_html_report()
