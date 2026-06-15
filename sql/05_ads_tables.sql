-- ============================================================
-- 文件: 05_ads_tables.sql
-- 说明: ADS 应用数据层建表（直接给可视化使用）
-- 使用: hive -f sql/05_ads_tables.sql
-- ============================================================

USE ads;

-- 任务1: 每日PV/UV趋势
DROP TABLE IF EXISTS daily_pv_uv;
CREATE TABLE daily_pv_uv (
    event_date   STRING   COMMENT '日期',
    pv           BIGINT   COMMENT '页面浏览量',
    uv           BIGINT   COMMENT '独立访客数',
    item_count   BIGINT   COMMENT '被浏览商品数',
    avg_pv_per_user DOUBLE COMMENT '人均浏览量'
) STORED AS PARQUET;

-- 任务2: 24小时活跃分布
DROP TABLE IF EXISTS hourly_distribution;
CREATE TABLE hourly_distribution (
    event_hour   INT      COMMENT '小时 0-23',
    pv           BIGINT   COMMENT '浏览量',
    uv           BIGINT   COMMENT '独立访客数',
    cart_count   BIGINT   COMMENT '加购数',
    buy_count    BIGINT   COMMENT '购买数'
) STORED AS PARQUET;

-- 任务3: 用户行为转化漏斗
DROP TABLE IF EXISTS behavior_funnel;
CREATE TABLE behavior_funnel (
    behavior     STRING   COMMENT '行为类型',
    user_count   BIGINT   COMMENT '用户数',
    ratio        DOUBLE   COMMENT '相对于上一步的转化率',
    overall_rate DOUBLE   COMMENT '相对于pv的整体转化率'
) STORED AS PARQUET;

-- 任务4: TOP100热门商品
DROP TABLE IF EXISTS top_items;
CREATE TABLE top_items (
    ranking      INT      COMMENT '排名',
    item_id      BIGINT   COMMENT '商品ID',
    pv_count     BIGINT   COMMENT '浏览量',
    fav_count    BIGINT   COMMENT '收藏量',
    cart_count   BIGINT   COMMENT '加购量',
    buy_count    BIGINT   COMMENT '购买量',
    total_score  DOUBLE   COMMENT '综合热度得分'
) STORED AS PARQUET;

-- 任务5: TOP20热门类目
DROP TABLE IF EXISTS top_categories;
CREATE TABLE top_categories (
    ranking        INT      COMMENT '排名',
    category_id    BIGINT   COMMENT '类目ID',
    pv_count       BIGINT   COMMENT '浏览量',
    buy_count      BIGINT   COMMENT '购买量',
    conversion_rate DOUBLE  COMMENT '转化率 buy/pv'
) STORED AS PARQUET;

-- 任务6: 工作日vs周末对比
DROP TABLE IF EXISTS weekday_vs_weekend;
CREATE TABLE weekday_vs_weekend (
    day_type     STRING   COMMENT 'weekday/weekend',
    behavior     STRING   COMMENT '行为类型',
    total_count  BIGINT   COMMENT '行为总数',
    user_count   BIGINT   COMMENT '用户数',
    avg_per_user DOUBLE   COMMENT '人均次数'
) STORED AS PARQUET;

-- 任务7: 用户留存分析
DROP TABLE IF EXISTS retention;
CREATE TABLE retention (
    first_date   STRING   COMMENT '首次活跃日期',
    new_users    BIGINT   COMMENT '该日新增（首次活跃）用户数，作为留存率分母',
    day_1        DOUBLE   COMMENT '次日留存率（%）',
    day_2        DOUBLE   COMMENT '2日留存率（%）',
    day_3        DOUBLE   COMMENT '3日留存率（%）'
) STORED AS PARQUET;

-- 任务8: RFM用户分群
DROP TABLE IF EXISTS user_rfm;
CREATE TABLE user_rfm (
    user_id      BIGINT   COMMENT '用户ID',
    recency      INT      COMMENT 'R值: 最近一次购买距今天数',
    frequency    INT      COMMENT 'F值: 购买总次数',
    monetary     DOUBLE   COMMENT 'M值: 加权消费力',
    r_score      INT      COMMENT 'R评分 1-3',
    f_score      INT      COMMENT 'F评分 1-3',
    m_score      INT      COMMENT 'M评分 1-3',
    segment      STRING   COMMENT '用户分群标签'
) STORED AS PARQUET;

-- RFM分群汇总
DROP TABLE IF EXISTS rfm_summary;
CREATE TABLE rfm_summary (
    segment      STRING   COMMENT '用户分群标签',
    user_count   BIGINT   COMMENT '用户数',
    avg_recency  DOUBLE   COMMENT '平均R值',
    avg_frequency DOUBLE  COMMENT '平均F值',
    avg_monetary DOUBLE   COMMENT '平均M值'
) STORED AS PARQUET;

-- 任务9: 用户行为路径（桑基图）
DROP TABLE IF EXISTS user_path;
CREATE TABLE user_path (
    from_behavior STRING  COMMENT '前一个行为',
    to_behavior   STRING  COMMENT '后一个行为',
    path_count    BIGINT  COMMENT '转移次数',
    path_ratio    DOUBLE  COMMENT '转移概率'
) STORED AS PARQUET;

-- 任务10: 24h × 7d 行为热力图（找下单黄金时段）
DROP TABLE IF EXISTS heatmap_hour_dow;
CREATE TABLE heatmap_hour_dow (
    day_of_week  INT     COMMENT '星期几 1=周日 ... 7=周六',
    event_hour   INT     COMMENT '小时 0-23',
    pv_count     BIGINT  COMMENT '该时段总浏览量',
    buy_count    BIGINT  COMMENT '该时段总购买量',
    active_users BIGINT  COMMENT '该时段活跃用户数（去重）'
) STORED AS PARQUET;

-- 任务11: 用户复购率分布（看会员价值长尾，验证二八定律）
DROP TABLE IF EXISTS repurchase_distribution;
CREATE TABLE repurchase_distribution (
    buy_times_bucket  STRING  COMMENT '购买次数分桶 1次/2次/3-5次/6-10次/11次以上',
    bucket_order      INT     COMMENT '分桶展示顺序（用于排序）',
    user_count        BIGINT  COMMENT '该桶用户数',
    user_ratio        DOUBLE  COMMENT '占购买用户的百分比',
    total_buy         BIGINT  COMMENT '该桶贡献的购买总量',
    buy_contribution  DOUBLE  COMMENT '该桶贡献的购买量百分比'
) STORED AS PARQUET;

-- 任务12: TOP10 类目内 TOP5 商品（嵌套层级，用于树状图 TreeMap）
DROP TABLE IF EXISTS category_top_items;
CREATE TABLE category_top_items (
    category_id      BIGINT  COMMENT '类目ID',
    category_pv      BIGINT  COMMENT '类目总浏览量（树状图父节点大小）',
    item_id          BIGINT  COMMENT '商品ID',
    item_pv          BIGINT  COMMENT '商品浏览量（树状图叶节点大小）',
    item_buy         BIGINT  COMMENT '商品购买量',
    rank_in_category INT     COMMENT '商品在类目内浏览量排名 1-5'
) STORED AS PARQUET;
