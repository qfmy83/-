-- ============================================================
-- 文件: 04_dws_tables.sql
-- 说明: DWS 汇总数据层建表（多维聚合）
-- 使用: hive -f sql/04_dws_tables.sql
-- ============================================================

USE dws;

-- 用户日维度汇总表
DROP TABLE IF EXISTS user_daily_behavior;
CREATE TABLE user_daily_behavior (
    user_id      BIGINT   COMMENT '用户ID',
    event_date   STRING   COMMENT '日期',
    pv_count     BIGINT   COMMENT '浏览次数',
    fav_count    BIGINT   COMMENT '收藏次数',
    cart_count   BIGINT   COMMENT '加购次数',
    buy_count    BIGINT   COMMENT '购买次数'
) STORED AS PARQUET;

-- 商品日维度汇总表
DROP TABLE IF EXISTS item_daily_behavior;
CREATE TABLE item_daily_behavior (
    item_id      BIGINT   COMMENT '商品ID',
    event_date   STRING   COMMENT '日期',
    pv_count     BIGINT   COMMENT '浏览次数',
    fav_count    BIGINT   COMMENT '收藏次数',
    cart_count   BIGINT   COMMENT '加购次数',
    buy_count    BIGINT   COMMENT '购买次数'
) STORED AS PARQUET;

-- 类目日维度汇总表
DROP TABLE IF EXISTS category_daily_behavior;
CREATE TABLE category_daily_behavior (
    category_id  BIGINT   COMMENT '类目ID',
    event_date   STRING   COMMENT '日期',
    pv_count     BIGINT   COMMENT '浏览次数',
    fav_count    BIGINT   COMMENT '收藏次数',
    cart_count   BIGINT   COMMENT '加购次数',
    buy_count    BIGINT   COMMENT '购买次数'
) STORED AS PARQUET;

-- 小时维度汇总表
DROP TABLE IF EXISTS hourly_behavior;
CREATE TABLE hourly_behavior (
    event_date   STRING   COMMENT '日期',
    event_hour   INT      COMMENT '小时 0-23',
    pv_count     BIGINT   COMMENT '浏览次数',
    fav_count    BIGINT   COMMENT '收藏次数',
    cart_count   BIGINT   COMMENT '加购次数',
    buy_count    BIGINT   COMMENT '购买次数',
    uv_count     BIGINT   COMMENT '独立用户数'
) STORED AS PARQUET;
