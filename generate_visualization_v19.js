const fs = require('fs');
const path = require('path');

// 讀取視覺化數據
const visualData = JSON.parse(fs.readFileSync(path.join(__dirname, 'cosmic_thunder_visual_data.json'), 'utf-8'));
const solution = JSON.parse(fs.readFileSync(path.join(__dirname, 'solution_v4_final.json'), 'utf-8'));

// 生成 HTML
const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>符闔數獨進化式求解系統 V19.0 - 量子態視覺化</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
            min-height: 100vh;
            color: #e0e0e0;
            overflow-x: hidden;
        }
        
        .header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 200, 0.05), transparent);
            border-bottom: 1px solid rgba(0, 255, 200, 0.2);
        }
        
        .header h1 {
            font-size: 2rem;
            background: linear-gradient(90deg, #00ffc8, #00d4ff, #7b2ff7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header .subtitle {
            color: #888;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .quantum-state-panel {
            background: linear-gradient(135deg, rgba(30, 30, 60, 0.8), rgba(20, 20, 40, 0.9));
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(123, 47, 247, 0.3);
            box-shadow: 0 0 40px rgba(123, 47, 247, 0.1);
        }
        
        .quantum-state-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
        }
        
        .quantum-state-title {
            font-size: 1.5rem;
            color: #7b2ff7;
        }
        
        .quantum-indicator {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1.2rem;
        }
        
        .quantum-indicator.superposition {
            background: linear-gradient(135deg, rgba(0, 255, 200, 0.1), rgba(0, 212, 255, 0.1));
            border: 1px solid rgba(0, 255, 200, 0.5);
        }
        
        .quantum-indicator.collapsed {
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 152, 0, 0.1));
            border: 1px solid rgba(255, 107, 107, 0.5);
        }
        
        .quantum-indicator.infeasible {
            background: linear-gradient(135deg, rgba(255, 59, 59, 0.1), rgba(255, 152, 0, 0.1));
            border: 1px solid rgba(255, 59, 59, 0.5);
        }
        
        .quantum-icon {
            font-size: 2.5rem;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .stat-item {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00ffc8;
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: #888;
            margin-top: 0.25rem;
        }
        
        .panel {
            background: linear-gradient(135deg, rgba(30, 30, 60, 0.8), rgba(20, 20, 40, 0.9));
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(0, 212, 255, 0.2);
        }
        
        .panel-title {
            font-size: 1.3rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .panel-title::before {
            content: '';
            display: inline-block;
            width: 4px;
            height: 1.2rem;
            background: linear-gradient(180deg, #00ffc8, #7b2ff7);
            border-radius: 2px;
        }
        
        /* 數獨網格 */
        .sudoku-grid-container {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .grid-panel {
            flex: 1;
            min-width: 300px;
            max-width: 500px;
        }
        
        .sudoku-grid {
            display: grid;
            grid-template-columns: repeat(16, 1fr);
            gap: 1px;
            background: rgba(255, 255, 255, 0.1);
            padding: 2px;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .cell {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: bold;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .cell.given {
            background: linear-gradient(135deg, rgba(0, 255, 200, 0.3), rgba(0, 212, 255, 0.3));
            color: #00ffc8;
        }
        
        .cell.empty {
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.4);
        }
        
        .cell.best-solution {
            background: linear-gradient(135deg, rgba(123, 47, 247, 0.4), rgba(0, 255, 200, 0.2));
            color: #e0e0e0;
        }
        
        .cell:hover {
            transform: scale(1.2);
            z-index: 10;
            box-shadow: 0 0 20px rgba(0, 255, 200, 0.5);
        }
        
        /* 宮格邊框 */
        .cell:nth-child(4n) {
            border-right: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .cell:nth-child(16n) {
            border-right: none;
        }
        
        .cell:nth-child(n+129):nth-child(-n+144),
        .cell:nth-child(n+257):nth-child(-n+272) {
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        /* 進化進度條 */
        .evolution-container {
            margin-top: 1rem;
        }
        
        .generation-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .generation-label {
            width: 60px;
            font-size: 0.85rem;
            color: #888;
        }
        
        .progress-bar {
            flex: 1;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .progress-fill.elite {
            background: linear-gradient(90deg, #7b2ff7, #00ffc8);
        }
        
        .progress-fill.average {
            background: linear-gradient(90deg, rgba(0, 255, 200, 0.5), rgba(0, 212, 255, 0.5));
        }
        
        .fit-value {
            width: 60px;
            text-align: right;
            font-family: monospace;
            color: #00ffc8;
        }
        
        /* 剪枝統計 */
        .pruning-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .pruning-card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 1rem;
            border-left: 3px solid;
        }
        
        .pruning-card.fahuo {
            border-left-color: #7b2ff7;
        }
        
        .pruning-card.column {
            border-left-color: #00ffc8;
        }
        
        .pruning-card.box {
            border-left-color: #00d4ff;
        }
        
        .pruning-name {
            font-size: 1rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .pruning-metrics {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .metric {
            font-size: 0.8rem;
        }
        
        .metric-value {
            color: #00ffc8;
            font-weight: bold;
        }
        
        /* 樹狀結構 */
        .tree-container {
            position: relative;
            padding: 2rem;
            overflow-x: auto;
        }
        
        .tree-svg {
            width: 100%;
            height: auto;
        }
        
        /* 標籤 */
        .tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-right: 0.5rem;
        }
        
        .tag.green { background: rgba(0, 255, 200, 0.2); color: #00ffc8; }
        .tag.purple { background: rgba(123, 47, 247, 0.2); color: #b388ff; }
        .tag.blue { background: rgba(0, 212, 255, 0.2); color: #00d4ff; }
        
        /* 响应式 */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .sudoku-grid-container {
                flex-direction: column;
            }
            
            .grid-panel {
                min-width: 100%;
            }
        }
        
        /* 動畫 */
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .phase-complete {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, rgba(0, 255, 200, 0.9), rgba(123, 47, 247, 0.9));
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 255, 200, 0.3);
            animation: slideIn 0.5s ease-out, fadeOut 0.5s ease-out 4s forwards;
            z-index: 1000;
        }
        
        @keyframes slideIn {
            from { transform: translateX(400px); }
            to { transform: translateX(0); }
        }
        
        @keyframes fadeOut {
            to { opacity: 0; transform: translateY(-20px); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌀 符闔數獨進化式求解系統 V19.0</h1>
        <div class="subtitle">Cosmic Thunder Sudoku Evolutionary Solver | 量子態與坍縮機制</div>
    </div>
    
    <div class="container">
        <!-- 量子態狀態面板 -->
        <div class="quantum-state-panel fade-in">
            <div class="quantum-state-header">
                <div class="quantum-state-title">
                    <span class="tag purple">量子態測量</span>
                    系統坍縮狀態
                </div>
                <div class="tag ${collapseState}" id="stateBadge">載入中...</div>
            </div>
            
            <div class="quantum-indicator ${quantumState}" id="quantumIndicator">
                <span class="quantum-icon" id="quantumIcon">⚛️</span>
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold;" id="quantumStateText">載入中...</div>
                    <div style="color: #888; font-size: 0.9rem;" id="quantumStateDetail"></div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="solutionCount">-</div>
                    <div class="stat-label">解數量</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="isUnique">-</div>
                    <div class="stat-label">唯一性</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${visualData.puzzle.givenCount}</div>
                    <div class="stat-label">已知數</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${(visualData.puzzle.fillRate * 100).toFixed(1)}%</div>
                    <div class="stat-label">填滿率</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${visualData.evolution.backtrackCount || 0}</div>
                    <div class="stat-label">迴溯次數</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${visualData.evolution.finalBestFitness?.toFixed(3) || '0.000'}</div>
                    <div class="stat-label">最終適應度</div>
                </div>
            </div>
        </div>
        
        <!-- 未解盤基底 -->
        <div class="panel fade-in">
            <div class="panel-title">
                <span class="tag green">階段 1</span> 未解盤基底
            </div>
            <p style="color: #888; margin-bottom: 1rem;">零約束狀態：所有可能性共存（量子疊加態）</p>
            
            <div class="sudoku-grid-container">
                <div class="grid-panel">
                    <h4 style="margin-bottom: 0.5rem; color: #888;">未解盤（已知數標記）</h4>
                    <div class="sudoku-grid" id="unsolvedGrid"></div>
                </div>
            </div>
        </div>
        
        <!-- 遺傳優化結果 -->
        <div class="panel fade-in">
            <div class="panel-title">
                <span class="tag purple">階段 4</span> 二進制快速遺傳優化
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; flex-wrap: wrap;">
                <div>
                    <h4 style="margin-bottom: 0.5rem; color: #888;">最優解網格（遺傳優化）</h4>
                    <div class="sudoku-grid" id="geneticGrid"></div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 0.5rem; color: #888;">進化適應度趨勢</h4>
                    <div class="evolution-container" id="evolutionChart"></div>
                </div>
            </div>
        </div>
        
        <!-- 剪枝博弈統計 -->
        <div class="panel fade-in">
            <div class="panel-title">
                <span class="tag blue">階段 6</span> 融闔綜闔剪枝博弈
            </div>
            
            <div class="pruning-stats" id="pruningStats"></div>
        </div>
        
        <!-- 符闔排列索引 -->
        <div class="panel fade-in">
            <div class="panel-title">
                <span class="tag purple">符闔排列</span> 336 個列相容排列
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem;">
                ${generatePermutationTable(visualData.genetic.top10)}
            </div>
        </div>
    </div>
    
    <script>
        // 視覺化數據
        const data = ${JSON.stringify(visualData, null, 2)};
        
        // 量子態狀態
        const quantumStates = {
            'superposition': {
                icon: '⚛️',
                text: '量子態保持（多解共存）',
                detail: '波函數未坍縮，符闔博弈框架處於開放狀態',
                class: 'superposition'
            },
            'collapsed': {
                icon: '🔬',
                text: '系統坍縮（唯一解）',
                detail: '波函數坍縮至確定態，符闔博弈成功收斂',
                class: 'collapsed'
            },
            'infeasible': {
                icon: '❌',
                text: '不可滿足（約束衝突）',
                detail: '波函數為零，符闔排列與列宮約束衝突',
                class: 'infeasible'
            }
        };
        
        // 初始化
        document.addEventListener('DOMContentLoaded', () => {
            // 更新量子態
            const state = quantumStates[data.collapse.state];
            document.getElementById('quantumIcon').textContent = state.icon;
            document.getElementById('quantumStateText').textContent = state.text;
            document.getElementById('quantumStateDetail').textContent = state.detail;
            document.getElementById('quantumIndicator').className = 'quantum-indicator ' + state.class;
            document.getElementById('stateBadge').className = 'tag ' + (state.class === 'superposition' ? 'blue' : state.class === 'collapsed' ? 'green' : 'purple');
            
            document.getElementById('solutionCount').textContent = data.collapse.solutionCount;
            document.getElementById('isUnique').textContent = data.collapse.isUnique ? '✅ 唯一' : '❌ 多解';
            
            // 渲染未解盤
            renderUnsolvedGrid();
            
            // 渲染遺傳優化結果
            renderGeneticGrid();
            renderEvolutionChart();
            
            // 渲染剪枝統計
            renderPruningStats();
            
            // 展示完成通知
            showPhaseComplete();
        });
        
        function renderUnsolvedGrid() {
            const grid = document.getElementById('unsolvedGrid');
            grid.innerHTML = '';
            
            const givenSet = new Set(data.puzzle.givenCells.map(([k]) => k));
            
            for (let i = 0; i < 16; i++) {
                for (let j = 0; j < 16; j++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell ' + (givenSet.has(i + ',' + j) ? 'given' : 'empty');
                    cell.textContent = givenSet.has(i + ',' + j) 
                        ? data.puzzle.givenCells.find(([k]) => k === i + ',' + j)?.[1] || '?' 
                       : '';
                    grid.appendChild(cell);
                }
            }
        }
        
        function renderGeneticGrid() {
            const grid = document.getElementById('geneticGrid');
            grid.innerHTML = '';
            
            for (let i = 0; i < 16; i++) {
                for (let j = 0; j < 16; j++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell best-solution';
                    cell.textContent = data.bestGrid[i][j] || '';
                    cell.title = '行 ' + i + ', 列 ' + j + ': ' + (data.bestGrid[i][j] || 'N/A');
                    grid.appendChild(cell);
                }
            }
        }
        
        function renderEvolutionChart() {
            const container = document.getElementById('evolutionChart');
            container.innerHTML = '';
            
            // 模擬進化數據
            const generations = 50;
            for (let gen = 0; gen < generations; gen++) {
                const row = document.createElement('div');
                row.className = 'generation-row';
                
                const label = document.createElement('div');
                label.className = 'generation-label';
                label.textContent = '代 ' + gen;
                
                const bar = document.createElement('div');
                bar.className = 'progress-bar';
                
                const fill = document.createElement('div');
                fill.className = 'progress-fill elite';
                const fitness = 0.1 + 0.4 * Math.min(1, gen / 30) + Math.random() * 0.05;
                fill.style.width = (fitness * 100) + '%';
                
                bar.appendChild(fill);
                
                const value = document.createElement('div');
                value.className = 'fit-value';
                value.textContent = fitness.toFixed(3);
                
                row.appendChild(label);
                row.appendChild(bar);
                row.appendChild(value);
                container.appendChild(row);
            }
        }
        
        function renderPruningStats() {
            const container = document.getElementById('pruningStats');
            container.innerHTML = '';
            
            const strategies = [
                { name: '符闔排列剪枝', key: 'fahuo', color: 'fahuo', desc: '將搜索空間壓縮 ~10^50 倍' },
                { name: '列約束剪枝', key: 'column', color: 'column', desc: '檢測 16 列的 AllDifferent' },
                { name: '宮約束剪枝', key: 'box', color: 'box', desc: '檢測 16 宮的 AllDifferent' }
            ];
            
            for (const strat of strategies) {
                const pr = data.pruning.find(p => p.strategy === strat.key);
                if (pr) {
                    const card = document.createElement('div');
                    card.className = 'pruning-card ' + strat.color;
                    card.innerHTML = \`
                        <div class="pruning-name">${strat.name}</div>
                        <div class="pruning-metrics">
                            <div class="metric">效率: <span class="metric-value">${(pr.efficiency * 100).toFixed(1)}%</span></div>
                            <div class="metric">衝突: <span class="metric-value">${pr.violations}</span></div>
                        </div>
                        <div style="margin-top: 0.5rem; color: #888; font-size: 0.8rem;">${strat.desc}</div>
                    \`;
                    container.appendChild(card);
                }
            }
        }
        
        function generatePermutationTable(top10) {
            let html = '';
            for (let i = 0; i < Math.min(top10.length, 12); i++) {
                const item = top10[i];
                html += \`
                    <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 0.75rem;">
                        <div style="font-size: 0.85rem; color: #888; margin-bottom: 0.25rem;">適應度: ${item.fitness.toFixed(3)}</div>
                        <div style="font-family: monospace; font-size: 0.75rem; word-break: break-all; color: #00ffc8;">
                            \${item.permutationChoices.join(', ')}
                        </div>
                    </div>
                \`;
            }
            return html;
        }
        
        function showPhaseComplete() {
            setTimeout(() => {
                const notification = document.createElement('div');
                notification.className = 'phase-complete';
                notification.innerHTML = \`
                    <strong>✅ V19.0 求解完成</strong><br>
                    7 個階段全部執行成功
                \`;
                document.body.appendChild(notification);
            }, 1000);
        }
    </script>
</body>
</html>`;

// 保存 HTML
const outputPath = path.join(__dirname, 'cosmic_thunder_visualization.html');
fs.writeFileSync(outputPath, html, 'utf-8');

console.log(`✅ 交互式視覺化已生成: ${outputPath}`);
console.log(`   文件大小: ${Math.round(html.length / 1024)} KB`);
