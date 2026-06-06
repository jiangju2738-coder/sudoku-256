#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理自动化脚本

功能：
1. 从多种数据源读取数据（CSV、JSON、Excel、SQLite）
2. 数据清洗管道（去重、缺失值处理、类型转换、异常值检测）
3. 数据转换与聚合（分组统计、透视表、时间序列重采样）
4. 生成 HTML 格式的数据质量报告（含统计摘要、数据分布图表）
5. 支持命令行参数配置（argparse）
6. 完整的日志记录和错误处理
7. 使用 dataclasses 定义配置模型

依赖：pandas, openpyxl
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
import warnings

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from openpyxl import load_workbook
except ImportError as e:
    print(f"错误: 缺少必要的依赖包 - {e}")
    print("请安装: pip install pandas openpyxl")
    sys.exit(1)


# ============================================================================
# 配置模型 (Dataclasses)
# ============================================================================

@dataclass
class DataSourceConfig:
    """数据源配置"""
    file_path: str
    data_type: str = 'csv'  # csv, json, excel, sqlite
    encoding: str = 'utf-8'
    sheet_name: Optional[str] = None
    sql_query: Optional[str] = None
    db_table: Optional[str] = None


@dataclass
class CleaningConfig:
    """数据清洗配置"""
    drop_duplicates: bool = True
    handle_missing: str = 'drop'  # drop, fill_mean, fill_median, fill_mode, fill_zero
    numeric_fill_value: float = 0.0
    categorical_fill_value: str = 'Unknown'
    detect_outliers: bool = True
    outlier_method: str = 'iqr'  # iqr, zscore
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0
    remove_outliers: bool = True
    convert_types: bool = True
    strip_whitespace: bool = True


@dataclass
class TransformationConfig:
    """数据转换配置"""
    group_by_columns: Optional[List[str]] = None
    group_by_aggregations: Optional[Dict[str, List[str]]] = None
    create_pivot: bool = False
    pivot_table_config: Optional[Dict[str, Any]] = None
    resample_frequency: Optional[str] = None
    resample_column: Optional[str] = None
    resample_aggregation: str = 'mean'


@dataclass
class ReportConfig:
    """报告生成配置"""
    output_dir: str = 'output'
    report_name: str = 'data_quality_report'
    include_charts: bool = True
    chart_types: List[str] = field(default_factory=lambda: ['distribution', 'correlation', 'missing_values'])
    save_data: bool = True
    saved_data_format: str = 'excel'  # excel, csv, json


@dataclass
class ProcessingConfig:
    """主处理配置"""
    data_source: DataSourceConfig
    cleaning: CleaningConfig
    transformation: TransformationConfig
    report: ReportConfig
    log_file: str = 'data_processor.log'
    log_level: str = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(log_file: str, log_level: str = 'INFO') -> logging.Logger:
    """设置日志系统"""
    logger = logging.getLogger('DataProcessor')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 文件处理器
    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"无法创建日志文件 {log_file}: {e}")
    
    return logger


# ============================================================================
# 数据读取模块
# ============================================================================

class DataReader:
    """多数据源读取器"""
    
    def __init__(self, config: DataSourceConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def read(self) -> pd.DataFrame:
        """读取数据"""
        self.logger.info(f"开始读取数据源: {self.config.file_path}")
        
        try:
            if self.config.data_type == 'csv':
                return self._read_csv()
            elif self.config.data_type == 'json':
                return self._read_json()
            elif self.config.data_type == 'excel':
                return self._read_excel()
            elif self.config.data_type == 'sqlite':
                return self._read_sqlite()
            else:
                raise ValueError(f"不支持的数据类型: {self.config.data_type}")
        except Exception as e:
            self.logger.error(f"读取数据失败: {e}")
            raise
    
    def _read_csv(self) -> pd.DataFrame:
        """读取CSV文件"""
        if not os.path.exists(self.config.file_path):
            raise FileNotFoundError(f"文件不存在: {self.config.file_path}")
        
        self.logger.info(f"读取CSV文件: {self.config.file_path}")
        df = pd.read_csv(self.config.file_path, encoding=self.config.encoding)
        self.logger.info(f"CSV文件读取成功，共 {len(df)} 行, {len(df.columns)} 列")
        return df
    
    def _read_json(self) -> pd.DataFrame:
        """读取JSON文件"""
        if not os.path.exists(self.config.file_path):
            raise FileNotFoundError(f"文件不存在: {self.config.file_path}")
        
        self.logger.info(f"读取JSON文件: {self.config.file_path}")
        
        with open(self.config.file_path, 'r', encoding=self.config.encoding) as f:
            data = json.load(f)
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.json_normalize(data)
        
        self.logger.info(f"JSON文件读取成功，共 {len(df)} 行, {len(df.columns)} 列")
        return df
    
    def _read_excel(self) -> pd.DataFrame:
        """读取Excel文件"""
        if not os.path.exists(self.config.file_path):
            raise FileNotFoundError(f"文件不存在: {self.config.file_path}")
        
        self.logger.info(f"读取Excel文件: {self.config.file_path}")
        
        sheet_name = self.config.sheet_name if self.config.sheet_name else 0
        df = pd.read_excel(self.config.file_path, sheet_name=sheet_name, engine='openpyxl')
        
        self.logger.info(f"Excel文件读取成功，共 {len(df)} 行, {len(df.columns)} 列，工作表: {sheet_name}")
        return df
    
    def _read_sqlite(self) -> pd.DataFrame:
        """读取SQLite数据库"""
        if not os.path.exists(self.config.file_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.config.file_path}")
        
        self.logger.info(f"读取SQLite数据库: {self.config.file_path}")
        
        if self.config.sql_query:
            query = self.config.sql_query
        elif self.config.db_table:
            query = f"SELECT * FROM {self.config.db_table}"
        else:
            raise ValueError("SQLite数据源需要指定 sql_query 或 db_table")
        
        try:
            conn = sqlite3.connect(self.config.file_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            self.logger.info(f"SQLite查询成功，共 {len(df)} 行, {len(df.columns)} 列")
            return df
        except Exception as e:
            self.logger.error(f"SQLite查询失败: {e}")
            raise


# ============================================================================
# 数据清洗模块
# ============================================================================

class DataCleaner:
    """数据清洗管道"""
    
    def __init__(self, config: CleaningConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.cleaning_stats = {}
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行数据清洗"""
        original_shape = df.shape
        self.logger.info(f"开始数据清洗，原始数据: {original_shape[0]} 行, {original_shape[1]} 列")
        
        # 1. 去重
        if self.config.drop_duplicates:
            df = self._drop_duplicates(df)
        
        # 2. 缺失值处理
        df = self._handle_missing_values(df)
        
        # 3. 数据类型转换
        if self.config.convert_types:
            df = self._convert_data_types(df)
        
        # 4. 字符串清洗
        if self.config.strip_whitespace:
            df = self._strip_whitespace(df)
        
        # 5. 异常值检测与处理
        if self.config.detect_outliers:
            df = self._handle_outliers(df)
        
        final_shape = df.shape
        self.logger.info(f"数据清洗完成，最终数据: {final_shape[0]} 行, {final_shape[1]} 列")
        self.logger.info(f"删除了 {original_shape[0] - final_shape[0]} 行数据")
        
        return df
    
    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """删除重复行"""
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        removed = before - after
        self.cleaning_stats['duplicates_removed'] = removed
        self.logger.info(f"删除重复行: {removed} 行")
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        missing_before = df.isnull().sum()
        total_missing = missing_before.sum()
        self.cleaning_stats['missing_before'] = int(total_missing)
        self.logger.info(f"缺失值统计: {total_missing} 个缺失值")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        for col in df.columns:
            if df[col].isnull().any():
                if col in numeric_cols:
                    if self.config.handle_missing == 'drop':
                        df = df.dropna(subset=[col])
                    elif self.config.handle_missing == 'fill_mean':
                        df[col] = df[col].fillna(df[col].mean())
                    elif self.config.handle_missing == 'fill_median':
                        df[col] = df[col].fillna(df[col].median())
                    else:
                        df[col] = df[col].fillna(self.config.numeric_fill_value)
                elif col in categorical_cols:
                    if self.config.handle_missing == 'drop':
                        df = df.dropna(subset=[col])
                    elif self.config.handle_missing == 'fill_mode':
                        mode_val = df[col].mode()
                        df[col] = df[col].fillna(mode_val[0] if not mode_val.empty else self.config.categorical_fill_value)
                    else:
                        df[col] = df[col].fillna(self.config.categorical_fill_value)
        
        missing_after = df.isnull().sum().sum()
        self.cleaning_stats['missing_after'] = int(missing_after)
        self.logger.info(f"缺失值处理后: {missing_after} 个缺失值")
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """自动转换数据类型"""
        self.logger.info("开始数据类型转换")
        
        for col in df.columns:
            # 尝试转换为数字类型
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        # 尝试转换日期列
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                    if df[col].dtype != 'object':
                        date_columns.append(col)
                except:
                    pass
        
        if date_columns:
            self.logger.info(f"检测到日期列: {date_columns}")
        
        return df
    
    def _strip_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除字符串前后空格"""
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """检测和处理异常值"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_info = {}
        
        for col in numeric_cols:
            if self.config.outlier_method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - self.config.iqr_multiplier * IQR
                upper_bound = Q3 + self.config.iqr_multiplier * IQR
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
            elif self.config.outlier_method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = df[z_scores > self.config.zscore_threshold][col]
            else:
                continue
            
            outlier_info[col] = {
                'count': len(outliers),
                'percentage': len(outliers) / len(df) * 100 if len(df) > 0 else 0
            }
            
            if self.config.remove_outliers and len(outliers) > 0:
                if self.config.outlier_method == 'iqr':
                    mask = (df[col] >= lower_bound) & (df[col] <= upper_bound)
                else:
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    mask = z_scores <= self.config.zscore_threshold
                df = df[mask]
        
        self.cleaning_stats['outliers'] = outlier_info
        self.logger.info(f"检测到异常值统计: {json.dumps(outlier_info, ensure_ascii=False)}")
        return df
    
    def get_stats(self) -> Dict[str, Any]:
        """获取清洗统计信息"""
        return self.cleaning_stats


# ============================================================================
# 数据转换模块
# ============================================================================

class DataTransformer:
    """数据转换与聚合"""
    
    def __init__(self, config: TransformationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.transform_stats = {}
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行数据转换"""
        original_shape = df.shape
        self.logger.info(f"开始数据转换，当前数据: {original_shape}")
        
        # 1. 分组聚合
        if self.config.group_by_columns:
            df = self._group_by_aggregate(df)
        
        # 2. 透视表
        if self.config.create_pivot:
            df = self._create_pivot_table(df)
        
        # 3. 时间序列重采样
        if self.config.resample_frequency:
            df = self._resample_time_series(df)
        
        final_shape = df.shape
        self.logger.info(f"数据转换完成，最终数据: {final_shape}")
        return df
    
    def _group_by_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """分组聚合"""
        self.logger.info(f"分组聚合: 按 {self.config.group_by_columns} 分组")
        
        if not self.config.group_by_aggregations:
            # 默认对所有数值列求均值
            agg_dict = {col: 'mean' for col in df.select_dtypes(include=[np.number]).columns}
        else:
            agg_dict = self.config.group_by_aggregations
        
        try:
            df = df.groupby(self.config.group_by_columns).agg(agg_dict).reset_index()
            self.transform_stats['grouped_columns'] = self.config.group_by_columns
        except Exception as e:
            self.logger.warning(f"分组聚合失败: {e}，跳过此步骤")
        
        return df
    
    def _create_pivot_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建透视表"""
        if not self.config.pivot_table_config:
            self.logger.warning("透视表配置为空，跳过")
            return df
        
        try:
            df = pd.pivot_table(
                df,
                values=self.config.pivot_table_config.get('values'),
                index=self.config.pivot_table_config.get('index'),
                columns=self.config.pivot_table_config.get('columns'),
                aggfunc=self.config.pivot_table_config.get('aggfunc', 'mean'),
                fill_value=0
            ).reset_index()
            self.logger.info("透视表创建成功")
        except Exception as e:
            self.logger.warning(f"透视表创建失败: {e}")
        
        return df
    
    def _resample_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """时间序列重采样"""
        if not self.config.resample_column:
            self.logger.warning("未指定重采样列，跳过")
            return df
        
        try:
            df[self.config.resample_column] = pd.to_datetime(df[self.config.resample_column])
            df = df.set_index(self.config.resample_column)
            df = df.resample(self.config.resample_frequency).agg(self.config.resample_aggregation)
            df = df.reset_index()
            self.logger.info(f"时间序列重采样成功，频率: {self.config.resample_frequency}")
        except Exception as e:
            self.logger.warning(f"时间序列重采样失败: {e}")
        
        return df
    
    def get_stats(self) -> Dict[str, Any]:
        """获取转换统计信息"""
        return self.transform_stats


# ============================================================================
# 数据质量报告模块
# ============================================================================

class DataQualityReport:
    """数据质量报告生成器"""
    
    def __init__(self, config: ReportConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.report_data = {}
    
    def generate(self, 
                 df: pd.DataFrame,
                 cleaning_stats: Dict[str, Any],
                 transform_stats: Dict[str, Any]) -> str:
        """生成HTML报告"""
        self.logger.info("开始生成数据质量报告")
        
        # 收集数据
        self.report_data = {
            'summary': self._generate_summary(df),
            'columns': self._analyze_columns(df),
            'missing_values': self._analyze_missing(df),
            'statistics': self._generate_statistics(df),
            'cleaning_stats': cleaning_stats,
            'transform_stats': transform_stats,
            'df_shape': df.shape,
            'generate_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 生成HTML
        html_content = self._create_html_report(df)
        
        # 保存报告
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        report_path = os.path.join(self.config.output_dir, f"{self.config.report_name}.html")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"报告已保存: {report_path}")
        
        # 保存处理后的数据
        if self.config.save_data:
            self._save_processed_data(df)
        
        return report_path
    
    def _generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据摘要"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns
        datetime_cols = df.select_dtypes(include=['datetime64', 'datetimetz']).columns
        
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(categorical_cols),
            'datetime_columns': len(datetime_cols),
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
        }
    
    def _analyze_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析每列信息"""
        column_info = []
        
        for col in df.columns:
            col_data = df[col]
            info = {
                'name': col,
                'dtype': str(col_data.dtype),
                'non_null_count': col_data.notna().sum(),
                'null_count': col_data.isna().sum(),
                'null_percentage': round(col_data.isna().sum() / len(df) * 100, 2) if len(df) > 0 else 0,
                'unique_count': col_data.nunique(),
                'memory_usage': f"{col_data.memory_usage(deep=True) / 1024:.2f} KB"
            }
            
            # 添加数值列统计
            if pd.api.types.is_numeric_dtype(col_data):
                info['min'] = col_data.min()
                info['max'] = col_data.max()
                info['mean'] = round(col_data.mean(), 4)
                info['std'] = round(col_data.std(), 4)
                info['median'] = col_data.median()
            
            column_info.append(info)
        
        return column_info
    
    def _analyze_missing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析缺失值"""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        
        return {
            'total_missing': int(missing.sum()),
            'missing_by_column': {col: {'count': int(missing[col]), 'percentage': missing_pct[col]} 
                                   for col in missing.index if missing[col] > 0},
            'completely_missing_columns': list(missing[missing == len(df)].index)
        }
    
    def _generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成统计描述"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) == 0:
            return {}
        
        return {
            'count': numeric_df.count().to_dict(),
            'mean': numeric_df.mean().round(4).to_dict(),
            'std': numeric_df.std().round(4).to_dict(),
            'min': numeric_df.min().to_dict(),
            '25%': numeric_df.quantile(0.25).round(4).to_dict(),
            '50%': numeric_df.quantile(0.50).round(4).to_dict(),
            '75%': numeric_df.quantile(0.75).round(4).to_dict(),
            'max': numeric_df.max().to_dict()
        }
    
    def _create_html_report(self, df: pd.DataFrame) -> str:
        """创建HTML报告"""
        # 准备图表数据
        charts_js = ''
        if self.config.include_charts:
            charts_js = self._generate_chart_script(df)
        
        # 生成表格HTML
        columns_table = self._generate_columns_table()
        stats_table = self._generate_statistics_table()
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据质量报告 - {self.config.report_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        h2 {{
            color: #667eea;
            margin: 30px 0 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        h3 {{
            color: #555;
            margin: 20px 0 15px;
        }}
        .meta-info {{
            color: #888;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }}
        .missing-table {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .missing-table th, .missing-table td {{
            white-space: nowrap;
        }}
        .stats-table {{
            width: 100%;
            margin-top: 20px;
        }}
        .badges {{
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }}
        .badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-success {{ background: #10b981; color: white; }}
        .badge-warning {{ background: #f59e0b; color: white; }}
        .badge-danger {{ background: #ef4444; color: white; }}
        .badge-info {{ background: #3b82f6; color: white; }}
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 数据质量报告</h1>
        <div class="meta-info">
            生成时间: {self.report_data['generate_time']} | 
            数据维度: {self.report_data['df_shape'][0]} 行 × {self.report_data['df_shape'][1]} 列
        </div>
        
        <div class="badges">
            <span class="badge badge-success">清洗完成</span>
            <span class="badge badge-info">转换完成</span>
            <span class="badge badge-warning">报告生成</span>
        </div>
        
        <h2>📈 数据摘要</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{self.report_data['summary']['total_rows']:,}</div>
                <div class="label">总行数</div>
            </div>
            <div class="summary-card">
                <div class="value">{self.report_data['summary']['total_columns']}</div>
                <div class="label">总列数</div>
            </div>
            <div class="summary-card">
                <div class="value">{self.report_data['summary']['numeric_columns']}</div>
                <div class="label">数值型列</div>
            </div>
            <div class="summary-card">
                <div class="value">{self.report_data['summary']['categorical_columns']}</div>
                <div class="label">类别型列</div>
            </div>
            <div class="summary-card">
                <div class="value">{self.report_data['summary']['memory_usage']}</div>
                <div class="label">内存占用</div>
            </div>
        </div>
        
        <h2>📋 列信息详情</h2>
        {columns_table}
        
        <h2>⚠️ 缺失值分析</h2>
        {self._generate_missing_section()}
        
        <h2>📊 数值统计描述</h2>
        {stats_table}
        
        <h2>🧹 数据清洗统计</h2>
        {self._generate_cleaning_stats()}
        
        <h2>🔄 数据转换统计</h2>
        {self._generate_transform_stats()}
        
        {charts_js}
    </div>
    
    <script>
        // 打印统计到控制台
        console.log('报告生成完成: {self.report_data["generate_time"]}');
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_columns_table(self) -> str:
        """生成列信息表格"""
        rows = ''
        for col in self.report_data['columns']:
            badge_class = 'badge-success' if col['null_percentage'] == 0 else 'badge-warning' if col['null_percentage'] < 5 else 'badge-danger'
            rows += f'''
            <tr>
                <td>{col['name']}</td>
                <td>{col['dtype']}</td>
                <td>{col['non_null_count']:,}</td>
                <td>{col['null_count']}</td>
                <td><span class="badge {badge_class}">{col['null_percentage']}%</span></td>
                <td>{col['unique_count']:,}</td>
            </tr>'''
        
        return f'''
        <div class="missing-table">
            <table>
                <thead>
                    <tr>
                        <th>列名</th>
                        <th>数据类型</th>
                        <th>非空值</th>
                        <th>缺失值</th>
                        <th>缺失率</th>
                        <th>唯一值</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''
    
    def _generate_statistics_table(self) -> str:
        """生成统计表格"""
        if not self.report_data['statistics']:
            return '<p>没有数值型列可供统计</p>'
        
        stats = self.report_data['statistics']
        headers = '<tr><th>统计量</th>' + '<th>'.join([f'<span style="display:none">{col}</span>' + col for col in stats['count'].keys()]) + '</th></tr>'
        
        rows = ''
        for stat in ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']:
            row = f'<tr><td><b>{stat}</b></td>'
            for col in stats[stat].keys():
                row += f'<td>{stats[stat][col]:,.4f}</td>'
            row += '</tr>'
            rows += row
        
        return f'''
        <table class="stats-table">
            <thead>
                {headers}
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''
    
    def _generate_missing_section(self) -> str:
        """生成缺失值分析区域"""
        missing = self.report_data['missing_values']
        
        if missing['total_missing'] == 0:
            return '''<div class="summary-grid">
                <div class="summary-card" style="background: linear-gradient(135deg, #10b981 0%, #34d399 100%);">
                    <div class="value">✅</div>
                    <div class="label">无缺失值</div>
                </div>
            </div>'''
        
        rows = ''
        for col, info in missing['missing_by_column'].items():
            rows += f'<tr><td>{col}</td><td>{info["count"]:,}</td><td>{info["percentage"]}%</td></tr>'
        
        return f'''
        <div class="summary-grid">
            <div class="summary-card" style="background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);">
                <div class="value">{missing["total_missing"]:,}</div>
                <div class="label">总缺失值</div>
            </div>
            <div class="summary-card" style="background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);">
                <div class="value">{len(missing["missing_by_column"])}</div>
                <div class="label">缺失列数</div>
            </div>
        </div>
        <div class="missing-table">
            <table>
                <thead>
                    <tr>
                        <th>列名</th>
                        <th>缺失数量</th>
                        <th>缺失百分比</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''
    
    def _generate_cleaning_stats(self) -> str:
        """生成清洗统计"""
        stats = self.report_data['cleaning_stats']
        if not stats:
            return '<p>无清洗统计信息</p>'
        
        content = '<ul>'
        if 'duplicates_removed' in stats:
            content += f'<li>删除重复行: <b>{stats["duplicates_removed"]}</b> 行</li>'
        if 'missing_before' in stats and 'missing_after' in stats:
            content += f'<li>缺失值处理: {stats["missing_before"]:,} → {stats["missing_after"]:,} (减少 {stats["missing_before"] - stats["missing_after"]:,})</li>'
        if 'outliers' in stats:
            content += f'<li>异常值检测: {len(stats["outliers"])} 列存在异常值</li>'
        content += '</ul>'
        return content
    
    def _generate_transform_stats(self) -> str:
        """生成转换统计"""
        stats = self.report_data['transform_stats']
        if not stats:
            return '<p>无转换统计信息</p>'
        
        content = '<ul>'
        if 'grouped_columns' in stats:
            content += f'<li>分组聚合: 按 {", ".join(stats["grouped_columns"])} 分组</li>'
        content += '</ul>'
        return content
    
    def _generate_chart_script(self, df: pd.DataFrame) -> str:
        """生成图表脚本"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return ''
        
        charts = []
        for col in numeric_cols[:6]:  # 最多6个图表
            charts.append(f'''
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h4>{col} 分布</h4>
                <div class="chart-container">
                    <canvas id="chart_{col}"></canvas>
                </div>
            </div>''')
            
        chart_js = '\n'.join(charts)
        
        js_charts = []
        for col in numeric_cols[:6]:
            # 创建直方图数据
            hist, bin_edges = np.histogram(df[col].dropna(), bins=20)
            labels = [f'{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}' for i in range(len(hist))]
            data = hist.tolist()
            
            js_charts.append(f'''
        new Chart(document.getElementById('chart_{col}'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: '频数',
                    data: {json.dumps(data)},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});''')
        
        return f'''
    <h2>📊 数据分布图表</h2>
    <div class="charts-grid">
        {chart_js}
    </div>
    
    <script>
        {chr(10).join(js_charts)}
    </script>'''
    
    def _save_processed_data(self, df: pd.DataFrame):
        """保存处理后的数据"""
        output_dir = self.config.output_dir
        
        if self.config.saved_data_format == 'excel':
            output_file = os.path.join(output_dir, f"{self.config.report_name}_processed.xlsx")
            df.to_excel(output_file, index=False, engine='openpyxl')
            self.logger.info(f"处理后数据已保存: {output_file}")
        elif self.config.saved_data_format == 'csv':
            output_file = os.path.join(output_dir, f"{self.config.report_name}_processed.csv")
            df.to_csv(output_file, index=False, encoding='utf-8')
            self.logger.info(f"处理后数据已保存: {output_file}")
        elif self.config.saved_data_format == 'json':
            output_file = os.path.join(output_dir, f"{self.config.report_name}_processed.json")
            df.to_json(output_file, orient='records', force_ascii=False, indent=2)
            self.logger.info(f"处理后数据已保存: {output_file}")


# ============================================================================
# 主处理管道
# ============================================================================

class DataProcessingPipeline:
    """数据处理主管道"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = setup_logging(config.log_file, config.log_level)
        self.reader = DataReader(config.data_source, self.logger)
        self.cleaner = DataCleaner(config.cleaning, self.logger)
        self.transformer = DataTransformer(config.transformation, self.logger)
        self.reporter = DataQualityReport(config.report, self.logger)
    
    def run(self) -> str:
        """执行完整处理管道"""
        self.logger.info("=" * 60)
        self.logger.info("开始数据处理自动化流程")
        self.logger.info("=" * 60)
        
        try:
            # 1. 读取数据
            df = self.reader.read()
            
            # 2. 数据清洗
            df = self.cleaner.clean(df)
            
            # 3. 数据转换
            df = self.transformer.transform(df)
            
            # 4. 生成报告
            report_path = self.reporter.generate(
                df,
                self.cleaner.get_stats(),
                self.transformer.get_stats()
            )
            
            self.logger.info("=" * 60)
            self.logger.info("数据处理完成！")
            self.logger.info(f"报告地址: {report_path}")
            self.logger.info("=" * 60)
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"处理流程失败: {e}", exc_info=True)
            raise


# ============================================================================
# 命令行参数解析
# ============================================================================

def parse_args() -> ProcessingConfig:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='数据处理自动化脚本 - 支持CSV、JSON、Excel、SQLite多种数据源',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本用法
  python data_processor_automation.py --input data.csv
  
  # 处理Excel文件
  python data_processor_automation.py --input data.xlsx --type excel
  
  # 处理SQLite数据库
  python data_processor_automation.py --input database.sqlite --type sqlite --db-table users
  
  # 自定义清洗选项
  python data_processor_automation.py --input data.csv --drop-duplicates --fill-missing mean
  
  # 生成分组统计
  python data_processor_automation.py --input data.csv --group-by category --aggregate mean:sum
        '''
    )
    
    # 数据源参数
    parser.add_argument('--input', '-i', required=True, help='输入文件/数据库路径')
    parser.add_argument('--type', '-t', choices=['csv', 'json', 'excel', 'sqlite'], 
                       default='csv', help='数据类型 (默认: csv)')
    parser.add_argument('--encoding', '-e', default='utf-8', help='文件编码 (默认: utf-8)')
    parser.add_argument('--sheet', '-s', help='Excel工作表名称')
    parser.add_argument('--db-table', '-dt', help='SQLite表名')
    parser.add_argument('--sql-query', '-q', help='自定义SQL查询')
    
    # 清洗参数
    parser.add_argument('--no-dedup', action='store_true', help='不禁用去重')
    parser.add_argument('--fill-missing', choices=['drop', 'mean', 'median', 'mode', 'zero'],
                       default='drop', help='缺失值填充策略 (默认: drop)')
    parser.add_argument('--numeric-fill', type=float, default=0.0, help='数值型填充值')
    parser.add_argument('--categorical-fill', type=str, default='Unknown', help='类别型填充值')
    parser.add_argument('--no-outlier-detection', action='store_true', help='禁用异常值检测')
    parser.add_argument('--no-type-conversion', action='store_true', help='禁用类型转换')
    parser.add_argument('--no-whitespace-strip', action='store_true', help='禁用空格清理')
    
    # 转换参数
    parser.add_argument('--group-by', '-g', nargs='+', help='分组列')
    parser.add_argument('--aggregate', '-a', nargs='+', help='聚合操作 (格式: 列:聚合函数)')
    parser.add_argument('--pivot', '-p', action='store_true', help='创建透视表')
    parser.add_argument('--pivot-values', help='透视表值列')
    parser.add_argument('--pivot-index', help='透视表索引列')
    parser.add_argument('--pivot-columns', help='透视表列列')
    parser.add_argument('--resample', '-r', help='时间序列重采样频率 (如: D, W, M)')
    parser.add_argument('--resample-column', help='重采样时间列')
    
    # 报告参数
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录')
    parser.add_argument('--report-name', '-n', default='data_quality_report', help='报告名称')
    parser.add_argument('--no-charts', action='store_true', help='不生成图表')
    parser.add_argument('--save-data', action='store_true', help='保存处理后的数据')
    parser.add_argument('--save-format', choices=['excel', 'csv', 'json'], default='excel',
                       help='保存格式 (默认: excel)')
    
    # 日志参数
    parser.add_argument('--log-file', '-l', default='data_processor.log', help='日志文件')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       default='INFO', help='日志级别')
    
    args = parser.parse_args()
    
    # 构建配置对象
    data_source = DataSourceConfig(
        file_path=args.input,
        data_type=args.type,
        encoding=args.encoding,
        sheet_name=args.sheet,
        sql_query=args.sql_query,
        db_table=args.db_table
    )
    
    cleaning = CleaningConfig(
        drop_duplicates=not args.no_dedup,
        handle_missing=args.fill_missing,
        numeric_fill_value=args.numeric_fill,
        categorical_fill_value=args.categorical_fill,
        detect_outliers=not args.no_outlier_detection,
        remove_outliers=True,
        convert_types=not args.no_type_conversion,
        strip_whitespace=not args.no_whitespace_strip
    )
    
    transformation = TransformationConfig(
        group_by_columns=args.group_by,
        group_by_aggregations=parse_aggregations(args.aggregate) if args.aggregate else None,
        create_pivot=args.pivot,
        pivot_table_config=build_pivot_config(args) if args.pivot else None,
        resample_frequency=args.resample,
        resample_column=args.resample_column,
        resample_aggregation='mean'
    )
    
    report = ReportConfig(
        output_dir=args.output_dir,
        report_name=args.report_name,
        include_charts=not args.no_charts,
        save_data=args.save_data,
        saved_data_format=args.save_format
    )
    
    return ProcessingConfig(
        data_source=data_source,
        cleaning=cleaning,
        transformation=transformation,
        report=report,
        log_file=args.log_file,
        log_level=args.log_level
    )


def parse_aggregations(agg_args: List[str]) -> Dict[str, List[str]]:
    """解析聚合参数"""
    aggregations = {}
    for arg in agg_args:
        if ':' in arg:
            col, func = arg.split(':', 1)
            if col not in aggregations:
                aggregations[col] = []
            aggregations[col].append(func)
    return aggregations


def build_pivot_config(args: argparse.Namespace) -> Dict[str, Any]:
    """构建透视表配置"""
    config = {}
    if args.pivot_values:
        config['values'] = args.pivot_values
    if args.pivot_index:
        config['index'] = args.pivot_index
    if args.pivot_columns:
        config['columns'] = args.pivot_columns
    return config


# ============================================================================
# 入口点
# ============================================================================

def main():
    """主入口"""
    config = parse_args()
    pipeline = DataProcessingPipeline(config)
    
    try:
        report_path = pipeline.run()
        print(f"\n✅ 处理完成！报告已生成: {report_path}")
        return 0
    except Exception as e:
        print(f"\n❌ 处理失败: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
