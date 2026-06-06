#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨整合求解框架
融合DFS擴展、CP-SAT SolutionCollector、SAT精確計數、博弈優化
生成A4電子文檔報告
"""

import json
import time
import subprocess
import os
from typing import List, Dict, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas


class IntegratedSolverFramework:
    """整合求解框架"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.config_path = config_path
        self.results = {}
        self.start_time = 0
        
    def run_all_methods(self):
        """執行所有求解方法"""
        self.start_time = time.time()
        
        print("=" * 70)
        print("符闔數獨整合求解框架")
        print("=" * 70)
        
        # === 方法1: DFS擴展搜索 ===
        print("\n【方法1】DFS擴展搜索 (上限1000解)")
        dfs_result = self._run_dfs_extended()
        self.results['dfs'] = dfs_result
        
        # === 方法2: CP-SAT SolutionCollector ===
        print("\n【方法2】CP-SAT SolutionCollector (上限1000解)")
        cpsat_result = self._run_cpsat()
        self.results['cpsat'] = cpsat_result
        
        # === 方法3: SAT DIMACS編碼 ===
        print("\n【方法3】SAT DIMACS 編碼")
        sat_result = self._run_sat_encoder()
        self.results['sat'] = sat_result
        
        # === 方法4: 博弈優化 ===
        print("\n【方法4】樹狀博弈剪枝優化")
        game_result = self._run_game_optimizer()
        self.results['game_opt'] = game_result
        
        # === 結果匯總 ===
        total_time = time.time() - self.start_time
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_execution_time_seconds": round(total_time, 2),
            "results_summary": {
                "dfs_solutions": dfs_result.get('statistics', {}).get('total_solutions', 0),
                "cpsat_solutions": cpsat_result.get('statistics', {}).get('total_solutions', 0),
                "sat_vars": sat_result.get('num_vars', 0),
                "sat_clauses": sat_result.get('num_clauses', 0),
                "game_opt_solutions": game_result.get('total_solutions_found', 0),
                "game_opt_nodes_explored": game_result.get('statistics', {}).get('total_nodes_explored', 0)
            },
            "conclusion": self._generate_conclusion(),
            "method_comparison": self._compare_methods()
        }
        
        self.results['summary'] = summary
        
        return self.results
    
    def _run_dfs_extended(self) -> Dict:
        """運行DFS擴展"""
        try:
            result = subprocess.run(
                ['python', 'verify_solution_v5_extended.py'],
                capture_output=True,
                text=True,
                timeout=7200,  # 2小時
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                try:
                    with open('solution_count_extended.json', 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {"error": "無法讀取結果文件", "stdout": result.stdout[:500]}
            else:
                return {"error": "DFS執行失敗", "stderr": result.stderr[:500]}
        except subprocess.TimeoutExpired:
            return {"error": "DFS超時", "timeout": True}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_cpsat(self) -> Dict:
        """運行CP-SAT"""
        try:
            result = subprocess.run(
                ['python', 'cpsat_solution_collector.py'],
                capture_output=True,
                text=True,
                timeout=7200,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                try:
                    with open('cpsat_collection_result.json', 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {"error": "無法讀取結果文件", "stdout": result.stdout[:500]}
            else:
                return {"error": "CP-SAT執行失敗", "stderr": result.stderr[:500]}
        except subprocess.TimeoutExpired:
            return {"error": "CP-SAT超時", "timeout": True}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_sat_encoder(self) -> Dict:
        """運行SAT編碼器"""
        try:
            result = subprocess.run(
                ['python', 'sat_dimacs_encoder.py'],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                try:
                    with open('sat_encoding_result.json', 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {"error": "無法讀取結果文件", "stdout": result.stdout[:500]}
            else:
                return {"error": "SAT編碼失敗", "stderr": result.stderr[:500]}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_game_optimizer(self) -> Dict:
        """運行博弈優化"""
        try:
            result = subprocess.run(
                ['python', 'tree_branching_optimizer.py'],
                capture_output=True,
                text=True,
                timeout=7200,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                try:
                    with open('tree_optimization_result.json', 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {"error": "無法讀取結果文件", "stdout": result.stdout[:500]}
            else:
                return {"error": "博弈優化失敗", "stderr": result.stderr[:500]}
        except subprocess.TimeoutExpired:
            return {"error": "博弈優化超時", "timeout": True}
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_conclusion(self) -> str:
        """生成結論"""
        dfs_sols = self.results['dfs'].get('statistics', {}).get('total_solutions', 0)
        cpsat_sols = self.results['cpsat'].get('statistics', {}).get('total_solutions', 0)
        game_sols = self.results['game_opt'].get('total_solutions_found', 0)
        
        max_solutions = max(dfs_sols, cpsat_sols, game_sols)
        
        if max_solutions >= 1000:
            conclusion = f"該16×16符闔數獨具有大量解，至少找到1000個解（達到上限）。多解性質確鑿。"
        elif max_solutions >= 100:
            conclusion = f"該16×16符闔數獨具有多解，已找到{max_solutions}個解。非唯一解。"
        elif max_solutions >= 10:
            conclusion = f"該16×16符闔數獨具有多解，已找到{max_solutions}個解。非唯一解。"
        elif max_solutions == 1:
            conclusion = "該16×16符闔數獨具有唯一解。"
        else:
            conclusion = f"該16×16符闔數獨解數量尚未完全確定，目前找到{max_solutions}個解。"
        
        return conclusion
    
    def _compare_methods(self) -> Dict:
        """方法比較"""
        methods = {}
        
        for method_name in ['dfs', 'cpsat', 'game_opt']:
            if method_name in self.results:
                result = self.results[method_name]
                methods[method_name] = {
                    "solutions": result.get('statistics', {}).get('total_solutions', 
                                     result.get('total_solutions_found', 0)),
                    "time_seconds": result.get('statistics', {}).get('time_seconds', 0),
                    "nodes_explored": result.get('statistics', {}).get('nodes_explored',
                                        result.get('statistics', {}).get('total_nodes_explored', 0)),
                    "pruning_count": result.get('statistics', {}).get('pruning_count', 0)
                }
        
        return methods
    
    def generate_pdf_report(self, output_path: str = "符闔數獨精確計數報告_A4.pdf"):
        """生成A4 PDF報告"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # 自定義樣式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # 居中
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12
        )
        
        normal_style = styles['Normal']
        
        # 構建內容
        story = []
        
        # 標題
        story.append(Paragraph("16×16 符闔數獨精確計數報告", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # 時間戳
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        story.append(Paragraph(f"生成時間: {timestamp}", normal_style))
        story.append(Spacer(1, 0.3*cm))
        
        # 執行概覽
        summary = self.results['summary']
        story.append(Paragraph("一、執行概覽", heading_style))
        
        exec_info = [
            ["總執行時間", f"{summary['total_execution_time_seconds']:.2f} 秒"],
            ["DFS解數量", str(summary['results_summary']['dfs_solutions'])],
            ["CP-SAT解數量", str(summary['results_summary']['cpsat_solutions'])],
            ["博弈優化解數量", str(summary['results_summary']['game_opt_solutions'])],
            ["SAT變數數量", str(summary['results_summary']['sat_vars'])],
            ["SAT子句數量", str(summary['results_summary']['sat_clauses'])]
        ]
        
        table = Table(exec_info, colWidths=[5*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
        
        # 方法比較
        story.append(Paragraph("二、方法比較", heading_style))
        
        method_data = [["方法", "解數量", "時間(秒)", "探索節點", "剪枝數量"]]
        for method_name, data in summary['method_comparison'].items():
            method_data.append([
                method_name.upper(),
                str(data['solutions']),
                f"{data['time_seconds']:.2f}",
                str(data['nodes_explored']),
                str(data['pruning_count'])
            ])
        
        method_table = Table(method_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm, 3*cm])
        method_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(method_table)
        story.append(Spacer(1, 0.5*cm))
        
        # 結論
        story.append(Paragraph("三、結論", heading_style))
        
        conclusion_para = Paragraph(
            f"<b>最終結論：</b>{summary['conclusion']}",
            ParagraphStyle('Conclusion', parent=styles['Normal'], fontSize=12, leading=20)
        )
        story.append(conclusion_para)
        story.append(Spacer(1, 0.3*cm))
        
        # 技術說明
        story.append(Paragraph("四、技術說明", heading_style))
        
        tech_notes = [
            "1. DFS擴展搜索：以10個已知解為起始節點，將搜索上限擴展至1000個解",
            "2. CP-SAT SolutionCollector：使用Google OR-Tools進行約束規劃，配置solution_limit=1000",
            "3. SAT DIMACS編碼：將符闔數獨編碼為CNF格式，變數數量約256×16=4096，可對接sharpSAT/Cachet",
            "4. 博弈優化：融合二進制遺傳算法、精英回溯、樹狀剪枝策略，探索多維解空間"
        ]
        
        for note in tech_notes:
            story.append(Paragraph(note, normal_style))
            story.append(Spacer(1, 0.1*cm))
        
        # 生成PDF
        doc.build(story)
        
        print(f"PDF報告已生成: {output_path}")
        return output_path


def main():
    """主函數"""
    print("=" * 70)
    print("符闔數獨整合求解框架 - 多方法精確計數")
    print("=" * 70)
    
    framework = IntegratedSolverFramework("sudoku_config.json")
    results = framework.run_all_methods()
    
    # 保存完整結果
    output_json = "integrated_solver_results.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n完整結果已保存至: {output_json}")
    
    # 生成PDF報告
    pdf_path = framework.generate_pdf_report()
    
    print(f"\nA4電子文檔報告已生成至: {pdf_path}")
    print("=" * 70)
    print(results['summary']['conclusion'])
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()
