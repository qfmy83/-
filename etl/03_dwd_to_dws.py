"""
ETL 步骤 3: DWD → DWS（多维聚合汇总）
功能: 按 用户×日、商品×日、类目×日、日×小时 四个维度聚合
运行: spark-submit etl/03_dwd_to_dws.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_spark_session
from pyspark.sql import functions as F


def main():
    spark = get_spark_session("ETL_03_DWD_to_DWS")
    try:
        print("=" * 60)
        print("ETL 步骤 3: DWD → DWS 多维聚合汇总")
        print("=" * 60)

        spark.sql("CREATE DATABASE IF NOT EXISTS dws")

        # cache DWD 数据，4 个聚合都基于同一份明细，避免重复扫描分布式存储
        dwd = spark.sql("SELECT * FROM dwd.user_behavior_detail").cache()
        dwd_count = dwd.count()
        print(f"[INFO] DWD 层记录数: {dwd_count:,}")
        if dwd_count == 0:
            print("[ERROR] DWD 层无数据，请先运行 ETL 步骤 2")
            return

        # ============ 1) 用户×日 维度汇总 ============
        # 用 SUM(CASE WHEN) 而不是多次 filter+groupBy，是为了一次 shuffle 同时算出 4 个指标
        print("[INFO] 正在聚合: 用户日维度...")
        user_daily = dwd.groupBy("user_id", "event_date").agg(
            F.sum(F.when(F.col("behavior") == "pv", 1).otherwise(0)).alias("pv_count"),
            F.sum(F.when(F.col("behavior") == "fav", 1).otherwise(0)).alias("fav_count"),
            F.sum(F.when(F.col("behavior") == "cart", 1).otherwise(0)).alias("cart_count"),
            F.sum(F.when(F.col("behavior") == "buy", 1).otherwise(0)).alias("buy_count"),
        )
        user_daily.write.mode("overwrite").saveAsTable("dws.user_daily_behavior")
        print(f"  → dws.user_daily_behavior: {user_daily.count():,} 条")

        # ============ 2) 商品×日 维度汇总 ============（供 TOP 商品分析使用）
        print("[INFO] 正在聚合: 商品日维度...")
        item_daily = dwd.groupBy("item_id", "event_date").agg(
            F.sum(F.when(F.col("behavior") == "pv", 1).otherwise(0)).alias("pv_count"),
            F.sum(F.when(F.col("behavior") == "fav", 1).otherwise(0)).alias("fav_count"),
            F.sum(F.when(F.col("behavior") == "cart", 1).otherwise(0)).alias("cart_count"),
            F.sum(F.when(F.col("behavior") == "buy", 1).otherwise(0)).alias("buy_count"),
        )
        item_daily.write.mode("overwrite").saveAsTable("dws.item_daily_behavior")
        print(f"  → dws.item_daily_behavior: {item_daily.count():,} 条")

        # ============ 3) 类目×日 维度汇总 ============（供类目转化率分析使用）
        print("[INFO] 正在聚合: 类目日维度...")
        cat_daily = dwd.groupBy("category_id", "event_date").agg(
            F.sum(F.when(F.col("behavior") == "pv", 1).otherwise(0)).alias("pv_count"),
            F.sum(F.when(F.col("behavior") == "fav", 1).otherwise(0)).alias("fav_count"),
            F.sum(F.when(F.col("behavior") == "cart", 1).otherwise(0)).alias("cart_count"),
            F.sum(F.when(F.col("behavior") == "buy", 1).otherwise(0)).alias("buy_count"),
        )
        cat_daily.write.mode("overwrite").saveAsTable("dws.category_daily_behavior")
        print(f"  → dws.category_daily_behavior: {cat_daily.count():,} 条")

        # ============ 4) 日×小时 维度汇总 ============（供 24 小时活跃分布使用）
        # countDistinct 触发 shuffle，单独一次聚合内即可完成 UV
        print("[INFO] 正在聚合: 小时维度...")
        hourly = dwd.groupBy("event_date", "event_hour").agg(
            F.sum(F.when(F.col("behavior") == "pv", 1).otherwise(0)).alias("pv_count"),
            F.sum(F.when(F.col("behavior") == "fav", 1).otherwise(0)).alias("fav_count"),
            F.sum(F.when(F.col("behavior") == "cart", 1).otherwise(0)).alias("cart_count"),
            F.sum(F.when(F.col("behavior") == "buy", 1).otherwise(0)).alias("buy_count"),
            F.countDistinct("user_id").alias("uv_count"),
        )
        hourly.write.mode("overwrite").saveAsTable("dws.hourly_behavior")
        print(f"  → dws.hourly_behavior: {hourly.count():,} 条")

        dwd.unpersist()
        print("\n[SUCCESS] ETL 步骤 3 完成！DWS 层四张汇总表已就绪。")
    except Exception as e:
        print(f"[ERROR] ETL 步骤 3 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
