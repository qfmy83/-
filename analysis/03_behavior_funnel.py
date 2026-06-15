"""
分析任务 3: 用户行为转化漏斗
指标: pv → fav → cart → buy 各阶段的用户数与转化率
输出: ads.behavior_funnel + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR
from pyspark.sql import functions as F, Window


def main():
    spark = get_spark_session("Analysis_03_BehaviorFunnel")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 3: 用户行为转化漏斗")
        print("=" * 60)

        # COUNT(DISTINCT user_id) 按 behavior 分组，得到每种行为的"覆盖用户数"
        # 注意：用户级漏斗不要求严格先后，只统计是否曾发生该行为
        funnel_data = spark.sql("""
            SELECT behavior, COUNT(DISTINCT user_id) AS user_count
            FROM dwd.user_behavior_detail
            GROUP BY behavior
        """).collect()

        if not funnel_data:
            print("[WARN] DWD 层无数据，漏斗分析跳过")
            return

        behavior_counts = {row["behavior"]: row["user_count"] for row in funnel_data}

        # 漏斗顺序（业务漏斗：浏览 → 收藏 → 加购 → 购买）
        order = ["pv", "fav", "cart", "buy"]
        labels = {"pv": "浏览(pv)", "fav": "收藏(fav)", "cart": "加购(cart)", "buy": "购买(buy)"}

        pv_users = behavior_counts.get("pv", 0)
        if pv_users == 0:
            print("[WARN] 无 PV 行为用户，漏斗分析跳过")
            return

        rows = []
        prev_count = pv_users
        for b in order:
            cnt = behavior_counts.get(b, 0)
            # ratio: 相对上一阶段的转化率；overall: 相对最初浏览用户的整体转化率
            ratio = round(cnt / prev_count * 100, 2) if prev_count > 0 else 0.0
            overall = round(cnt / pv_users * 100, 2)
            rows.append((labels[b], cnt, ratio, overall))
            prev_count = cnt

        result = spark.createDataFrame(rows, ["behavior", "user_count", "ratio", "overall_rate"])
        result.show(truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.behavior_funnel")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "03_behavior_funnel.csv"), index=False)

        print("[SUCCESS] 任务 3 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 3 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
