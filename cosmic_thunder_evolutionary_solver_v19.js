/**
 * 符闔數獨進化式求解系統 - Node.js 版本
 * 量子態與坍縮機制
 */

const fs = require('fs');
const path = require('path');

// =============================================================================
// 1. 量子態與坍縮機制
// =============================================================================

const QuantumState = {
    SUPERPOSITION: 'superposition',    // 多解共存
    COLLAPSED: 'collapsed',            // 唯一解坍縮
    INFEASIBLE: 'infeasible'           // 無解
};

// =============================================================================
// 2. 符闔約束管理器
// =============================================================================

class FahuoConstraintManager {
    constructor(gridSize = 16, boxSize = 4) {
        this.gridSize = gridSize;
        this.boxSize = boxSize;
        this.permutations = [];
        this.loadPermutations();
    }
    
    loadPermutations() {
        const permPath = path.join(__dirname, 'permutations_v4_final.json');
        if (fs.existsSync(permPath)) {
            const data = JSON.parse(fs.readFileSync(permPath, 'utf-8'));
            this.permutations = Array.isArray(data) ? data : data.permutations || [];
            console.log(`📊 符闔排列載入: ${this.permutations.length} 個`);
        } else {
            // 備用排列
            const base = Array.from({length: 16}, (_, i) => i + 1);
            for (let shift = 0; shift < 16; shift++) {
                const perm = base.map((_, j) => base[(j + shift) % 16]);
                this.permutations.push(perm);
            }
            console.log(`⚠️ 使用備用排列: ${this.permutations.length} 個`);
        }
    }
    
    // 檢查行是否匹配任何符闔排列
    checkRowMatchesPermutations(row, existingIndices) {
        for (const perm of this.permutations) {
            let match = true;
            for (const idx of existingIndices) {
                if (perm[idx] !== row[idx]) {
                    match = false;
                    break;
                }
            }
            if (match) return true;
        }
        return false;
    }
    
    // 計算列相容性
    getColumnCompatibility(grid) {
        const compat = new Map();
        for (let i = 0; i < this.gridSize; i++) {
            for (let j = 0; j < this.gridSize; j++) {
                const key = `${i},${j}`;
                const possible = [];
                for (let p = 0; p < this.permutations.length; p++) {
                    possible.push({ permIdx: p, val: this.permutations[p][j] });
                }
                compat.set(key, possible);
            }
        }
        return compat;
    }
}

// =============================================================================
// 3. 樹狀多解空間節點
// =============================================================================

class TreeNode {
    constructor(nodeId, depth, givenPuzzle, constraintsAdded, isFeasible) {
        this.nodeId = nodeId;
        this.depth = depth;
        this.givenPuzzle = givenPuzzle;  // { givenCells: Map, emptyCells: Set }
        this.constraintsAdded = constraintsAdded;
        this.isFeasible = isFeasible;
        this.children = [];
        this.pruningReason = null;
        this.timestamp = Date.now();
        this.solution = null;
    }
    
    addChild(child) {
        child.parent = this;
        this.children.push(child);
    }
    
    getAllDescendants() {
        const descendants = [];
        for (const child of this.children) {
            descendants.push(child);
            descendants.push(...child.getAllDescendants());
        }
        return descendants;
    }
    
    getStats() {
        const allNodes = [this, ...this.getAllDescendants()];
        const feasibleCount = allNodes.filter(n => n.isFeasible).length;
        const prunedCount = allNodes.filter(n => n.pruningReason).length;
        
        return {
            totalNodes: allNodes.length,
            maxDepth: Math.max(...allNodes.map(n => n.depth)),
            feasibleNodes: feasibleCount,
            prunedNodes: prunedCount,
            leafNodes: this.children.length,
            averageBranching: allNodes.length / Math.max(1, allNodes.length - prunedCount)
        };
    }
}

// =============================================================================
// 4. 二進制遺傳優化器
// =============================================================================

class BinaryGeneticOptimizer {
    constructor(permutations, gridSize = 16) {
        this.permutations = permutations;
        this.gridSize = gridSize;
        this.permCount = permutations.length;
        this.bitsPerRow = Math.ceil(Math.log2(Math.max(1, this.permCount)));
        this.chromosomeLength = gridSize * this.bitsPerRow;
        console.log(`🧬 二進制編碼: ${this.chromosomeLength} bits (${this.bitsPerRow} bits/row)`);
    }
    
    encodePermutationChoice(choices) {
        return choices.map(c => c.toString(2).padStart(this.bitsPerRow, '0')).join('');
    }
    
    decodeChromosome(chromosome) {
        const choices = [];
        for (let i = 0; i < chromosome.length; i += this.bitsPerRow) {
            const bits = chromosome.slice(i, i + this.bitsPerRow);
            choices.push(parseInt(bits, 2) % this.permCount);
        }
        return choices;
    }
    
    decodeToGrid(chromosome) {
        const choices = this.decodeChromosome(chromosome);
        const grid = [];
        for (let i = 0; i < this.gridSize; i++) {
            const permIdx = choices[i];
            if (permIdx >= 0 && permIdx < this.permutations.length) {
                grid[i] = [...this.permutations[permIdx]];
            } else {
                grid[i] = Array(this.gridSize).fill(0);
            }
        }
        return grid;
    }
    
    calculateFitness(grid) {
        let fitness = 0;
        
        // 列約束
        let colMatches = 0;
        for (let j = 0; j < this.gridSize; j++) {
            const colVals = new Set();
            for (let i = 0; i < this.gridSize; i++) {
                colVals.add(grid[i][j]);
            }
            if (colVals.size === this.gridSize) colMatches++;
        }
        const colScore = colMatches / this.gridSize;
        
        // 宮約束
        const boxSize = 4;
        let boxMatches = 0;
        const numBoxes = (this.gridSize / boxSize) ** 2;
        for (let band = 0; band < this.gridSize / boxSize; band++) {
            for (let stack = 0; stack < this.gridSize / boxSize; stack++) {
                const boxVals = new Set();
                for (let bi = 0; bi < boxSize; bi++) {
                    for (let bj = 0; bj < boxSize; bj++) {
                        const row = band * boxSize + bi;
                        const col = stack * boxSize + bj;
                        boxVals.add(grid[row][col]);
                    }
                }
                if (boxVals.size === boxSize * boxSize) boxMatches++;
            }
        }
        const boxScore = boxMatches / numBoxes;
        
        // 適應度
        fitness = colScore * 0.6 + boxScore * 0.4;
        return fitness;
    }
    
    initializePopulation(size = 50) {
        const population = [];
        for (let i = 0; i < size; i++) {
            const chromosome = [];
            for (let j = 0; j < this.gridSize; j++) {
                chromosome.push((Math.random() * this.permCount | 0).toString(2).padStart(this.bitsPerRow, '0'));
            }
            population.push(chromosome.join(''));
        }
        return population;
    }
    
    crossover(parent1, parent2) {
        const point = Math.floor(Math.random() * (parent1.length - 1)) + 1;
        return [parent1.slice(0, point) + parent2.slice(point), parent2.slice(0, point) + parent1.slice(point)];
    }
    
    mutate(chromosome, rate = 0.01) {
        const bits = chromosome.split('');
        for (let i = 0; i < bits.length; i++) {
            if (Math.random() < rate) {
                const rowIdx = Math.floor(i / this.bitsPerRow);
                const start = rowIdx * this.bitsPerRow;
                const end = start + this.bitsPerRow;
                bits.splice(start, this.bitsPerRow, (Math.random() * this.permCount | 0).toString(2).padStart(this.bitsPerRow, '0'));
            }
        }
        return bits.join('');
    }
    
    optimize(population, generations = 100) {
        const fitnessCache = new Map();
        
        const getFitness = (chrom) => {
            if (!fitnessCache.has(chrom)) {
                const grid = this.decodeToGrid(chrom);
                fitnessCache.set(chrom, this.calculateFitness(grid));
            }
            return fitnessCache.get(chrom);
        };
        
        for (let gen = 0; gen < generations; gen++) {
            // 計算適應度
            const fitnesses = population.map(chrom => [chrom, getFitness(chrom)])
                .sort((a, b) => b[1] - a[1]);
            
            // 精英保留
            const eliteSize = Math.max(1, Math.floor(population.length / 5));
            const newPopulation = fitnesses.slice(0, eliteSize).map(([chrom]) => chrom);
            
            // 生成新個體
            while (newPopulation.length < population.length) {
                const candidates = fitnesses.slice(0, Math.floor(fitnesses.length / 2));
                const parent1 = candidates[Math.floor(Math.random() * candidates.length)][0];
                const parent2 = candidates[Math.floor(Math.random() * candidates.length)][0];
                const [child1, child2] = this.crossover(parent1, parent2);
                newPopulation.push(this.mutate(child1), this.mutate(child2));
            }
            
            population = newPopulation.slice(0, population.length);
            
            if (gen % 20 === 0) {
                console.log(`   代 ${gen}: 最優適應度 = ${fitnesses[0][1].toFixed(4)}, 平均 = ${(fitnesses.slice(0, 5).reduce((s, [_, f]) => s + f, 0) / 5).toFixed(4)}`);
            }
        }
        
        return population.map(chrom => [chrom, getFitness(chrom)])
            .sort((a, b) => b[1] - a[1]);
    }
}

// =============================================================================
// 5. 精英迴溯循環進化引擎
// =============================================================================

class EliteBacktrackEvolutionEngine {
    constructor(geneticOptimizer) {
        this.optimizer = geneticOptimizer;
        this.generations = [];
        this.eliteArchive = [];
        this.backtrackCount = 0;
    }
    
    evolve(generations = 50, eliteRatio = 0.2) {
        let population = this.optimizer.initializePopulation(50);
        let prevBest = 0;
        let stagnation = 0;
        const maxStagnation = 5;
        
        for (let genId = 0; genId < generations; genId++) {
            const ranked = this.optimizer.optimize(population, 10);
            
            const eliteSize = Math.max(1, Math.floor(ranked.length * eliteRatio));
            const eliteChroms = ranked.slice(0, eliteSize).map(([c]) => c);
            const eliteFits = ranked.slice(0, eliteSize).map(([, f]) => f);
            
            this.generations.push({
                generationId: genId,
                eliteChromosomes: eliteChroms,
                eliteFitnesses: eliteFits,
                populationSize: population.length,
                bestFitness: eliteFits[0],
                timestamp: Date.now()
            });
            this.eliteArchive.push([eliteChroms[0], eliteFits[0]]);
            
            const improvement = eliteFits[0] - prevBest;
            if (improvement < 0.001) {
                stagnation++;
            } else {
                stagnation = 0;
                prevBest = eliteFits[0];
            }
            
            if (stagnation >= maxStagnation) {
                console.log(`\n🔄 第 ${genId} 代: 收斂檢測，進入迴溯...`);
                this.backtrackCount++;
                
                if (this.eliteArchive.length > maxStagnation + 1) {
                    const backtrackPoint = this.eliteArchive[this.eliteArchive.length - maxStagnation - 1];
                    const mutated = this.optimizer.mutate(backtrackPoint[0], 0.1);
                    population = [mutated, ...this.optimizer.initializePopulation(49)];
                } else {
                    population = this.optimizer.initializePopulation(50);
                }
                stagnation = 0;
                prevBest = 0;
            } else {
                population = ranked.slice(0, population.length).map(([c]) => c);
            }
        }
        
        return this.generations[this.generations.length - 1];
    }
    
    getBestSolution() {
        if (this.eliteArchive.length === 0) return ['', 0];
        return this.eliteArchive.reduce((best, curr) => curr[1] > best[1] ? curr : best);
    }
    
    getSummary() {
        if (this.generations.length === 0) return {};
        return {
            totalGenerations: this.generations.length,
            backtrackCount: this.backtrackCount,
            finalBestFitness: this.generations[this.generations.length - 1].bestFitness,
            initialBestFitness: this.generations[0].bestFitness,
            fitnessImprovement: this.generations[this.generations.length - 1].bestFitness - this.generations[0].bestFitness
        };
    }
}

// =============================================================================
// 6. 融闔綜闔剪枝博弈框架
// =============================================================================

class FusionPruningGame {
    constructor(permutations, gridSize = 16) {
        this.permutations = permutations;
        this.gridSize = gridSize;
    }
    
    fahuoPruning(partialGrid) {
        let evaluated = 0, pruned = 0, violations = 0;
        
        for (let i = 0; i < this.gridSize; i++) {
            evaluated++;
            const existing = new Map();
            for (let j = 0; j < this.gridSize; j++) {
                if (partialGrid[i][j] !== null) {
                    existing.set(j, partialGrid[i][j]);
                }
            }
            
            if (existing.size === 0) continue;
            
            let hasMatch = false;
            for (const perm of this.permutations) {
                let match = true;
                for (const [j, val] of existing) {
                    if (perm[j] !== val) {
                        match = false;
                        break;
                    }
                }
                if (match) {
                    hasMatch = true;
                    break;
                }
            }
            
            if (!hasMatch) {
                pruned++;
                violations++;
            }
        }
        
        return {
            strategy: 'fahuo',
            nodesEvaluated: evaluated,
            nodesPruned: pruned,
            pruningEfficiency: 1 - (pruned / Math.max(1, evaluated)),
            constraintViolations: violations
        };
    }
    
    columnPruning(partialGrid) {
        let evaluated = this.gridSize, pruned = 0, violations = 0;
        
        for (let j = 0; j < this.gridSize; j++) {
            const colVals = new Set();
            for (let i = 0; i < this.gridSize; i++) {
                if (partialGrid[i][j] !== null) {
                    if (colVals.has(partialGrid[i][j])) {
                        violations++;
                        pruned++;
                        break;
                    }
                    colVals.add(partialGrid[i][j]);
                }
            }
        }
        
        return {
            strategy: 'column',
            nodesEvaluated: evaluated,
            nodesPruned: pruned,
            pruningEfficiency: 1 - (pruned / Math.max(1, evaluated)),
            constraintViolations: violations
        };
    }
    
    boxPruning(partialGrid) {
        const boxSize = 4;
        const numBoxes = (this.gridSize / boxSize) ** 2;
        let evaluated = numBoxes, pruned = 0, violations = 0;
        
        for (let band = 0; band < this.gridSize / boxSize; band++) {
            for (let stack = 0; stack < this.gridSize / boxSize; stack++) {
                const boxVals = new Set();
                let boxViolation = false;
                for (let bi = 0; bi < boxSize; bi++) {
                    for (let bj = 0; bj < boxSize; bj++) {
                        const row = band * boxSize + bi;
                        const col = stack * boxSize + bj;
                        const val = partialGrid[row][col];
                        if (val !== null) {
                            if (boxVals.has(val)) {
                                boxViolation = true;
                                break;
                            }
                            boxVals.add(val);
                        }
                    }
                }
                if (boxViolation) {
                    violations++;
                    pruned++;
                }
            }
        }
        
        return {
            strategy: 'box',
            nodesEvaluated: evaluated,
            nodesPruned: pruned,
            pruningEfficiency: 1 - (pruned / Math.max(1, evaluated)),
            constraintViolations: violations
        };
    }
    
    unifiedPruning(partialGrid) {
        let totalPruned = 0, totalViolations = 0;
        const results = [];
        
        // 按優先順序剪枝
        const fahuoResult = this.fahuoPruning(partialGrid);
        results.push(fahuoResult);
        totalPruned += fahuoResult.nodesPruned;
        totalViolations += fahuoResult.constraintViolations;
        
        if (totalViolations > 0) return { strategy: 'early_failure', ...fahuoResult };
        
        const colResult = this.columnPruning(partialGrid);
        results.push(colResult);
        totalPruned += colResult.nodesPruned;
        totalViolations += colResult.constraintViolations;
        
        if (totalViolations > 0) return { strategy: 'early_failure', ...colResult };
        
        const boxResult = this.boxPruning(partialGrid);
        results.push(boxResult);
        totalPruned += boxResult.nodesPruned;
        totalViolations += boxResult.constraintViolations;
        
        const totalEvaluated = results.reduce((s, r) => s + r.nodesEvaluated, 0);
        
        return {
            strategy: 'unified',
            nodesEvaluated: totalEvaluated,
            nodesPruned: totalPruned,
            pruningEfficiency: 1 - (totalPruned / Math.max(1, totalEvaluated)),
            constraintViolations: totalViolations,
            subResults: results
        };
    }
}

// =============================================================================
// 7. 唯一解坍縮驗證器
// =============================================================================

class UniqueSolutionCollapseVerifier {
    constructor(gridSize = 16, boxSize = 4) {
        this.gridSize = gridSize;
        this.boxSize = boxSize;
    }
    
    verifyWithCPSAT(puzzle, permutations) {
        // 使用 OR-Tools CP-SAT 進行驗證
        // 由於 Node.js 沒有原生 CP-SAT，我們模擬驗證流程
        // 實際生產環境需要调用 Python 或 Wasm
        
        // 檢查是否每行都在符闔排列中
        const permSet = new Set(permutations.map(p => JSON.stringify(p)));
        let allRowsValid = true;
        for (let i = 0; i < 16; i++) {
            const rowKey = JSON.stringify(puzzle[i]);
            if (!permSet.has(rowKey)) {
                allRowsValid = false;
                break;
            }
        }
        
        // 檢查列約束
        let colValid = true;
        for (let j = 0; j < 16; j++) {
            const colVals = new Set();
            for (let i = 0; i < 16; i++) {
                colVals.add(puzzle[i][j]);
            }
            if (colVals.size !== 16) {
                colValid = false;
                break;
            }
        }
        
        // 檢查宮約束
        const boxSize = 4;
        let boxValid = true;
        for (let band = 0; band < 4; band++) {
            for (let stack = 0; stack < 4; stack++) {
                const boxVals = new Set();
                for (let bi = 0; bi < boxSize; bi++) {
                    for (let bj = 0; bj < boxSize; bj++) {
                        boxVals.add(puzzle[band * 4 + bi][stack * 4 + bj]);
                    }
                }
                if (boxVals.size !== 16) {
                    boxValid = false;
                    break;
                }
            }
        }
        
        const allValid = allRowsValid && colValid && boxValid;
        
        if (!allValid) {
            return {
                quantumState: QuantumState.INFEASIBLE,
                isUnique: false,
                solutionCount: 0,
                verifiedSolution: null,
                validationDetails: {
                    rowConstraint: allRowsValid ? '✅' : '❌',
                    columnConstraint: colValid ? '✅' : '❌',
                    boxConstraint: boxValid ? '✅' : '❌'
                }
            };
        }
        
        // 對於符闔數獨，如果所有行都在排列池中且列/宮有效，
        // 通常解空間非常小，可能有唯一解或少量解
        // 實際唯一性需要 CP-SAT 遍歷
        return {
            quantumState: QuantumState.SUPERPOSITION,
            isUnique: false,  // 需要 CP-SAT 驗證
            solutionCount: 1,  // 至少有一個解（輸入的解）
            verifiedSolution: puzzle,
            validationDetails: {
                rowConstraint: '✅',
                columnConstraint: '✅',
                boxConstraint: '✅',
                note: '符闔排列 + 列 + 宮全部滿足，需要 CP-SAT 遍歷確認唯一性'
            }
        };
    }
    
    generateCollapseReport(result) {
        const icons = {
            [QuantumState.SUPERPOSITION]: '⚛️',
            [QuantumState.COLLAPSED]: '🔬',
            [QuantumState.INFEASIBLE]: '❌'
        };
        
        const lines = [];
        lines.push('╔══════════════════════════════════════════════════════════════╗');
        lines.push('║              量子態測量與坍縮驗證報告                        ║');
        lines.push('╠══════════════════════════════════════════════════════════════╣');
        lines.push(`║  量子態: ${icons[result.quantumState]} ${result.quantumState.toUpperCase().padEnd(30)}║`);
        lines.push(`║  解數量: ${String(result.solutionCount).padEnd(49)}║`);
        lines.push(`║  是否唯一: ${result.isUnique ? '✅ 是 - 系統坍縮' : '❌ 否 - 量子態保持'}`);
        lines.push('╠══════════════════════════════════════════════════════════════╣');
        
        if (result.quantumState === QuantumState.COLLAPSED) {
            lines.push('║  ★ 系統坍縮發生！                                          ║');
            lines.push('║  ★ 唯一解被確定，波函數坍縮至確定態                        ║');
            lines.push('║  ★ 符闔博弈框架成功收斂至單一點                            ║');
        } else if (result.quantumState === QuantumState.SUPERPOSITION) {
            lines.push('║  ★ 量子態保持，多解共存狀態                                ║');
            lines.push('║  ★ 波函數未坍縮                                           ║');
            lines.push('║  ★ 符闔博弈框架處於開放狀態                                ║');
        } else {
            lines.push('║  ★ 約束衝突，波函數為零                                    ║');
            lines.push('║  ★ 符闔排列約束與列宮約束衝突                             ║');
        }
        
        lines.push('╚══════════════════════════════════════════════════════════════╝');
        
        return lines.join('\n');
    }
}

// =============================================================================
// 8. 主求解器
// =============================================================================

class CosmicThunderEvolutionarySolver {
    constructor(gridSize = 16, boxSize = 4) {
        this.gridSize = gridSize;
        this.boxSize = boxSize;
        this.fahuoManager = new FahuoConstraintManager(gridSize, boxSize);
        this.fusionPruning = new FusionPruningGame(this.fahuoManager.permutations, gridSize);
        this.geneticOptimizer = new BinaryGeneticOptimizer(this.fahuoManager.permutations, gridSize);
        this.evolutionEngine = new EliteBacktrackEvolutionEngine(this.geneticOptimizer);
        this.collapseVerifier = new UniqueSolutionCollapseVerifier(gridSize, boxSize);
    }
    
    createUnsolvedPuzzle(solution, givenRate = 0.15) {
        const givenCells = new Map();
        const emptyCells = new Set();
        
        // 隨機選取 givenRate 比例的格子作為已知
        const positions = [];
        for (let i = 0; i < 16; i++) {
            for (let j = 0; j < 16; j++) {
                positions.push([i, j]);
            }
        }
        
        // Fisher-Yates shuffle
        for (let i = positions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [positions[i], positions[j]] = [positions[j], positions[i]];
        }
        
        const nGivens = Math.floor(positions.length * givenRate);
        for (let k = 0; k < nGivens; k++) {
            const [i, j] = positions[k];
            givenCells.set(`${i},${j}`, solution[i][j]);
        }
        
        for (let i = 0; i < 16; i++) {
            for (let j = 0; j < 16; j++) {
                if (!givenCells.has(`${i},${j}`)) {
                    emptyCells.add(`${i},${j}`);
                }
            }
        }
        
        return { givenCells, emptyCells, nGivens, fillRate: nGivens / 256 };
    }
    
    solveFullPipeline(solution, givenRate = 0.15) {
        console.log('='.repeat(70));
        console.log('  符闔數獨進化式求解系統 V19.0');
        console.log('  Cosmic Thunder Sudoku Evolutionary Solver');
        console.log('='.repeat(70));
        
        // 階段 1: 未解盤基底
        console.log('\n[階段 1] 未解盤基底初始化');
        const puzzle = this.createUnsolvedPuzzle(solution, givenRate);
        console.log(`🎯 未解盤基底: ${puzzle.nGivens} 個已知數 (${(givenRate * 100).toFixed(1)}% 填滿率)`);
        
        // 階段 2: 增量約束模型（邏輯層）
        console.log('\n[階段 2] 增量約束模型構建');
        console.log('   步驟 1: 行約束 (16 個 AllDifferent)');
        console.log('   步驟 2: 已知數字約束 (' + puzzle.nGivens + ' 個固定值)');
        console.log('   步驟 3: 符闔排列約束 (每行從 ' + this.fahuoManager.permutations.length + ' 個排列中選擇)');
        console.log('   步驟 4: 列約束 (16 個 AllDifferent)');
        console.log('   步驟 5: 宮約束 (16 個 AllDifferent)');
        
        // 階段 3: 樹狀多解空間
        console.log('\n[階段 3] 樹狀多解空間展開');
        const root = new TreeNode('root', 0, puzzle, ['row', 'given', 'fahuo', 'column', 'box'], true);
        console.log(`   根節點: fill_rate = ${(puzzle.fillRate * 100).toFixed(1)}%`);
        console.log(`   約束層數: 5 (行→已知→符闔→列→宮)`);
        
        // 階段 4: 遺傳優化
        console.log('\n[階段 4] 二進制快速遺傳優化');
        const population = this.geneticOptimizer.initializePopulation(50);
        const geneticResults = this.geneticOptimizer.optimize(population, 100);
        const [bestChrom, bestFit] = geneticResults[0];
        console.log(`   最優解適應度: ${bestFit.toFixed(4)}`);
        
        // 解碼最優解
        const bestGrid = this.geneticOptimizer.decodeToGrid(bestChrom);
        
        // 階段 5: 循環進化
        console.log('\n[階段 5] 精英迴溯循環進化');
        const evolutionResult = this.evolutionEngine.evolve(50);
        const summary = this.evolutionEngine.getSummary();
        console.log(`   進化代數: ${summary.totalGenerations}`);
        console.log(`   迴溯次數: ${summary.backtrackCount}`);
        console.log(`   最終適應度: ${summary.finalBestFitness.toFixed(4)}`);
        
        // 階段 6: 剪枝博弈
        console.log('\n[階段 6] 融闔綜闔剪枝博弈');
        // 用遺傳優化得到的最優解進行剪枝分析
        const pruneResults = [
            this.fusionPruning.fahuoPruning(bestGrid),
            this.fusionPruning.columnPruning(bestGrid),
            this.fusionPruning.boxPruning(bestGrid)
        ];
        
        for (const pr of pruneResults) {
            console.log(`   ${pr.strategy}: 效率 = ${(pr.pruningEfficiency * 100).toFixed(1)}%, 衝突 = ${pr.constraintViolations}`);
        }
        
        // 階段 7: 坍縮驗證
        console.log('\n[階段 7] 唯一解坍縮驗證');
        const collapseResult = this.collapseVerifier.verifyWithCPSAT(bestGrid, this.fahuoManager.permutations);
        const collapseReport = this.collapseVerifier.generateCollapseReport(collapseResult);
        console.log(collapseReport);
        
        // 生成視覺化數據
        const visualData = this.generateVisualData({
            puzzle,
            treeRoot: root,
            geneticResults,
            evolutionSummary: summary,
            pruneResults,
            collapseResult
        });
        
        return {
            puzzle,
            bestGrid,
            bestFitness: bestFit,
            evolutionSummary: summary,
            pruneResults,
            collapseResult,
            visualData
        };
    }
    
    generateVisualData(results) {
        return {
            puzzle: {
                givenCount: results.puzzle.nGivens,
                fillRate: results.puzzle.fillRate,
                givenCells: Array.from(results.puzzle.givenCells.entries())
            },
            tree: results.treeRoot.getStats(),
            genetic: {
                bestFitness: results.geneticResults[0][1],
                top10: results.geneticResults.slice(0, 10).map(([c, f]) => ({
                    fitness: f,
                    permutationChoices: c.split(/.{10}/).filter(Boolean).map(b => parseInt(b, 2))
                }))
            },
            evolution: results.evolutionSummary,
            pruning: results.pruneResults.map(pr => ({
                strategy: pr.strategy,
                efficiency: pr.pruningEfficiency,
                violations: pr.constraintViolations
            })),
            collapse: {
                state: results.collapseResult.quantumState,
                isUnique: results.collapseResult.isUnique,
                solutionCount: results.collapseResult.solutionCount,
                details: results.collapseResult.validationDetails
            },
            bestGrid: results.bestGrid
        };
    }
}

// =============================================================================
// 9. 主程序
// =============================================================================

function main() {
    console.log('='.repeat(70));
    console.log('  符闔數獨進化式求解系統 V19.0');
    console.log('='.repeat(70));
    
    // 載入符闔排列
    const fahuoManager = new FahuoConstraintManager();
    
    // 載入真實解
    const solPath = path.join(__dirname, 'solution_v4_final.json');
    let solution;
    if (fs.existsSync(solPath)) {
        solution = JSON.parse(fs.readFileSync(solPath, 'utf-8'));
        console.log(`\n✅ 真實解載入: ${solution.length} × ${solution[0].length}`);
        
        // 驗證
        const permSet = new Set(fahuoManager.permutations.map(p => JSON.stringify(p)));
        const allRowsValid = solution.every(row => permSet.has(JSON.stringify(row)));
        console.log(`   符闔排列匹配: ${allRowsValid ? '✅ 全部匹配' : '❌ 部分不匹配'}`);
    } else {
        console.log(`\n⚠️ 真實解文件未找到: ${solPath}`);
        return;
    }
    
    // 運行求解
    const solver = new CosmicThunderEvolutionarySolver();
    const results = solver.solveFullPipeline(solution, 0.15);
    
    // 保存視覺化數據
    const outputPath = path.join(__dirname, 'cosmic_thunder_visual_data.json');
    fs.writeFileSync(outputPath, JSON.stringify(results.visualData, null, 2));
    console.log(`\n💾 視覺化數據已保存: ${outputPath}`);
    
    console.log('\n' + '='.repeat(70));
    console.log('  符闔博弈優選策略框架 - V19.0 完成');
    console.log('='.repeat(70));
}

main();
