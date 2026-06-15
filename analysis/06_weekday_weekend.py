"""
分析任务 6: 工作日 vs 周末行为对比
指标: 工作日和周末各类行为的总数、用户数、人均次数
输出: ads.weekday_vs_weekend + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_06_WeekdayWeekend")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 6: 工作日 vs 周末行为对比")
        print("=" * 60)

        # is_weekend 字段在 DWD 阶段已经计算好（周六周日 = 1），此处直接复用
        result = spark.sql("""
            SELECT
                CASE WHEN is_weekend = 1 THEN 'weekend' ELSE 'weekday' END AS day_type,
                behavior,
                COUNT(*) AS total_count,
                COUNT(DISTINCT user_id) AS user_count,
                ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS avg_per_user
            FROM dwd.user_behavior_detail
            GROUP BY is_weekend, behavior
            ORDER BY day_type, behavior
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(20, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.weekday_vs_weekend")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "06_weekday_vs_weekend.csv"), index=False)

        print("[SUCCESS] 任务 6 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 6 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
