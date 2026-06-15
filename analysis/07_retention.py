"""
分析任务 7: 用户留存分析
指标: 次日(D+1)、2日(D+2)、3日(D+3)留存率
算法: 用户首次出现日期为基准，计算后续几日是否有活跃
输出: ads.retention + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_07_Retention")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 7: 用户留存分析")
        print("=" * 60)

        # 留存率分母 = 首次活跃日期为 D 的新用户数
        # 留存率分子 = 这些用户在 D+N 日仍有活跃的人数
        # 注意：100 万样本时间集中在 11-25 头部，跨日数据可能偏少，结果仅供演示

        # 每个用户的首次活跃日期（即获客日期）
        spark.sql("""
            CREATE OR REPLACE TEMP VIEW user_first_date AS
            SELECT user_id, MIN(event_date) AS first_date
            FROM dwd.user_behavior_detail
            GROUP BY user_id
        """)

        # 每个用户的活跃日期集合（去重）
        spark.sql("""
            CREATE OR REPLACE TEMP VIEW user_active_dates AS
            SELECT DISTINCT user_id, event_date
            FROM dwd.user_behavior_detail
        """)

        # 三次自连接分别匹配 D+1 / D+2 / D+3 的活跃记录
        # NULLIF 防止某日仅一两个新用户、且全是当日离去时分母为 0
        result = spark.sql("""
            SELECT
                f.first_date,
                COUNT(DISTINCT f.user_id) AS new_users,
                ROUND(COUNT(DISTINCT CASE
                    WHEN DATEDIFF(a1.event_date, f.first_date) = 1
                    THEN f.user_id END) * 100.0 / NULLIF(COUNT(DISTINCT f.user_id), 0), 2) AS day_1,
                ROUND(COUNT(DISTINCT CASE
                    WHEN DATEDIFF(a2.event_date, f.first_date) = 2
                    THEN f.user_id END) * 100.0 / NULLIF(COUNT(DISTINCT f.user_id), 0), 2) AS day_2,
                ROUND(COUNT(DISTINCT CASE
                    WHEN DATEDIFF(a3.event_date, f.first_date) = 3
                    THEN f.user_id END) * 100.0 / NULLIF(COUNT(DISTINCT f.user_id), 0), 2) AS day_3
            FROM user_first_date f
            LEFT JOIN user_active_dates a1
                ON f.user_id = a1.user_id AND DATEDIFF(a1.event_date, f.first_date) = 1
            LEFT JOIN user_active_dates a2
                ON f.user_id = a2.user_id AND DATEDIFF(a2.event_date, f.first_date) = 2
            LEFT JOIN user_active_dates a3
                ON f.user_id = a3.user_id AND DATEDIFF(a3.event_date, f.first_date) = 3
            GROUP BY f.first_date
            ORDER BY f.first_date
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(20, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.retention")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "07_retention.csv"), index=False)

        print("[SUCCESS] 任务 7 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 7 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
