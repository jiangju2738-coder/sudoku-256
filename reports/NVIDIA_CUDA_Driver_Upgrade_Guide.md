# NVIDIA GPU + CUDA 12.x 驱动升级指南
# 超级256数独系统 GPU加速准备
#
# 作者: Jualius
# 日期: 2026-05-30

"""
============================================
🔍 当前状态诊断
============================================

✅ CuPy 已安装 (v14.1.0)
❌ CUDA 驱动不可用
❌ 无法检测到NVIDIA GPU设备

错误信息:
- "CUDA path could not be detected"
- "cudaErrorInsufficientDriver"

============================================
📋 升级步骤
============================================

步骤 1: 确认NVIDIA GPU型号
--------------------------------------------
在Windows上运行以下命令之一:

选项A - 设备管理器:
1. Win+X → 设备管理器
2. 展开"显示适配器"
3. 查看NVIDIA GPU型号

选项B - PowerShell:
 powershell -Command "Get-WmiObject Win32_VideoController | Select Name, DriverVersion"

选项C - 系统信息:
 msinfo32 → 组件 → 显示

常见型号示例:
- NVIDIA GeForce RTX 3060 / 3070 / 3080 / 3090
- NVIDIA GeForce RTX 4060 / 4070 / 4080 / 4090
- NVIDIA Tesla T4 / V100 / A100 (数据中心)
- NVIDIA Quadro RTX 系列

--------------------------------------------

步骤 2: 下载最新NVIDIA驱动
--------------------------------------------
官方下载地址:
https://www.nvidia.com/Download/index.aspx

或手动选择:
- 产品类型: GeForce / RTX / Quadro / Tesla
- 产品系列: [根据步骤1选择]
- 操作系统: Windows 10/11 64-bit
- 驱动类型: Game Ready Driver 或 Studio Driver
- 语言: 中文

推荐: 直接下载最新"Game Ready Driver"

示例 (RTX 3080):
  https://www.nvidia.com/download/driverResults.aspx/199922/en-us/

--------------------------------------------

步骤 3: 安装NVIDIA驱动
--------------------------------------------
1. 关闭所有应用程序
2. 运行下载的.exe安装程序
3. 选择"自定义安装"
4. ✅ 勾选"NVIDIA显卡驱动程序"
5. ✅ 勾选"Express安装"或"自定义安装"
6. 点击"下一步"并完成安装
7. **重要: 重启计算机**

安装后验证:
- 右键桌面 → NVIDIA控制面板
- 或: nvidia-smi (命令行)

--------------------------------------------

步骤 4: (可选) 安装CUDA Toolkit 12.x
--------------------------------------------
CuPy 14.1.0 自带CUDA运行时，无需单独安装CUDA Toolkit。

如需完整CUDA开发环境:
https://developer.nvidia.com/cuda-downloads

选择:
- 操作系统: Windows
- 架构: x86_64
- 版本: Windows 10/11
- CUDA Toolkit: 12.x (推荐 12.6 或 12.8)

安装后添加环境变量:
  CUDA_PATH = C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x

--------------------------------------------

步骤 5: 验证CUDA环境
--------------------------------------------
打开新的命令提示符或PowerShell:

# 检查驱动版本
nvidia-smi

预期输出示例:
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 551.23     Driver Version: 551.23    CUDA Version: 12.4         |
|----------------------------|----------------------+----------------------+
| GPU  Name        TCC/WDDM   | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap | Memory-Usage | GPU-Util  Compute M. |
|=============================|======================|======================|
|   0  NVIDIA GeForce ...  WDDM | 00000000:01:00.0  On |                  0 |
| 45%   52C    P2   85W / 320W |  1234MiB / 10240MiB |      3%      Default |
+-----------------------------------------------------------------------------+

# 检查CUDA版本
nvcc --version

# 测试CuPy
python -c "import cupy as cp; print('CuPy:', cp.__version__); print('GPU Count:', cp.cuda.runtime.getDeviceCount())"

--------------------------------------------

步骤 6: 重新运行验证
--------------------------------------------
驱动修复后，回到256数独系统目录:

cd D:\2026\WPF_Sudoku\Sudoku_256

# 运行集成验证
python rl_gpu_dlx_integration_v2.py

# 运行批量验证
python batch_benchmark_framework.py

预期输出:
✅ CuPy版本: 14.1.0
✅ 检测到 1 个GPU设备
✅ 主GPU: NVIDIA GeForce RTX 3080, 计算能力: 8.6
✅ GPU加速模式已激活 (CUDA)

============================================
⚠️ 常见问题排查
============================================

问题1: nvidia-smi 命令不存在
--------------------------------------------
解决方案: 驱动未安装或安装失败
1. 检查设备管理器中是否有黄色感叹号
2. 重新运行驱动安装程序
3. 选择"清洁安装"

问题2: cudaErrorInsufficientDriver
--------------------------------------------
解决方案: 驱动版本与CUDA不匹配
1. 确保安装的是最新驱动
2. 尝试"清洁安装"选项
3. 使用DDU工具完全卸载旧驱动后重装

问题3: 检测到多个GPU但CUDA不可用
--------------------------------------------
解决方案: 
1. 检查是否在虚拟环境中
2. 确保物理GPU已正确插入
3. 检查BIOS中GPU设置

问题4: CuPy找不到CUDA
--------------------------------------------
解决方案: 设置CUDA_PATH环境变量
Windows:
  系统属性 → 高级 → 环境变量
  新建: CUDA_PATH = C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6

============================================
🚀 GPU加速效果预期
============================================

对于16×16 (256宫格) 数独:

| 场景              | CPU时间     | GPU时间      | 加速比 |
|-------------------|-------------|--------------|--------|
| 标准谜题 (60提示) | 5-10秒      | 0.5-1秒      | 10-20× |
| 困难谜题 (30提示) | 超时        | 2-5秒        | N/A    |
| 极端困难 (15提示) | 不可解      | 10-30秒      | N/A    |

对于9×9 数独:
| 场景              | CPU时间     | GPU时间      | 加速比 |
|-------------------|-------------|--------------|--------|
| 标准谜题          | 0.1-0.5秒   | 0.01-0.05秒  | 10-20× |
| 困难谜题          | 1-5秒       | 0.1-0.5秒    | 10-20× |

============================================
📝 后续步骤
============================================

1. ✅ 完成驱动升级
2. ⬜ 重新运行验证确认GPU激活
3. ⬜ 执行完整批量基准测试 (10+谜题)
4. ⬜ 分析GPU加速性能数据
5. ⬜ 优化CUDA内核参数
6. ⬜ 集成到策略路由层

============================================
🔗 参考资源
============================================

- NVIDIA驱动下载: https://www.nvidia.com/Download/index.aspx
- CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
- CuPy文档: https://docs.cupy.dev/
- NVIDIA CUDA Zonal Guide: https://developer.nvidia.com/blog/cuda-toolkit-12-4-available-now/

"""
