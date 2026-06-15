"""
分析任务 4: TOP100 热门商品排行
指标: 综合 pv/fav/cart/buy 加权计算商品热度得分
算法: total_score = pv*1 + fav*3 + cart*5 + buy*10
输出: ads.top_items + CSV
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_04_TopItems")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 4: TOP100 热门商品排行")
        print("=" * 60)

        # 综合热度得分加权：购买行为权重最高（×10）反映商业价值
        # 排名先内层算分，再外层 ROW_NUMBER 编号；LIMIT 100 截断
        result = spark.sql("""
            SELECT
                ROW_NUMBER() OVER (ORDER BY total_score DESC) AS ranking,
                item_id, pv_count, fav_count, cart_count, buy_count, total_score
            FROM (
                SELECT
                    item_id,
                    SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) AS pv_count,
                    SUM(CASE WHEN behavior = 'fav' THEN 1 ELSE 0 END) AS fav_count,
                    SUM(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) AS cart_count,
                    SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS buy_count,
                    -- 加权分：体现"越接近购买行为越重要"的业务直觉
                    SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) * 1
                    + SUM(CASE WHEN behavior = 'fav' THEN 1 ELSE 0 END) * 3
                    + SUM(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) * 5
                    + SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) * 10 AS total_score
                FROM dwd.user_behavior_detail
                GROUP BY item_id
            ) t
            ORDER BY total_score DESC
            LIMIT 100
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(20, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.top_items")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "04_top_items.csv"), index=False)

        print("[SUCCESS] 任务 4 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 4 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
