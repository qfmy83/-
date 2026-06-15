-- ============================================================
-- 文件: 03_dwd_tables.sql
-- 说明: DWD 明细数据层建表（清洗后，增加时间维度字段）
-- 使用: hive -f sql/03_dwd_tables.sql
-- ============================================================

USE dwd;

DROP TABLE IF EXISTS user_behavior_detail;

CREATE TABLE user_behavior_detail (
    user_id      BIGINT   COMMENT '用户ID',
    item_id      BIGINT   COMMENT '商品ID',
    category_id  BIGINT   COMMENT '商品类目ID',
    behavior     STRING   COMMENT '行为类型: pv/cart/fav/buy',
    event_time   STRING   COMMENT '事件时间 yyyy-MM-dd HH:mm:ss',
    event_hour   INT      COMMENT '事件发生的小时 0-23',
    day_of_week  INT      COMMENT '星期几 1=周日 ... 7=周六（Spark dayofweek 语义）',
    is_weekend   INT      COMMENT '是否周末 0=否 1=是（周六周日为 1）'
)
PARTITIONED BY (event_date STRING COMMENT '事件日期 yyyy-MM-dd')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression'='SNAPPY');
