-- ============================================================
-- 文件: 02_ods_tables.sql
-- 说明: ODS 原始数据层
--
--   ODS 层表 ods.user_behavior 由 etl/01_load_to_ods.py 通过 Spark
--   df.write.saveAsTable("ods.user_behavior") 创建，Schema 与 CSV 字段一致：
--     user_id BIGINT, item_id BIGINT, category_id BIGINT,
--     behavior STRING, `timestamp` BIGINT
--   存储格式 Parquet（Spark 默认），由 Hive Metastore 统一管理。
-- ============================================================

USE ods;

-- 该数据库由 01_create_databases.sql 创建；ODS 表由 ETL 程序写入时自动建立。
SHOW TABLES;
