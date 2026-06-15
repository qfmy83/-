"""
分析任务 11: 用户复购率分布
业务目的: 验证电商二八定律 —— 大多数购买量是否由少数高频用户贡献？
       同时洞察"复购漏斗"：1次→2次→3次的用户流失情况
算法: 先按用户聚合购买次数，再按"购买次数桶"分组（1次/2次/3-5次/6-10次/11次以上）
     双指标：用户数占比（看长尾） + 购买量占比（看二八）
输出: ads.repurchase_distribution + CSV
运行: spark-submit analysis/11_repurchase.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_11_Repurchase")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 11: 用户复购率分布")
        print("=" * 60)

        # 第一层 CTE：每个用户的购买次数（HAVING 过滤掉没买过的用户）
        # 第二层 CTE：按购买次数 CASE 分桶，得到桶名 + 桶顺序
        # 外层：按桶聚合用户数和购买量，并算两个百分比
        result = spark.sql("""
            WITH user_buy AS (
                SELECT user_id,
                       SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS buy_times
                FROM dwd.user_behavior_detail
                GROUP BY user_id
                HAVING SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) > 0
            ),
            bucketed AS (
                SELECT user_id, buy_times,
                    CASE
                        WHEN buy_times = 1 THEN '1次（一次性买家）'
                        WHEN buy_times = 2 THEN '2次（首次复购）'
                        WHEN buy_times BETWEEN 3 AND 5 THEN '3-5次（活跃买家）'
                        WHEN buy_times BETWEEN 6 AND 10 THEN '6-10次（高频买家）'
                        ELSE '11次以上（核心买家）'
                    END AS buy_times_bucket,
                    CASE
                        WHEN buy_times = 1 THEN 1
                        WHEN buy_times = 2 THEN 2
                        WHEN buy_times BETWEEN 3 AND 5 THEN 3
                        WHEN buy_times BETWEEN 6 AND 10 THEN 4
                        ELSE 5
                    END AS bucket_order
                FROM user_buy
            )
            SELECT
                buy_times_bucket,
                bucket_order,
                COUNT(*) AS user_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS user_ratio,
                SUM(buy_times) AS total_buy,
                ROUND(SUM(buy_times) * 100.0 / SUM(SUM(buy_times)) OVER (), 2) AS buy_contribution
            FROM bucketed
            GROUP BY buy_times_bucket, bucket_order
            ORDER BY bucket_order
        """).cache()

        if result.count() == 0:
            print("[WARN] 无购买用户，复购分析跳过")
            return

        result.show(truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.repurchase_distribution")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "11_repurchase.csv"), index=False)

        print("[SUCCESS] 任务 11 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 11 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
