#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU诊断工具 - 检查CUDA环境状态
"""

def check_gpu_environment():
    """检测GPU环境"""
    
    print("="*60)
    print("🔍 GPU/CUDA 环境诊断")
    print("="*60)
    
    results = {
        'cuda_available': False,
        'cupy_available': False,
        'gpu_detected': False,
        'gpu_count': 0,
        'gpu_name': None,
        'cuda_version': None,
        'driver_version': None,
        'recommendations': []
    }
    
    # 1. 检查CuPy
    print("\n1️⃣ 检查CuPy...")
    try:
        import cupy as cp
        print(f"   ✅ CuPy已安装: {cp.__version__}")
        results['cupy_available'] = True
    except ImportError as e:
        print(f"   ❌ CuPy未安装: {e}")
        results['recommendations'].append("安装CuPy: pip install cupy-cuda12x")
        return results
    
    # 2. 检查CUDA Runtime
    print("\n2️⃣ 检查CUDA Runtime...")
    try:
        from cupy_backends.cuda.api import runtime
        cuda_version = runtime.runtimeGetVersion()
        print(f"   ✅ CUDA Runtime版本: {cuda_version // 1000}.{cuda_version % 1000}")
        results['cuda_version'] = f"{cuda_version // 1000}.{cuda_version % 1000}"
    except Exception as e:
        print(f"   ⚠️ CUDA Runtime不可用: {e}")
        results['recommendations'].append("安装CUDA Toolkit或更新NVIDIA驱动")
        return results
    
    # 3. 检查GPU设备
    print("\n3️⃣ 检查GPU设备...")
    try:
        device_count = runtime.getDeviceCount()
        results['gpu_count'] = device_count
        
        if device_count > 0:
            print(f"   ✅ 检测到 {device_count} 个GPU")
            results['gpu_detected'] = True
            
            for i in range(min(device_count, 4)):
                device = cp.cuda.Device(i)
                print(f"   📺 GPU {i}: {device.name}")
                print(f"       计算能力: {device.compute_capability}")
                print(f"       显存: {device.total_memory / 1024 / 1024:.1f} MB")
                if i == 0:
                    results['gpu_name'] = device.name
        else:
            print("   ❌ 未检测到GPU设备")
            results['recommendations'].append("检查NVIDIA显卡是否正确安装")
            
    except Exception as e:
        print(f"   ❌ GPU设备检测失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        
        error_str = str(e).lower()
        if 'insufficient' in error_str or 'driver' in error_str:
            results['recommendations'].append("🔴 驱动版本不足 - 请升级NVIDIA驱动至CUDA 12.x支持版本")
            results['recommendations'].append("   下载: https://www.nvidia.com/Download/index.aspx")
        elif 'no device' in error_str or 'not found' in error_str:
            results['recommendations'].append("🔴 未检测到NVIDIA GPU - 请检查显卡是否正确安装")
        else:
            results['recommendations'].append(f"🔴 未知错误: {e}")
    
    # 4. 检查nvidia-smi
    print("\n4️⃣ 检查nvidia-smi...")
    import subprocess
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,driver_version,memory.total --format=csv'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("   ✅ nvidia-smi可用")
            print(f"   输出: {result.stdout[:200]}")
        else:
            print(f"   ⚠️ nvidia-smi失败: {result.stderr[:100]}")
    except FileNotFoundError:
        print("   ⚠️ nvidia-smi未找到 (驱动可能未安装)")
        results['recommendations'].append("安装或重新安装NVIDIA驱动")
    except Exception as e:
        print(f"   ⚠️ 错误: {e}")
    
    # 5. 总结
    print("\n" + "="*60)
    print("📊 诊断结果")
    print("="*60)
    
    if results['gpu_detected'] and results['cuda_version']:
        print("✅ GPU环境就绪!")
        results['cuda_available'] = True
        print("   可以运行CUDA加速的数独求解器")
    else:
        print("❌ GPU环境未就绪")
        print("\n💡 建议操作:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    print("\n" + "="*60)
    
    return results


if __name__ == "__main__":
    import json
    results = check_gpu_environment()
    
    # 保存诊断报告
    report_path = "GPU_环境诊断报告.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 诊断报告已保存: {report_path}")
