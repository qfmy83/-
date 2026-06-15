"""
ETL 步骤 1: 将 CSV 原始数据加载到 Hive ODS 层
功能: 读取 HDFS 上的 CSV → 定义 Schema → 写入 Hive ODS 外部表
运行: spark-submit etl/01_load_to_ods.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_spark_session, HDFS_RAW_PATH
from pyspark.sql.types import StructType, StructField, LongType, StringType


def main():
    spark = get_spark_session("ETL_01_LoadToODS")
    try:
        print("=" * 60)
        print("ETL 步骤 1: 加载原始数据到 ODS 层")
        print("=" * 60)

        # 显式定义 Schema 比让 Spark 自动推断更快、更稳——CSV 无表头，
        # 必须显式给定字段名和类型，否则下游引用 user_id 会失败
        schema = StructType([
            StructField("user_id", LongType(), True),
            StructField("item_id", LongType(), True),
            StructField("category_id", LongType(), True),
            StructField("behavior", StringType(), True),
            StructField("timestamp", LongType(), True),
        ])

        # 从 HDFS 读取 CSV 文件（分布式读取，按 block 切分到多个 task）
        csv_path = HDFS_RAW_PATH + "/UserBehavior.csv"
        print(f"[INFO] 正在从 {csv_path} 读取数据...")

        df = spark.read.csv(csv_path, schema=schema, header=False)

        total_count = df.count()
        print(f"[INFO] 读取到 {total_count:,} 条记录")

        if total_count == 0:
            print("[ERROR] 数据为空，请检查 HDFS 文件是否上传成功。")
            return

        spark.sql("CREATE DATABASE IF NOT EXISTS ods")

        # saveAsTable 会自动在 Hive Metastore 注册表，并以 Parquet 列式存储到 warehouse
        # Parquet + Snappy 压缩约为 CSV 的 30%，且支持谓词下推，下游 SQL 速度显著优于 TextFile
        print("[INFO] 正在写入 Hive ODS 层（Parquet 格式，由 Hive Metastore 管理）...")
        df.write.mode("overwrite").saveAsTable("ods.user_behavior")

        # 验证：直接走 Hive 元数据查询，确认表注册成功
        count_check = spark.sql("SELECT COUNT(*) AS cnt FROM ods.user_behavior").collect()[0]["cnt"]
        print(f"[INFO] ODS 层验证: {count_check:,} 条记录")

        print("\n[INFO] 数据样本（前5行）:")
        spark.sql("SELECT * FROM ods.user_behavior LIMIT 5").show(truncate=False)

        print("\n[INFO] 行为类型分布:")
        spark.sql("""
            SELECT behavior, COUNT(*) AS cnt,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
            FROM ods.user_behavior
            GROUP BY behavior
            ORDER BY cnt DESC
        """).show()

        print("[SUCCESS] ETL 步骤 1 完成！ODS 层数据已就绪。")
    except Exception as e:
        print(f"[ERROR] ETL 步骤 1 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
