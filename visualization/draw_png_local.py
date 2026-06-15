"""
Matplotlib 静态图表绘制工具
依赖：pip install matplotlib pandas squarify
用法：python visualization/draw_png_local.py
输出：output/png/01_*.png ~ 16_*.png
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

# Windows GBK 控制台兼容
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
import squarify

# ---------- 中文字体（Windows 优先 Microsoft YaHei） ----------
mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei', 'sans-serif']
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['figure.dpi'] = 100

# ---------- 路径 ----------
PROJECT_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(PROJECT_HOME, "output", "csv")
PNG_DIR = os.path.join(PROJECT_HOME, "output", "png")
os.makedirs(PNG_DIR, exist_ok=True)

# ---------- 配色（与 pyecharts 看板风格统一） ----------
COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
          '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5470c6']


def save(fig, name, w=12, h=6):
    """统一保存为高 DPI PNG"""
    fig.set_size_inches(w, h)
    fig.tight_layout()
    path = os.path.join(PNG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    size_kb = os.path.getsize(path) // 1024
    print(f"  [OK] {name:38s}  ({size_kb} KB)")


def load(csv_name):
    """读 CSV，返回 DataFrame"""
    path = os.path.join(CSV_DIR, csv_name)
    if not os.path.isfile(path):
        print(f"  [WARN] {csv_name} 不存在，跳过")
        return None
    return pd.read_csv(path)


# ===================================================================
# 主要图表
# ===================================================================

def chart_01_daily_pv_uv():
    """01 每日 PV/UV 趋势 - 双 Y 轴折线柱组合"""
    df = load("01_daily_pv_uv.csv")
    if df is None: return
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    x = df['event_date']
    bar = ax1.bar(x, df['pv'], color=COLORS[0], alpha=0.7, label='PV（浏览量）')
    line = ax2.plot(x, df['uv'], color=COLORS[3], marker='o', linewidth=2.5,
                    markersize=8, label='UV（独立访客）')
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('PV', fontsize=12, color=COLORS[0])
    ax2.set_ylabel('UV', fontsize=12, color=COLORS[3])
    ax1.tick_params(axis='y', labelcolor=COLORS[0])
    ax2.tick_params(axis='y', labelcolor=COLORS[3])
    plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')
    plt.title('每日 PV / UV 趋势', fontsize=15, fontweight='bold', pad=15)
    # 合并 legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')
    ax1.grid(axis='y', alpha=0.3)
    save(fig, "01_daily_pv_uv.png", 12, 6)


def chart_02_hourly_distribution():
    """02 24 小时活跃分布 - 柱+折线"""
    df = load("02_hourly_distribution.csv")
    if df is None: return
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    x = df['event_hour']
    ax1.bar(x, df['pv'], color=COLORS[0], alpha=0.75, label='PV')
    ax2.plot(x, df['buy_count'], color=COLORS[3], marker='s', linewidth=2.5,
             markersize=7, label='购买数')
    ax2.plot(x, df['cart_count'], color=COLORS[2], marker='^', linewidth=2,
             markersize=6, label='加购数')
    ax1.set_xlabel('小时（0-23）', fontsize=12)
    ax1.set_ylabel('PV', fontsize=12, color=COLORS[0])
    ax2.set_ylabel('购买 / 加购数', fontsize=12, color=COLORS[3])
    ax1.set_xticks(range(0, 24))
    plt.title('24 小时活跃分布（PV vs 购买/加购）', fontsize=15, fontweight='bold', pad=15)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')
    ax1.grid(axis='y', alpha=0.3)
    save(fig, "02_hourly_distribution.png", 13, 6)


def chart_03_behavior_funnel():
    """03 行为转化漏斗"""
    df = load("03_behavior_funnel.csv")
    if df is None: return
    fig, ax = plt.subplots()
    # 漏斗：横向条降序展示
    behaviors = df['behavior'].tolist()
    counts = df['user_count'].tolist()
    ratios = df['ratio'].tolist()
    y_pos = np.arange(len(behaviors))
    bars = ax.barh(y_pos, counts, color=COLORS[:len(behaviors)], alpha=0.85,
                   edgecolor='white', linewidth=2)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(behaviors, fontsize=12)
    ax.invert_yaxis()
    for i, (bar, cnt, r) in enumerate(zip(bars, counts, ratios)):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height()/2,
                f'{cnt:,}  ({r}%)', va='center', fontsize=11, fontweight='bold')
    ax.set_xlabel('用户数', fontsize=12)
    plt.title('用户行为转化漏斗', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlim(0, max(counts) * 1.18)
    ax.grid(axis='x', alpha=0.3)
    save(fig, "03_behavior_funnel.png", 11, 5)


def chart_04_top_items():
    """04 TOP 商品（综合评分） - 横向条形图"""
    df = load("04_top_items.csv").head(20)
    fig, ax = plt.subplots()
    df = df.iloc[::-1]  # 倒序让 TOP1 在最上
    bars = ax.barh(range(len(df)), df['total_score'], color=COLORS[0], alpha=0.85,
                   edgecolor='white')
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([f"#{int(r)} 商品{int(i)}" for r, i in
                        zip(df['ranking'], df['item_id'])], fontsize=10)
    for bar, score, buy in zip(bars, df['total_score'], df['buy_count']):
        ax.text(bar.get_width() + max(df['total_score']) * 0.01,
                bar.get_y() + bar.get_height()/2,
                f'综合={int(score)} / 购买={int(buy)}', va='center', fontsize=9)
    ax.set_xlabel('综合评分（pv×1 + fav×3 + cart×5 + buy×10）', fontsize=12)
    plt.title('TOP 20 热门商品', fontsize=15, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3)
    save(fig, "04_top_items.png", 12, 9)


def chart_05_top_categories():
    """05 TOP 类目 - 玫瑰图（极坐标条形）"""
    df = load("05_top_categories.csv").head(15)
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    N = len(df)
    theta = np.linspace(0, 2*np.pi, N, endpoint=False)
    width = 2*np.pi / N
    pvs = df['pv_count'].values
    colors_arr = plt.cm.viridis(np.linspace(0.15, 0.85, N))
    bars = ax.bar(theta, pvs, width=width, bottom=0, color=colors_arr,
                  edgecolor='white', linewidth=2, alpha=0.85)
    ax.set_xticks(theta)
    ax.set_xticklabels([f"#{int(r)}\n{int(cid)}" for r, cid in
                        zip(df['ranking'], df['category_id'])], fontsize=9)
    ax.set_yticklabels([])
    ax.set_title('TOP 15 热门类目（PV 玫瑰图）', fontsize=15, fontweight='bold', pad=25)
    save(fig, "05_top_categories.png", 10, 10)


def chart_06_weekday_weekend():
    """06 工作日 vs 周末 - 分组柱状图"""
    df = load("06_weekday_vs_weekend.csv")
    if df is None: return
    # 透视：行为为列
    pivot = df.pivot_table(index='day_type', columns='behavior',
                          values='total_count', aggfunc='sum').fillna(0)
    # 排序行为顺序
    order = ['pv', 'cart', 'fav', 'buy']
    cols = [c for c in order if c in pivot.columns] + [c for c in pivot.columns if c not in order]
    pivot = pivot[cols]
    # 重命名
    label_map = {'pv': '浏览', 'cart': '加购', 'fav': '收藏', 'buy': '购买'}
    pivot.columns = [label_map.get(c, c) for c in pivot.columns]
    pivot.index = ['工作日' if x == 'weekday' else '周末' for x in pivot.index]

    fig, ax = plt.subplots()
    pivot.plot(kind='bar', ax=ax, color=COLORS[:len(pivot.columns)],
              edgecolor='white', width=0.7)
    ax.set_xlabel('')
    ax.set_ylabel('行为总数', fontsize=12)
    ax.set_title('工作日 vs 周末：各类行为对比', fontsize=15, fontweight='bold', pad=15)
    plt.xticks(rotation=0)
    ax.legend(title='', loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    # 给柱顶加数据标签
    for c in ax.containers:
        ax.bar_label(c, fmt='%.0f', fontsize=8, padding=2)
    save(fig, "06_weekday_vs_weekend.png", 11, 6)


def chart_07_retention():
    """07 用户留存 - 折线图"""
    df = load("07_retention.csv")
    if df is None: return
    fig, ax = plt.subplots()
    x = df['first_date']
    cohorts = [c for c in ['day_1', 'day_2', 'day_3', 'day_7', 'day_14'] if c in df.columns]
    label_map = {'day_1': '次日留存', 'day_2': 'D+2 留存', 'day_3': 'D+3 留存',
                 'day_7': 'D+7 留存', 'day_14': 'D+14 留存'}
    markers = ['o', 's', '^', 'D', 'v']
    for i, col in enumerate(cohorts):
        ax.plot(x, df[col], marker=markers[i % len(markers)], linewidth=2.5,
               markersize=8, color=COLORS[i], label=label_map.get(col, col))
    ax.set_xlabel('首次访问日期', fontsize=12)
    ax.set_ylabel('留存率（%）', fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    ax.set_title('用户留存率曲线', fontsize=15, fontweight='bold', pad=15)
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    save(fig, "07_retention.png", 12, 6)


def chart_08_rfm():
    """08 RFM 用户分群 - 环形图"""
    df = load("08_rfm_summary.csv")
    if df is None: return
    fig, ax = plt.subplots()
    sizes = df['user_count'].values
    labels = df['segment'].values
    colors_arr = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_arr,
                                       autopct='%1.1f%%', startangle=90,
                                       pctdistance=0.82,
                                       wedgeprops=dict(width=0.42, edgecolor='white', linewidth=2),
                                       textprops=dict(fontsize=10))
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight('bold')
    total = sizes.sum()
    ax.text(0, 0, f'总用户\n{total:,}', ha='center', va='center',
            fontsize=14, fontweight='bold')
    ax.set_title('RFM 用户分群', fontsize=15, fontweight='bold', pad=15)
    save(fig, "08_rfm.png", 10, 8)


def chart_09_user_path():
    """09 用户行为路径 - 横向条形（替代桑基）"""
    df = load("09_user_path.csv").head(15)
    label_map = {'pv': '浏览', 'cart': '加购', 'fav': '收藏', 'buy': '购买'}
    df['path'] = df.apply(lambda r: f"{label_map.get(r['from_behavior'], r['from_behavior'])} → {label_map.get(r['to_behavior'], r['to_behavior'])}", axis=1)
    df = df.iloc[::-1]
    fig, ax = plt.subplots()
    bars = ax.barh(df['path'], df['path_count'], color=COLORS[1], alpha=0.85,
                   edgecolor='white')
    for bar, cnt, r in zip(bars, df['path_count'], df['path_ratio']):
        ax.text(bar.get_width() + max(df['path_count']) * 0.01,
                bar.get_y() + bar.get_height()/2,
                f'{int(cnt):,} ({r}%)', va='center', fontsize=10, fontweight='bold')
    ax.set_xlabel('路径出现次数', fontsize=12)
    ax.set_title('用户行为转移路径（TOP 15）', fontsize=15, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3)
    save(fig, "09_user_path.png", 12, 8)


def chart_10_category_conversion():
    """10 类目转化率 - 柱状+折线（这个图的 CSV 是 top_categories.csv 派生）"""
    df = load("05_top_categories.csv").head(15)
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    x = range(len(df))
    ax1.bar(x, df['pv_count'], color=COLORS[0], alpha=0.75, label='PV')
    ax2.plot(x, df['conversion_rate'], color=COLORS[3], marker='o', linewidth=2.5,
             markersize=8, label='转化率(%)')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"#{int(r)}\n{int(c)}" for r, c in
                         zip(df['ranking'], df['category_id'])], fontsize=9, rotation=0)
    ax1.set_xlabel('类目排名 / ID', fontsize=12)
    ax1.set_ylabel('PV', fontsize=12, color=COLORS[0])
    ax2.set_ylabel('转化率(%)', fontsize=12, color=COLORS[3])
    plt.title('TOP 15 类目：PV vs 转化率', fontsize=15, fontweight='bold', pad=15)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    save(fig, "10_category_conversion.png", 13, 6)


def chart_11_heatmap_hour_dow():
    """11 24h × 7d 行为热力图（buy_count）"""
    df = load("10_heatmap_hour_dow.csv")
    if df is None: return
    # day_of_week: 1=周日 ... 7=周六；event_hour: 0-23
    week_labels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    pivot = df.pivot_table(index='day_of_week', columns='event_hour',
                          values='buy_count', aggfunc='sum').fillna(0)
    # 保证 7×24
    full_index = list(range(1, 8))
    full_cols = list(range(0, 24))
    pivot = pivot.reindex(index=full_index, columns=full_cols, fill_value=0)
    fig, ax = plt.subplots(figsize=(15, 5))
    data = pivot.values
    im = ax.imshow(data, aspect='auto', cmap='YlOrRd', interpolation='nearest')
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h}:00" for h in range(24)], fontsize=9)
    ax.set_yticks(range(7))
    ax.set_yticklabels(week_labels, fontsize=10)
    # 数值标注
    vmax = data.max()
    for i in range(7):
        for j in range(24):
            v = int(data[i, j])
            if v > 0:
                color = 'white' if v > vmax * 0.55 else 'black'
                ax.text(j, i, str(v), ha='center', va='center',
                       fontsize=7, color=color)
    cbar = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label('购买数', fontsize=11)
    ax.set_xlabel('小时', fontsize=12)
    ax.set_ylabel('星期', fontsize=12)
    plt.title('24 小时 × 7 天 购买热力图（找下单黄金时段）', fontsize=15,
              fontweight='bold', pad=15)
    save(fig, "11_heatmap_hour_dow.png", 15, 5)


def chart_12_repurchase():
    """12 复购率分布 - 双柱（用户占比 vs 购买贡献占比）"""
    df = load("11_repurchase.csv").sort_values('bucket_order')
    fig, ax = plt.subplots()
    x = np.arange(len(df))
    w = 0.4
    b1 = ax.bar(x - w/2, df['user_ratio'], w, color=COLORS[0], alpha=0.85,
               label='用户数占比(%)', edgecolor='white')
    b2 = ax.bar(x + w/2, df['buy_contribution'], w, color=COLORS[3], alpha=0.85,
               label='购买量贡献(%)', edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(df['buy_times_bucket'], fontsize=10, rotation=15, ha='right')
    ax.set_xlabel('购买次数分桶', fontsize=12)
    ax.set_ylabel('百分比(%)', fontsize=12)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.title('用户复购率分布（验证二八定律）', fontsize=15, fontweight='bold', pad=15)
    for c in (b1, b2):
        ax.bar_label(c, fmt='%.1f%%', fontsize=9, padding=2)
    save(fig, "12_repurchase.png", 11, 6)


def chart_13_category_treemap():
    """13 类目 × 类目内商品 树状图"""
    df = load("12_category_top_items.csv")
    if df is None: return
    # 按类目分组，每个类目占大块；类目内商品占小块
    cats = df.groupby('category_id').agg(category_pv=('category_pv', 'first')).reset_index()
    cats = cats.sort_values('category_pv', ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(14, 8))
    sizes = cats['category_pv'].values
    labels = [f"类目 {int(c)}\nPV={int(p):,}" for c, p in
              zip(cats['category_id'], cats['category_pv'])]
    colors_arr = plt.cm.Pastel1(np.linspace(0, 1, len(cats)))
    squarify.plot(sizes=sizes, label=labels, color=colors_arr, alpha=0.85,
                  edgecolor='white', linewidth=2, ax=ax,
                  text_kwargs={'fontsize': 10, 'fontweight': 'bold'})
    ax.axis('off')
    plt.title('TOP 10 类目 PV 树状图', fontsize=15, fontweight='bold', pad=15)
    save(fig, "13_category_treemap.png", 14, 8)


# ===================================================================
# 扩展图表
# ===================================================================

def chart_14_behavior_pie():
    """14 行为分布饼图 - 直观看四种行为比例"""
    df = load("03_behavior_funnel.csv")
    if df is None: return
    fig, ax = plt.subplots()
    sizes = df['user_count'].values
    labels = df['behavior'].values
    explode = [0.02] * len(sizes)
    explode[-1] = 0.08  # 把最末"购买"突出
    colors_arr = COLORS[:len(sizes)]
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_arr,
                                       autopct='%1.2f%%', startangle=90,
                                       explode=explode, shadow=True,
                                       textprops=dict(fontsize=11))
    for t in autotexts:
        t.set_color('white'); t.set_fontweight('bold')
    ax.set_title('用户参与四种行为的占比（漏斗扁平视角）', fontsize=15,
                 fontweight='bold', pad=15)
    save(fig, "14_behavior_pie.png", 10, 8)


def chart_15_rfm_scatter():
    """15 RFM 散点图 - R vs F，颜色 = M，大小 = 用户重要性"""
    df = load("08_rfm_detail.csv")
    if df is None: return
    df_sample = df.sample(min(2000, len(df)), random_state=42) if len(df) > 2000 else df
    fig, ax = plt.subplots()
    sc = ax.scatter(df_sample['recency'], df_sample['frequency'],
                    c=df_sample['monetary'], cmap='RdYlGn_r',
                    s=df_sample['monetary'] * 3 + 10, alpha=0.55, edgecolor='white', linewidth=0.5)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('Monetary（消费力代理）', fontsize=11)
    ax.set_xlabel('Recency（最近一次购买距今天数）—— 越小越好', fontsize=12)
    ax.set_ylabel('Frequency（购买频次）—— 越大越好', fontsize=12)
    ax.set_title(f'RFM 用户散点图（样本 {len(df_sample)} 人）', fontsize=15,
                 fontweight='bold', pad=15)
    ax.grid(alpha=0.3)
    save(fig, "15_rfm_scatter.png", 12, 7)


def chart_16_dashboard():
    """16 综合看板（4 张关键图合一）"""
    fig, axes = plt.subplots(2, 2, figsize=(18, 11))

    # 左上：日 PV/UV
    df1 = load("01_daily_pv_uv.csv")
    if df1 is not None:
        ax = axes[0][0]; ax2 = ax.twinx()
        ax.bar(df1['event_date'], df1['pv'], color=COLORS[0], alpha=0.7, label='PV')
        ax2.plot(df1['event_date'], df1['uv'], color=COLORS[3], marker='o', label='UV')
        ax.set_title('① 每日 PV / UV', fontweight='bold', fontsize=13)
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right', fontsize=8)
        ax.grid(axis='y', alpha=0.3)
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1+h2, l1+l2, fontsize=9)

    # 右上：行为漏斗
    df3 = load("03_behavior_funnel.csv")
    if df3 is not None:
        ax = axes[0][1]
        ax.barh(df3['behavior'], df3['user_count'], color=COLORS[:len(df3)], alpha=0.85,
               edgecolor='white', linewidth=2)
        ax.invert_yaxis()
        for i, (cnt, r) in enumerate(zip(df3['user_count'], df3['ratio'])):
            ax.text(cnt + max(df3['user_count'])*0.01, i, f'{int(cnt):,} ({r}%)',
                   va='center', fontsize=10, fontweight='bold')
        ax.set_title('② 行为转化漏斗', fontweight='bold', fontsize=13)
        ax.set_xlim(0, max(df3['user_count']) * 1.2)
        ax.grid(axis='x', alpha=0.3)

    # 左下：RFM 分群
    df8 = load("08_rfm_summary.csv")
    if df8 is not None:
        ax = axes[1][0]
        colors_arr = plt.cm.Set3(np.linspace(0, 1, len(df8)))
        ax.pie(df8['user_count'], labels=df8['segment'], colors=colors_arr,
              autopct='%1.1f%%', startangle=90,
              wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
              textprops=dict(fontsize=9))
        ax.set_title('③ RFM 用户分群', fontweight='bold', fontsize=13)

    # 右下：复购分布
    df11 = load("11_repurchase.csv")
    if df11 is not None:
        df11 = df11.sort_values('bucket_order')
        ax = axes[1][1]; x = np.arange(len(df11)); w = 0.4
        ax.bar(x - w/2, df11['user_ratio'], w, color=COLORS[0], alpha=0.85,
              label='用户占比(%)')
        ax.bar(x + w/2, df11['buy_contribution'], w, color=COLORS[3], alpha=0.85,
              label='购买贡献(%)')
        ax.set_xticks(x)
        ax.set_xticklabels(df11['buy_times_bucket'], fontsize=8, rotation=15, ha='right')
        ax.set_title('④ 复购率分布（二八定律）', fontweight='bold', fontsize=13)
        ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)

    plt.suptitle('大数据用户行为分析 — 综合看板', fontsize=18, fontweight='bold', y=1.00)
    save(fig, "16_dashboard.png", 18, 11)


# ===================================================================
if __name__ == "__main__":
    print(f"输出目录: {PNG_DIR}")
    print("=" * 60)
    print("[1/2] 主要图表")
    chart_01_daily_pv_uv()
    chart_02_hourly_distribution()
    chart_03_behavior_funnel()
    chart_04_top_items()
    chart_05_top_categories()
    chart_06_weekday_weekend()
    chart_07_retention()
    chart_08_rfm()
    chart_09_user_path()
    chart_10_category_conversion()
    chart_11_heatmap_hour_dow()
    chart_12_repurchase()
    chart_13_category_treemap()
    print()
    print("[2/2] 扩展图表")
    chart_14_behavior_pie()
    chart_15_rfm_scatter()
    chart_16_dashboard()
    print("=" * 60)
    print(f"全部完成！PNG 在 {PNG_DIR}")
