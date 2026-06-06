# Data Processor Automation Skill

**用途**: 生成和维护数据处理自动化脚本，支持多数据源读取、清洗、转换和HTML报告生成。

## 核心功能

1. **多数据源读取**: CSV、JSON、Excel、SQLite
2. **数据清洗管道**: 去重、缺失值处理、类型转换、异常值检测
3. **数据转换聚合**: 分组统计、透视表、时间序列重采样
4. **HTML质量报告**: 统计摘要、分布图表、缺失值分析
5. **命令行配置**: 完整的argparse参数支持
6. **日志错误处理**: 结构化日志记录

## 使用方法

### 基本用法

```bash
# CSV文件处理
python data_processor_automation.py --input data.csv

# Excel文件处理
python data_processor_automation.py --input data.xlsx --type excel

# SQLite数据库处理
python data_processor_automation.py --input database.sqlite --type sqlite --db-table users

# 带清洗选项
python data_processor_automation.py --input data.csv --fill-missing mean --no-dedup

# 分组聚合
python data_processor_automation.py --input data.csv --group-by category gender --aggregate sales:sum,age:mean
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `--input, -i` | 输入文件路径（必需） |
| `--type, -t` | 数据类型: csv/json/excel/sqlite |
| `--fill-missing` | 缺失值策略: drop/mean/median/mode/zero |
| `--group-by` | 分组列名 |
| `--aggregate` | 聚合操作: 列:函数 |
| `--output-dir, -o` | 输出目录 |
| `--save-data` | 保存处理后数据 |
| `--log-level` | 日志级别 |

### 复杂场景示例

```bash
# 时间序列重采样
python data_processor_automation.py \
    --input sales_data.csv \
    --resample M \
    --resample-column date \
    --group-by region product \
    --aggregate sales:sum quantity:mean

# SQLite复杂查询
python data_processor_automation.py \
    --input database.sqlite \
    --type sqlite \
    --sql-query "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id" \
    --fill-missing zero \
    --save-data
```

## 数据结构

### 配置模型 (dataclasses)

```python
@dataclass
class DataSourceConfig:      # 数据源配置
@dataclass
class CleaningConfig:        # 清洗配置
@dataclass
class TransformationConfig:  # 转换配置
@dataclass
class ReportConfig:          # 报告配置
@dataclass
class ProcessingConfig:      # 主配置
```

### 处理流程

```
输入数据 → DataReader → DataCleaner → DataTransformer → DataQualityReport → HTML报告
```

## 输出文件

- `data_quality_report.html` - 交互式数据质量报告
- `data_quality_report_processed.xlsx` - 处理后的数据（可选）
- `data_processor.log` - 详细日志

## 维护要点

- 依赖包: pandas, openpyxl
- Python版本: 3.8+
- 扩展数据源需要实现新的 `_read_*` 方法
- 图表使用 Chart.js (CDN加载)
