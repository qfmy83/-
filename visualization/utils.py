"""
可视化工具模块 - 通用函数和配色方案
"""

import os
import pandas as pd

# 输出目录
PROJECT_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(PROJECT_HOME, "output", "csv")
HTML_DIR = os.path.join(PROJECT_HOME, "output", "html")

# 确保输出目录存在
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

# 统一配色方案
COLORS = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#73c0de", "#3ba272", "#fc8452", "#9a60b4",
    "#ea7ccc", "#48b8d0"
]

# 行为类型中文映射
BEHAVIOR_MAP = {
    "pv": "浏览",
    "fav": "收藏",
    "cart": "加购",
    "buy": "购买",
}


def load_csv(filename):
    """从 CSV 目录加载数据"""
    filepath = os.path.join(CSV_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV 文件不存在: {filepath}\n请先运行分析程序。")
    return pd.read_csv(filepath)


def save_html(chart, filename):
    """保存图表到 HTML"""
    filepath = os.path.join(HTML_DIR, filename)
    chart.render(filepath)
    print(f"  → 已保存: {filepath}")
    return filepath
