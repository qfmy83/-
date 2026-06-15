"""
ETL 步骤 2: ODS → DWD（数据清洗 + 维度增强）
功能: 时间戳转换、去重、过滤异常、衍生时间字段、按日期分区写入
运行: spark-submit etl/02_ods_to_dwd.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_spark_session, DATE_START, DATE_END
from pyspark.sql import functions as F


def main():
    spark = get_spark_session("ETL_02_ODS_to_DWD")
    try:
        print("=" * 60)
        print("ETL 步骤 2: ODS → DWD 数据清洗与维度增强")
        print("=" * 60)

        # 读取 ODS 数据；先 cache 避免后续多次 count 触发重复计算
        df = spark.sql("SELECT * FROM ods.user_behavior").cache()
        raw_count = df.count()
        print(f"[INFO] ODS 原始记录数: {raw_count:,}")
        if raw_count == 0:
            print("[ERROR] ODS 层无数据，请先运行 ETL 步骤 1")
            return

        # ============ 数据清洗：5 步漏斗式过滤 ============

        # 1) 删除空值（任一字段为 null 都丢弃，保证下游聚合不出错）
        df_clean = df.dropna()
        after_null = df_clean.count()
        null_removed = raw_count - after_null
        print(f"[INFO] 删除空值: {null_removed:,} 条")

        # 2) 过滤非法行为（数据集中可能混入未知行为标签，统一只保留 4 类）
        valid_behaviors = ['pv', 'cart', 'fav', 'buy']
        df_clean = df_clean.filter(F.col("behavior").isin(valid_behaviors))
        after_behavior = df_clean.count()
        behavior_removed = after_null - after_behavior
        print(f"[INFO] 删除非法行为类型: {behavior_removed:,} 条")

        # 3) 时间戳转换：UNIX 秒 → 字符串日期/日期时间，方便后续按日期分区与按小时聚合
        df_clean = df_clean.withColumn(
            "event_time", F.from_unixtime(F.col("timestamp"), "yyyy-MM-dd HH:mm:ss")
        ).withColumn(
            "event_date", F.from_unixtime(F.col("timestamp"), "yyyy-MM-dd")
        )

        # 4) 过滤时间范围（数据集官方时间窗口外的属于脏数据）
        df_clean = df_clean.filter(
            (F.col("event_date") >= DATE_START) &
            (F.col("event_date") <= DATE_END)
        )
        after_date = df_clean.count()
        date_removed = after_behavior - after_date
        print(f"[INFO] 删除超出时间范围的记录: {date_removed:,} 条")

        # 5) 去重：同一用户对同一商品在同一秒发出相同行为视为重复，仅保留一条
        df_clean = df_clean.dropDuplicates(["user_id", "item_id", "behavior", "timestamp"])
        df_clean.cache()
        after_dedup = df_clean.count()
        dedup_removed = after_date - after_dedup
        print(f"[INFO] 删除重复记录: {dedup_removed:,} 条")

        # ============ 维度增强：派生 3 个时间维度字段供下游分析直接使用 ============
        # event_hour：24 小时活跃分布分析需要
        # day_of_week：1=周日 ... 7=周六（Spark dayofweek 内置语义）
        # is_weekend：周末/工作日对比分析需要

        df_dwd = df_clean.select(
            F.col("user_id"),
            F.col("item_id"),
            F.col("category_id"),
            F.col("behavior"),
            F.col("event_time"),
            F.hour(F.col("event_time")).alias("event_hour"),
            F.dayofweek(F.col("event_time")).alias("day_of_week"),
            F.when(F.dayofweek(F.col("event_time")).isin([1, 7]), 1).otherwise(0).alias("is_weekend"),
            F.col("event_date")
        )

        # ============ 写入 DWD 层（按 event_date 分区 + Parquet 列式压缩） ============
        # 按日期分区的好处：分析任务大多带 event_date 过滤，分区裁剪可跳过无关文件
        spark.sql("CREATE DATABASE IF NOT EXISTS dwd")
        spark.sql("DROP TABLE IF EXISTS dwd.user_behavior_detail")

        print("[INFO] 正在写入 DWD 层（按日期分区，Parquet+Snappy）...")
        df_dwd.write \
            .mode("overwrite") \
            .partitionBy("event_date") \
            .saveAsTable("dwd.user_behavior_detail")

        # ============ 数据质量报告 ============
        final_count = spark.sql("SELECT COUNT(*) AS cnt FROM dwd.user_behavior_detail").collect()[0]["cnt"]

        print("\n" + "=" * 60)
        print("数据质量报告")
        print("=" * 60)
        print(f"  原始记录数:         {raw_count:>15,}")
        print(f"  空值删除:           {null_removed:>15,}")
        print(f"  非法行为删除:       {behavior_removed:>15,}")
        print(f"  超时间范围删除:     {date_removed:>15,}")
        print(f"  重复记录删除:       {dedup_removed:>15,}")
        print(f"  最终入库记录数:     {final_count:>15,}")
        print(f"  入库率:             {final_count/raw_count*100:>14.2f}%")
        print("=" * 60)

        print("\n[INFO] 各日期分区数据量:")
        spark.sql("""
            SELECT event_date, COUNT(*) AS cnt
            FROM dwd.user_behavior_detail
            GROUP BY event_date
            ORDER BY event_date
        """).show(20, truncate=False)

        print("[INFO] DWD 数据样本:")
        spark.sql("SELECT * FROM dwd.user_behavior_detail LIMIT 5").show(truncate=False)

        df.unpersist()
        df_clean.unpersist()
        print("[SUCCESS] ETL 步骤 2 完成！DWD 层数据已就绪。")
    except Exception as e:
        print(f"[ERROR] ETL 步骤 2 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
