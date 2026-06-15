"""
公共配置模块 - 各模块共享的 SparkSession 创建和配置
"""

from pyspark.sql import SparkSession
import os


def get_spark_session(app_name="BigDataCoursework"):
    """
    创建并返回带有 Hive 支持的 SparkSession
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "32") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .enableHiveSupport() \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark


# 项目根目录
PROJECT_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(PROJECT_HOME, "data")

# 输出目录
OUTPUT_CSV_DIR = os.path.join(PROJECT_HOME, "output", "csv")
OUTPUT_HTML_DIR = os.path.join(PROJECT_HOME, "output", "html")

# HDFS 路径
HDFS_RAW_PATH = "/data/raw"
HDFS_ODS_PATH = "/data/ods/user_behavior"

# 数据集时间范围
DATE_START = "2017-11-25"
DATE_END = "2017-12-03"
