"""
可视化图表生成程序
依赖: pip install pyecharts
运行: python3 visualization/viz_all.py
"""

import os
import sys

# 确保能导入 utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import load_csv, save_html, HTML_DIR, COLORS, BEHAVIOR_MAP

from pyecharts import options as opts
from pyecharts.charts import (
    Bar, Line, Pie, Funnel, HeatMap, Sankey,
    Radar, Scatter, TreeMap, Page, Grid, Tab
)
from pyecharts.components import Table as PyTable
from pyecharts.globals import ThemeType
from pyecharts.commons.utils import JsCode


def chart_01_daily_pv_uv():
    """图表1: 每日PV/UV趋势 - 双Y轴折线图"""
    print("[1/10] 每日 PV/UV 趋势...")
    df = load_csv("01_daily_pv_uv.csv")

    dates = df["event_date"].tolist()
    pv_data = df["pv"].tolist()
    uv_data = df["uv"].tolist()
    avg_pv = df["avg_pv_per_user"].tolist()

    chart = (
        Line(init_opts=opts.InitOpts(width="1000px", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(dates)
        .add_yaxis("PV(浏览量)", pv_data, yaxis_index=0,
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[0]))
        .add_yaxis("UV(独立访客)", uv_data, yaxis_index=1,
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[1]))
        .extend_axis(yaxis=opts.AxisOpts(name="UV", position="right"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="每日 PV/UV 流量趋势", subtitle="数据来源: UserBehavior 数据集"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            yaxis_opts=opts.AxisOpts(name="PV"),
            xaxis_opts=opts.AxisOpts(name="日期", axislabel_opts=opts.LabelOpts(rotate=30)),
            legend_opts=opts.LegendOpts(pos_top="5%"),
            datazoom_opts=[opts.DataZoomOpts(type_="inside")],
        )
    )
    save_html(chart, "01_daily_pv_uv.html")
    return chart


def chart_02_hourly_distribution():
    """图表2: 24小时活跃分布 - 柱状图+折线图"""
    print("[2/10] 24小时活跃分布...")
    df = load_csv("02_hourly_distribution.csv")

    hours = [f"{h}:00" for h in df["event_hour"].tolist()]
    pv_data = df["pv"].tolist()
    uv_data = df["uv"].tolist()
    buy_data = df["buy_count"].tolist()

    chart = (
        Bar(init_opts=opts.InitOpts(width="1000px", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(hours)
        .add_yaxis("浏览量(PV)", pv_data,
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[4]),
                    label_opts=opts.LabelOpts(is_show=False))
        .extend_axis(yaxis=opts.AxisOpts(name="UV / 购买数", position="right"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="24小时用户活跃分布", subtitle="用户行为随时间的变化规律"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="时段"),
            yaxis_opts=opts.AxisOpts(name="浏览量"),
            legend_opts=opts.LegendOpts(pos_top="5%"),
        )
    )

    line = (
        Line()
        .add_xaxis(hours)
        .add_yaxis("独立访客(UV)", uv_data, yaxis_index=1,
                    linestyle_opts=opts.LineStyleOpts(width=3, type_="dashed"),
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[3]))
        .add_yaxis("购买数", buy_data, yaxis_index=1,
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[1]))
    )
    chart.overlap(line)
    save_html(chart, "02_hourly_distribution.html")
    return chart


def chart_03_behavior_funnel():
    """图表3: 用户行为转化漏斗"""
    print("[3/10] 用户行为转化漏斗...")
    df = load_csv("03_behavior_funnel.csv")

    data = [(row["behavior"], row["user_count"]) for _, row in df.iterrows()]

    chart = (
        Funnel(init_opts=opts.InitOpts(width="1000px", height="500px", theme=ThemeType.LIGHT))
        .add("用户数", data,
             sort_="descending",
             gap=2,
             label_opts=opts.LabelOpts(position="inside", formatter="{b}: {c}"),
             itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=1))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="用户行为转化漏斗",
                                      subtitle="从浏览到购买的转化路径"),
            tooltip_opts=opts.TooltipOpts(trigger="item",
                                           formatter="{b}: {c} 用户"),
            legend_opts=opts.LegendOpts(pos_top="5%"),
        )
    )
    save_html(chart, "03_behavior_funnel.html")
    return chart


def chart_04_top_items():
    """图表4: TOP20热门商品 - 横向条形图"""
    print("[4/10] TOP20 热门商品...")
    df = load_csv("04_top_items.csv").head(20)

    items = [str(x) for x in df["item_id"].tolist()]
    scores = df["total_score"].tolist()
    pv_list = df["pv_count"].tolist()
    buy_list = df["buy_count"].tolist()

    items.reverse()
    scores.reverse()
    pv_list.reverse()
    buy_list.reverse()

    chart = (
        Bar(init_opts=opts.InitOpts(width="1000px", height="600px", theme=ThemeType.LIGHT))
        .add_xaxis(items)
        .add_yaxis("热度得分", scores,
                    label_opts=opts.LabelOpts(position="right"),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=JsCode(
                            """new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                                {offset: 0, color: '#5470c6'},
                                {offset: 1, color: '#91cc75'}
                            ])"""
                        )
                    ))
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title="TOP20 热门商品排行",
                                      subtitle="综合热度得分 = PV×1 + FAV×3 + CART×5 + BUY×10"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            yaxis_opts=opts.AxisOpts(name="商品ID"),
            xaxis_opts=opts.AxisOpts(name="热度得分"),
        )
    )
    save_html(chart, "04_top_items.html")
    return chart


def chart_05_top_categories():
    """图表5: TOP20热门类目 - 玫瑰饼图"""
    print("[5/10] TOP20 热门类目...")
    df = load_csv("05_top_categories.csv").head(15)

    data = [(str(row["category_id"]), int(row["pv_count"])) for _, row in df.iterrows()]

    chart = (
        Pie(init_opts=opts.InitOpts(width="1000px", height="600px", theme=ThemeType.LIGHT))
        .add("浏览量", data,
             radius=["20%", "70%"],
             rosetype="area",
             label_opts=opts.LabelOpts(formatter="{b}\n{d}%"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="TOP15 热门类目占比",
                                      subtitle="南丁格尔玫瑰图 - 按浏览量排序"),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
            # legend 放底部水平排列，避免在 1000px 宽下右侧文字被裁
            legend_opts=opts.LegendOpts(type_="scroll", pos_bottom="0%", orient="horizontal"),
        )
    )
    save_html(chart, "05_top_categories.html")
    return chart


def chart_06_weekday_weekend():
    """图表6: 工作日vs周末对比 - 分组柱状图"""
    print("[6/10] 工作日 vs 周末对比...")
    df = load_csv("06_weekday_vs_weekend.csv")

    behaviors = sorted(df["behavior"].unique())
    behavior_labels = [BEHAVIOR_MAP.get(b, b) for b in behaviors]

    weekday_data = []
    weekend_data = []
    for b in behaviors:
        wd = df[(df["day_type"] == "weekday") & (df["behavior"] == b)]
        we = df[(df["day_type"] == "weekend") & (df["behavior"] == b)]
        # 用 float 而非 int，保留小数差异（人均次数通常是 4.7、5.2 这种）
        weekday_data.append(round(float(wd["avg_per_user"].iloc[0]), 2) if len(wd) > 0 else 0)
        weekend_data.append(round(float(we["avg_per_user"].iloc[0]), 2) if len(we) > 0 else 0)

    chart = (
        Bar(init_opts=opts.InitOpts(width="1000px", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(behavior_labels)
        .add_yaxis("工作日", weekday_data,
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[0]))
        .add_yaxis("周末", weekend_data,
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[3]))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="工作日 vs 周末 用户行为对比",
                                      subtitle="人均行为次数对比"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="行为类型"),
            yaxis_opts=opts.AxisOpts(name="人均次数"),
        )
    )
    save_html(chart, "06_weekday_weekend.html")
    return chart


def chart_07_retention():
    """图表7: 用户留存率曲线"""
    print("[7/10] 用户留存率...")
    df = load_csv("07_retention.csv")

    dates = df["first_date"].tolist()
    d1 = df["day_1"].tolist()
    d2 = df["day_2"].tolist()
    d3 = df["day_3"].tolist()

    chart = (
        Line(init_opts=opts.InitOpts(width="1000px", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(dates)
        .add_yaxis("次日留存率(%)", d1,
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    label_opts=opts.LabelOpts(formatter="{c}%"),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[0]),
                    markpoint_opts=opts.MarkPointOpts(data=[
                        opts.MarkPointItem(type_="max", name="最高"),
                        opts.MarkPointItem(type_="min", name="最低"),
                    ]))
        .add_yaxis("2日留存率(%)", d2,
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    label_opts=opts.LabelOpts(formatter="{c}%"),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[1]))
        .add_yaxis("3日留存率(%)", d3,
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    label_opts=opts.LabelOpts(formatter="{c}%"),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[3]))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="用户留存率分析", subtitle="按首次活跃日期统计"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="首次活跃日期", axislabel_opts=opts.LabelOpts(rotate=30)),
            yaxis_opts=opts.AxisOpts(name="留存率(%)"),
            legend_opts=opts.LegendOpts(pos_top="5%"),
        )
    )
    save_html(chart, "07_retention.html")
    return chart


def chart_08_rfm():
    """图表8: RFM用户分群 - 饼图"""
    print("[8/10] RFM 用户分群...")
    df = load_csv("08_rfm_summary.csv")

    data = [(row["segment"], int(row["user_count"])) for _, row in df.iterrows()]

    chart = (
        Pie(init_opts=opts.InitOpts(width="1000px", height="600px", theme=ThemeType.LIGHT))
        .add("用户数", data,
             radius=["35%", "65%"],
             label_opts=opts.LabelOpts(
                 formatter="{b}\n{c}人 ({d}%)",
                 font_size=12,
             ))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="RFM 用户分群分布",
                                      subtitle="基于 Recency/Frequency/Monetary 三维度"),
            tooltip_opts=opts.TooltipOpts(trigger="item",
                                           formatter="{b}: {c}人 ({d}%)"),
            legend_opts=opts.LegendOpts(type_="scroll", pos_bottom="0%",
                                         orient="horizontal"),
        )
    )
    save_html(chart, "08_rfm.html")
    return chart


def chart_09_user_path():
    """图表9: 用户行为路径 - 桑基图"""
    print("[9/10] 用户行为路径(桑基图)...")
    df = load_csv("09_user_path.csv")

    # 构建桑基图节点和链接
    # 为区分来源和目标，添加前缀
    nodes = []
    seen = set()
    for _, row in df.iterrows():
        src = f"前序_{BEHAVIOR_MAP.get(row['from_behavior'], row['from_behavior'])}"
        tgt = f"后续_{BEHAVIOR_MAP.get(row['to_behavior'], row['to_behavior'])}"
        if src not in seen:
            nodes.append({"name": src})
            seen.add(src)
        if tgt not in seen:
            nodes.append({"name": tgt})
            seen.add(tgt)

    links = []
    for _, row in df.iterrows():
        src = f"前序_{BEHAVIOR_MAP.get(row['from_behavior'], row['from_behavior'])}"
        tgt = f"后续_{BEHAVIOR_MAP.get(row['to_behavior'], row['to_behavior'])}"
        links.append({
            "source": src,
            "target": tgt,
            "value": int(row["path_count"]),
        })

    chart = (
        Sankey(init_opts=opts.InitOpts(width="1000px", height="600px", theme=ThemeType.LIGHT))
        .add("行为转移",
             nodes=nodes,
             links=links,
             linestyle_opt=opts.LineStyleOpts(opacity=0.3, curve=0.5, color="source"),
             label_opts=opts.LabelOpts(position="right", font_size=14),
             node_width=30,
             node_gap=15)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="用户行为路径分析",
                                      subtitle="基于窗口函数的行为转移概率"),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )
    save_html(chart, "09_user_path.html")
    return chart


def chart_10_category_conversion():
    """图表10: 类目转化率对比 - 散点图"""
    print("[10/10] 类目浏览量vs转化率(散点图)...")
    df = load_csv("05_top_categories.csv").head(20)

    data = []
    for _, row in df.iterrows():
        data.append([
            int(row["pv_count"]),
            float(row["conversion_rate"]),
            str(row["category_id"]),
        ])

    chart = (
        Scatter(init_opts=opts.InitOpts(width="1000px", height="600px", theme=ThemeType.LIGHT))
        .add_xaxis([d[0] for d in data])
        .add_yaxis("类目", [d[1] for d in data],
                    symbol_size=20,
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(color=COLORS[0]))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="类目浏览量 vs 转化率",
                                      subtitle="气泡越大代表浏览量越高"),
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    "function(params){return '类目: '+params.data[2]+"
                    "'<br/>浏览量: '+params.data[0]+'<br/>转化率: '+params.data[1]+'%';}"
                )
            ),
            xaxis_opts=opts.AxisOpts(name="浏览量(PV)", type_="value"),
            yaxis_opts=opts.AxisOpts(name="转化率(%)"),
            visualmap_opts=opts.VisualMapOpts(
                min_=min(d[0] for d in data),
                max_=max(d[0] for d in data),
                dimension=0,
                is_show=True,
                range_color=["#5470c6", "#91cc75", "#fac858", "#ee6666"],
            ),
        )
    )
    save_html(chart, "10_category_conversion.html")
    return chart


def chart_11_heatmap_hour_dow():
    """图表11: 24h × 7d 行为热力图 - 找下单黄金时段"""
    print("[11/13] 24h × 7d 行为热力图...")
    df = load_csv("10_heatmap_hour_dow.csv")

    # pyecharts HeatMap 数据格式: [[x, y, value], ...]
    # 用 buy_count 作为热度值（业务意义最强：哪个时段下单最多）
    week_labels = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
    hour_labels = [f"{h}:00" for h in range(24)]

    data = []
    for _, row in df.iterrows():
        # day_of_week 1=周日 → x 轴 0；event_hour 0-23 → y 轴 0-23
        x = int(row["event_hour"])
        y = int(row["day_of_week"]) - 1
        data.append([x, y, int(row["buy_count"])])

    max_buy = int(df["buy_count"].max()) if len(df) > 0 else 1

    chart = (
        HeatMap(init_opts=opts.InitOpts(width="1100px", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(hour_labels)
        .add_yaxis(
            "购买量",
            week_labels,
            data,
            label_opts=opts.LabelOpts(is_show=True, position="inside", font_size=9),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="24小时 × 7天 购买热力图",
                subtitle="颜色越深表示该时段下单越多 — 找出运营黄金时段"
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
            xaxis_opts=opts.AxisOpts(type_="category", name="小时", splitarea_opts=opts.SplitAreaOpts(is_show=True)),
            yaxis_opts=opts.AxisOpts(type_="category", name="星期", splitarea_opts=opts.SplitAreaOpts(is_show=True)),
            visualmap_opts=opts.VisualMapOpts(
                min_=0, max_=max_buy, is_calculable=True, orient="horizontal", pos_left="center", pos_bottom="0%",
                range_color=["#e0f3f8", "#abd9e9", "#74add1", "#4575b4", "#313695"],
            ),
        )
    )
    save_html(chart, "11_heatmap_hour_dow.html")
    return chart


def chart_12_repurchase():
    """图表12: 用户复购率分布 - 验证二八定律"""
    print("[12/13] 用户复购率分布...")
    df = load_csv("11_repurchase.csv")

    buckets = df["buy_times_bucket"].tolist()
    user_ratio = df["user_ratio"].tolist()       # 用户数占比
    buy_contri = df["buy_contribution"].tolist()  # 购买量占比

    # 双 Y 轴对比：用户占比（多） vs 购买量占比（集中）
    # 经典二八：少数高频用户贡献大部分订单
    chart = (
        Bar(init_opts=opts.InitOpts(width="1000px", height="500px", theme=ThemeType.LIGHT))
        .add_xaxis(buckets)
        .add_yaxis(
            "用户数占比(%)", user_ratio,
            itemstyle_opts=opts.ItemStyleOpts(color=COLORS[0]),
            label_opts=opts.LabelOpts(position="top", formatter="{c}%"),
        )
        .add_yaxis(
            "购买量贡献占比(%)", buy_contri,
            itemstyle_opts=opts.ItemStyleOpts(color=COLORS[3]),
            label_opts=opts.LabelOpts(position="top", formatter="{c}%"),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="用户复购率分布",
                subtitle="对比『用户占比』与『购买量贡献』 — 验证二八定律"
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="购买次数分桶", axislabel_opts=opts.LabelOpts(rotate=15, font_size=10)),
            yaxis_opts=opts.AxisOpts(name="百分比(%)"),
            legend_opts=opts.LegendOpts(pos_top="5%"),
        )
    )
    save_html(chart, "12_repurchase.html")
    return chart


def chart_13_category_treemap():
    """图表13: TOP10 类目内 TOP5 商品树状图 - 嵌套层级关系"""
    print("[13/13] TOP10 类目内 TOP5 商品(树状图)...")
    df = load_csv("12_category_top_items.csv")

    # TreeMap 数据格式: [{name, value, children: [...]}, ...]
    # 父节点 = 类目（大小由 category_pv 决定）
    # 子节点 = 类目内 TOP5 商品（大小由 item_pv 决定）
    cat_to_items = {}
    cat_pv_map = {}
    for _, row in df.iterrows():
        cid = str(int(row["category_id"]))
        cat_pv_map[cid] = int(row["category_pv"])
        cat_to_items.setdefault(cid, []).append({
            "name": f"商品{int(row['item_id'])}",
            "value": int(row["item_pv"]),
        })

    treemap_data = []
    for cid, items in cat_to_items.items():
        treemap_data.append({
            "name": f"类目{cid}",
            "value": cat_pv_map[cid],
            "children": items,
        })

    chart = (
        TreeMap(init_opts=opts.InitOpts(width="1100px", height="600px", theme=ThemeType.LIGHT))
        .add(
            "类目-商品",
            treemap_data,
            leaf_depth=2,
            label_opts=opts.LabelOpts(position="inside", font_size=11),
            levels=[
                opts.TreeMapLevelsOpts(
                    treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(
                        border_color="#fff", border_width=2, gap_width=2
                    )
                ),
                opts.TreeMapLevelsOpts(
                    color_saturation=[0.3, 0.6],
                    treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(
                        border_color_saturation=0.7, gap_width=1, border_width=1
                    )
                ),
            ],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="TOP10 类目 × 类目内 TOP5 商品",
                subtitle="父矩形=类目浏览量，子矩形=该类目内 TOP5 商品"
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}"),
        )
    )
    save_html(chart, "13_category_treemap.html")
    return chart


def build_dashboard():
    """构建综合仪表盘（合并所有图表）"""
    print("\n[INFO] 正在构建综合仪表盘...")

    page = Page(layout=Page.SimplePageLayout)
    page.add(
        chart_01_daily_pv_uv(),
        chart_02_hourly_distribution(),
        chart_03_behavior_funnel(),
        chart_04_top_items(),
        chart_05_top_categories(),
        chart_06_weekday_weekend(),
        chart_07_retention(),
        chart_08_rfm(),
        chart_09_user_path(),
        chart_10_category_conversion(),
        chart_11_heatmap_hour_dow(),
        chart_12_repurchase(),
        chart_13_category_treemap(),
    )

    dashboard_path = os.path.join(HTML_DIR, "dashboard.html")
    page.render(dashboard_path)
    print(f"\n[SUCCESS] 综合仪表盘已生成: {dashboard_path}")
    print(f"  在浏览器中打开即可查看所有图表。")


def main():
    print("=" * 60)
    print("数据可视化生成")
    print("=" * 60)

    try:
        build_dashboard()
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("请先运行分析程序生成 CSV 数据。")
        sys.exit(1)

    print("\n[SUCCESS] 全部可视化完成！")
    print(f"  单独图表: {HTML_DIR}/01_*.html ~ 13_*.html")
    print(f"  综合看板: {HTML_DIR}/dashboard.html")


if __name__ == "__main__":
    main()
