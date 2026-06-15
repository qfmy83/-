"""
分析任务 1: 每日 PV/UV 流量趋势
指标: 每日页面浏览量(PV)、独立访客数(UV)、被浏览商品数、人均浏览量
输出: ads.daily_pv_uv + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_01_DailyPVUV")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 1: 每日 PV/UV 流量趋势")
        print("=" * 60)

        # 同一查询同时计算 4 个指标：避免多次扫描 DWD
        # COUNT(DISTINCT user_id) 触发 shuffle，是最贵的步骤
        result = spark.sql("""
            SELECT
                event_date,
                SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) AS pv,
                COUNT(DISTINCT user_id) AS uv,
                COUNT(DISTINCT CASE WHEN behavior = 'pv' THEN item_id END) AS item_count,
                ROUND(SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) * 1.0
                      / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS avg_pv_per_user
            FROM dwd.user_behavior_detail
            GROUP BY event_date
            ORDER BY event_date
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空，可能 DWD 层无数据")
            return

        result.show(20, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.daily_pv_uv")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "01_daily_pv_uv.csv"), index=False)

        print("[SUCCESS] 任务 1 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 1 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
