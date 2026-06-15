"""
Kafka + Spark Structured Streaming 实时统计脚本。
从 Kafka 读取 JSON 格式的用户行为数据，并在控制台输出滚动窗口 PV/UV 统计结果。
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType


def main():
    project_home = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    checkpoint_dir = os.path.join(project_home, "logs", "streaming_checkpoint", "pv_uv")
    os.makedirs(checkpoint_dir, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("KafkaSparkStreamingRealtimePV")
        .master("local[*]")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    print("=" * 60)
    print("Spark Structured Streaming: realtime PV/UV stats")
    print("=" * 60)

    schema = StructType(
        [
            StructField("user_id", LongType(), True),
            StructField("item_id", LongType(), True),
            StructField("category_id", LongType(), True),
            StructField("behavior", StringType(), True),
            StructField("timestamp", LongType(), True),
        ]
    )

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "user_behavior")
        .option("startingOffsets", "latest")
        .load()
    )

    parsed_df = (
        kafka_df.selectExpr("CAST(value AS STRING) AS json_str")
        .select(F.from_json(F.col("json_str"), schema).alias("data"))
        .select("data.*")
        .withColumn("event_time", F.from_unixtime(F.col("timestamp")).cast("timestamp"))
    )

    # 在当前流式窗口聚合写法下，Spark Structured Streaming 不支持精确 countDistinct。
    # 这里使用近似去重统计 UV，保证实时任务可以持续运行。
    windowed_stats = (
        parsed_df.withWatermark("event_time", "30 seconds")
        .groupBy(F.window("event_time", "30 seconds", "10 seconds"), "behavior")
        .agg(
            F.count("*").alias("count"),
            F.approx_count_distinct("user_id").alias("unique_users"),
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "behavior",
            "count",
            "unique_users",
        )
    )

    query = (
        windowed_stats.writeStream
        .outputMode("update")
        .format("console")
        .option("checkpointLocation", checkpoint_dir)
        .option("truncate", "false")
        .option("numRows", 50)
        .trigger(processingTime="10 seconds")
        .start()
    )

    print("[INFO] Streaming query started. Waiting for Kafka data...")
    print(f"[INFO] Checkpoint: {checkpoint_dir}")
    print("[INFO] UV uses approximate distinct count for streaming compatibility.")
    print("[INFO] Start the producer in another terminal.")
    print("[INFO] Press Ctrl+C to stop.")

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping streaming query...")
        query.stop()
        spark.stop()
        print("[DONE] Stopped.")


if __name__ == "__main__":
    main()
