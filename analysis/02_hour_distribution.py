"""
分析任务 2: 24小时用户活跃分布
指标: 每个小时的浏览量、独立访客数、加购数、购买数
输出: ads.hourly_distribution + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_02_HourDistribution")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 2: 24小时用户活跃分布")
        print("=" * 60)

        # 按 event_hour 聚合，DWD 已有此字段，无需再次时间换算
        result = spark.sql("""
            SELECT
                event_hour,
                SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) AS pv,
                COUNT(DISTINCT user_id) AS uv,
                SUM(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) AS cart_count,
                SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS buy_count
            FROM dwd.user_behavior_detail
            GROUP BY event_hour
            ORDER BY event_hour
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(24, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.hourly_distribution")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "02_hourly_distribution.csv"), index=False)

        print("[SUCCESS] 任务 2 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 2 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
