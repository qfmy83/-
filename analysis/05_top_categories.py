"""
分析任务 5: TOP20 热门类目及转化率
指标: 各类目的浏览量、购买量及转化率(buy/pv)
输出: ads.top_categories + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_05_TopCategories")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 5: TOP20 热门类目及转化率")
        print("=" * 60)

        # NULLIF(pv_count, 0) 防止极端情况下类目无 PV 时的除零错误
        result = spark.sql("""
            SELECT
                ROW_NUMBER() OVER (ORDER BY pv_count DESC) AS ranking,
                category_id, pv_count, buy_count,
                ROUND(buy_count * 100.0 / NULLIF(pv_count, 0), 4) AS conversion_rate
            FROM (
                SELECT
                    category_id,
                    SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) AS pv_count,
                    SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS buy_count
                FROM dwd.user_behavior_detail
                GROUP BY category_id
            ) t
            ORDER BY pv_count DESC
            LIMIT 20
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(20, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.top_categories")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "05_top_categories.csv"), index=False)

        print("[SUCCESS] 任务 5 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 5 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
