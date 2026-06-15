"""
分析任务 12: TOP10 类目内 TOP5 商品（嵌套层级）
业务目的: 揭示"哪些类目带火了哪些爆款"，用于品类运营决策
       例如：服装类目 TOP3 商品都是连衣裙 → 重点补货/拓展同类
算法: 第一阶段先取 TOP10 类目；第二阶段在 TOP 类目内用窗口函数 ROW_NUMBER
     按 PV 排名，取 rank<=5 的商品
输出: ads.category_top_items + CSV（共 50 行：10 类目 × 5 商品）
运行: spark-submit analysis/12_category_top_items.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR


def main():
    spark = get_spark_session("Analysis_12_CategoryTopItems")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 12: TOP10 类目内 TOP5 商品")
        print("=" * 60)

        # CTE 1: 取浏览量 TOP10 的类目（业务上小类目噪声大，先过滤）
        # CTE 2: 在这些类目内，按"商品 PV"用 ROW_NUMBER() PARTITION BY 排名
        # 外层：只保留每个类目的 TOP5 商品
        result = spark.sql("""
            WITH top_cats AS (
                SELECT category_id,
                       SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END) AS category_pv
                FROM dwd.user_behavior_detail
                GROUP BY category_id
                ORDER BY category_pv DESC
                LIMIT 10
            ),
            item_in_cat AS (
                SELECT
                    d.category_id,
                    d.item_id,
                    SUM(CASE WHEN d.behavior = 'pv' THEN 1 ELSE 0 END) AS item_pv,
                    SUM(CASE WHEN d.behavior = 'buy' THEN 1 ELSE 0 END) AS item_buy
                FROM dwd.user_behavior_detail d
                JOIN top_cats c ON d.category_id = c.category_id
                GROUP BY d.category_id, d.item_id
            ),
            ranked AS (
                SELECT
                    i.category_id,
                    c.category_pv,
                    i.item_id,
                    i.item_pv,
                    i.item_buy,
                    ROW_NUMBER() OVER (PARTITION BY i.category_id ORDER BY i.item_pv DESC) AS rank_in_category
                FROM item_in_cat i
                JOIN top_cats c ON i.category_id = c.category_id
            )
            SELECT category_id, category_pv, item_id, item_pv, item_buy, rank_in_category
            FROM ranked
            WHERE rank_in_category <= 5
            ORDER BY category_pv DESC, rank_in_category
        """).cache()

        if result.count() == 0:
            print("[WARN] 分析结果为空")
            return

        result.show(50, truncate=False)
        result.write.mode("overwrite").saveAsTable("ads.category_top_items")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        result.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "12_category_top_items.csv"), index=False)

        print("[SUCCESS] 任务 12 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 12 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
