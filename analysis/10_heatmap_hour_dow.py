"""
分析任务 10: 24小时 × 7天 行为热力图
业务目的: 找出"下单黄金时段"，比单维度的小时分布更能揭示运营时机
       例如：周日晚 8 点的购买量明显高于工作日同时段
算法: 按 day_of_week × event_hour 双维度聚合，168 个格子（24×7）
输出: ads.heatmap_hour_dow + CSV
运行: spark-submit analysis/10_heatmap_hour_dow.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_10_HeatmapHourDow")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 10: 24h × 7d 行为热力图")
        print("=" * 60)

        # day_of_week 和 event_hour 都已在 DWD 阶段预派生，这里直接双 GROUP BY
        # COUNT(DISTINCT user_id) 触发 shuffle，是分布式聚合的体现
        result = spark.sql("""
            SELECT
                day_of_week,
                event_hour,
                COUNT(*) AS pv_count,
                SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS buy_count,
                COUNT(DISTINCT user_id) AS active_users
            FROM dwd.user_behavior_detail
            GROUP BY day_of_week, event_hour
            ORDER BY day_of_week, event_hour
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(50, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.heatmap_hour_dow")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "10_heatmap_hour_dow.csv"), index=False)

        print("[SUCCESS] 任务 10 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 10 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
