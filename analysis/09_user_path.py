"""
分析任务 9: 用户行为路径分析（桑基图数据）
算法: 使用窗口函数 LAG() 获取用户相邻两次行为，构建行为转移矩阵
输出: ads.user_path + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_09_UserPath")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 9: 用户行为路径分析")
        print("=" * 60)

        # 用 LAG 窗口函数取每个用户按时间排序的前一个行为，构成 (from→to) 行为对
        # 外层按 from_behavior 分区做百分比，得到从某行为到各后续行为的转移概率，可直接画桑基图
        result = spark.sql("""
            SELECT
                from_behavior,
                to_behavior,
                COUNT(*) AS path_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY from_behavior), 2) AS path_ratio
            FROM (
                SELECT
                    LAG(behavior) OVER (
                        PARTITION BY user_id ORDER BY event_time
                    ) AS from_behavior,
                    behavior AS to_behavior
                FROM dwd.user_behavior_detail
            ) t
            WHERE from_behavior IS NOT NULL
            GROUP BY from_behavior, to_behavior
            ORDER BY from_behavior, path_count DESC
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(20, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.user_path")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "09_user_path.csv"), index=False)

        print("[SUCCESS] 任务 9 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 9 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
