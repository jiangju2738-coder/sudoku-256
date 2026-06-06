import ast
import sys

files = ['fusion_engine_v1.py', 'neural_fusion_v1.py', 'slime_mold_optimizer_v1.py', 'strategy_router_v1.py', 'run_fusion_search.py']

for fname in files:
    try:
        with open(fname, 'r') as f:
            code = f.read()
        ast.parse(code)
        print(f"✅ {fname}")
    except SyntaxError as e:
        print(f"❌ {fname} Line {e.lineno}: {e.msg}")
        # 显示错误行
        lines = code.split('\n')
        if e.lineno and e.lineno <= len(lines):
            print(f"   -> {lines[e.lineno-1][:80]}")
    except Exception as e:
        print(f"❌ {fname} {type(e).__name__}: {e}")
