# 基于 Hadoop、Spark、Kafka 和 Hive 的用户购物行为分析
> 大数据编程课程设计

## 一、项目简介
本项目以阿里天池公开发布的 **UserBehavior** 数据集（截取 3000 万行，约 1.02 GB）为分析对象，基于 **Hadoop HDFS**（分布式存储）、**Hive**（数据仓库）、**Spark**（分布式计算）和 **Kafka**（消息中间件）四个分布式框架，搭建了一个完整的用户购物行为分析平台。平台覆盖数据准备 -> 四层数据仓库建模 -> ETL 清洗 -> 12 个离线分析任务 -> 实时流处理 -> 可视化的全流程。

## 二、技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Ubuntu | 22.04 LTS | 操作系统 |
| JDK | 1.8 | Java 运行环境 |
| Hadoop | 3.3.6 | HDFS 分布式文件系统 + YARN 资源调度 |
| Hive | 3.1.3 | 数据仓库（ODS / DWD / DWS / ADS 四层） |
| Spark | 3.5.0 | PySpark + Spark SQL + Structured Streaming |
| Kafka | 3.x | 实时消息中间件 |
| Zookeeper | 3.x | Kafka 元数据协调 |
| Derby | 嵌入式 | Hive Metastore 后端 |
| Python | 3.10 | PySpark / Pyecharts / Matplotlib |

## 三、数据集

| 项目 | 内容 |
|----|------|
| 名称 | UserBehavior |
| 来源 | 阿里天池 https://tianchi.aliyun.com/dataset/649 |
| 时间窗口 | 2017-11-25 至 2017-12-03（9 天） |
| 实验规模 | 3000 万行 / 约 1.02 GB |
| 字段 | user_id, item_id, category_id, behavior, timestamp |
| 行为类型 | pv（浏览）/ fav（收藏）/ cart（加购）/ buy（购买） |

## 四、项目结构
```text
bigdatacty1/
├── README.md                         项目说明、运行步骤与指标说明
├── derby.log                         Hive Derby Metastore 本地日志
├── data/                              原始数据目录
│   └── UserBehavior.csv               3000 万行用户行为 CSV 数据
├── sql/                               Hive 数据库和数仓表 DDL
│   ├── 01_create_databases.sql        创建 ods/dwd/dws/ads 四层数据库
│   ├── 02_ods_tables.sql              ODS 层说明，实际 ODS 表由 Spark 写入创建
│   ├── 03_dwd_tables.sql              DWD 明细层表结构与分区设计
│   ├── 04_dws_tables.sql              DWS 汇总层四张聚合表结构
│   └── 05_ads_tables.sql              ADS 应用层分析结果表结构
├── etl/                               离线 ETL 处理脚本
│   ├── config.py                      SparkSession、HDFS 路径、日期范围等公共配置
│   ├── 01_load_to_ods.py              读取 HDFS CSV 并写入 ods.user_behavior
│   ├── 02_ods_to_dwd.py               ODS 到 DWD，完成清洗、去重和时间维度增强
│   └── 03_dwd_to_dws.py               DWD 到 DWS，生成用户/商品/类目/小时汇总表
├── analysis/                          12 个离线分析任务
│   ├── 01_daily_pv_uv.py              每日 PV/UV 趋势分析
│   ├── 02_hour_distribution.py        24 小时活跃分布分析
│   ├── 03_behavior_funnel.py          用户行为转化漏斗分析
│   ├── 04_top_items.py                TOP100 热门商品分析
│   ├── 05_top_categories.py           TOP20 热门类目及转化率分析
│   ├── 06_weekday_weekend.py          工作日与周末行为对比
│   ├── 07_retention.py                用户留存分析
│   ├── 08_rfm.py                      RFM 用户分群分析
│   ├── 09_user_path.py                用户行为路径分析
│   ├── 10_heatmap_hour_dow.py         24 小时 × 7 天行为热力图分析
│   ├── 11_repurchase.py               用户复购次数分布分析
│   └── 12_category_top_items.py       TOP 类目内热门商品分析
├── kafka/                             Kafka 实时流演示模块
│   ├── kafka_producer.py              读取 CSV 并向 user_behavior Topic 发送 JSON 消息
│   ├── kafka_consumer_hdfs.py         可选：消费 Kafka 消息并按批次写入 HDFS
│   └── spark_streaming_pv.py          Spark Structured Streaming 实时 PV/UV 统计
├── visualization/                     可视化生成模块
│   ├── utils.py                       CSV 读取、路径创建等公共工具函数
│   ├── viz_all.py                     生成 Pyecharts 交互式 HTML 图表和 Dashboard
│   └── draw_png_local.py              生成 Matplotlib 静态 PNG 图表
├── output/                            分析和可视化输出目录
│   ├── csv/                           ADS 分析结果导出的 CSV 文件
│   ├── html/                          Pyecharts 交互式 HTML 图表
│   └── png/                           Matplotlib 静态 PNG 图表
└── logs/                              运行日志和校验结果
    ├── pipeline/                      主流程及各阶段脚本运行日志
    ├── streaming_checkpoint/          Structured Streaming 检查点目录
    ├── verification/                  Hive 校验查询输出
    └── system/                        Hadoop、Hive、Kafka 等系统服务日志
```

## 五、四层数据仓库
```text
ODS（原始层） -> DWD（明细层） -> DWS（汇总层） -> ADS（应用层） -> 可视化
```

| 层级 | 表数 | 职责 |
|------|------|------|
| ODS | 1 | 与 CSV 字段一一对应，保留原始数据，仅做类型转换 |
| DWD | 1 | 5 步清洗 + 派生 event_hour / day_of_week / is_weekend 三个时间维度，按 event_date 分区 |
| DWS | 4 | 用户×日、商品×日、类目×日、日×小时四个维度的多维聚合 |
| ADS | 13 | 12 个分析任务对应的应用层结果表（RFM 任务输出 2 张） |

全部表统一使用 Parquet 列式存储 + Snappy 压缩。

## 六、运行步骤
> 环境要求：Ubuntu 22.04 + Hadoop 3.3.6 + Hive 3.1.3 + Spark 3.5.0 + Kafka；HDFS / YARN / Zookeeper / Kafka / Hive Metastore 全部启动；项目根目录 `~/bigdatacty1/`。

### 1. 建库建表（Hive）

```bash
hive -f sql/01_create_databases.sql
hive -f sql/03_dwd_tables.sql
hive -f sql/04_dws_tables.sql
hive -f sql/05_ads_tables.sql
# ODS 表由 ETL 程序写入时自动建立，无需 DDL
```

### 2. 数据准备：把 CSV 上传到 HDFS

```bash
hdfs dfs -mkdir -p /data/raw
hdfs dfs -put data/UserBehavior.csv /data/raw/
```

### 3. ETL 三步

```bash
spark-submit etl/01_load_to_ods.py     # CSV -> ODS
spark-submit etl/02_ods_to_dwd.py      # ODS -> DWD
spark-submit etl/03_dwd_to_dws.py      # DWD -> DWS
```

### 4. 12 个离线分析任务
```bash
for f in analysis/0?_*.py analysis/1?_*.py; do
    spark-submit "$f"
done
```

也可单独运行任一任务，例如：

```bash
spark-submit analysis/08_rfm.py
```

### 5. Kafka 实时流演示
```bash
# 终端 1：创建 Topic
kafka-topics.sh --create --topic user_behavior --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# 终端 2：先启动 Spark Structured Streaming
rm -rf logs/streaming_checkpoint/pv_uv
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 kafka/spark_streaming_pv.py

# 可选：如需演示 Kafka -> HDFS 落盘，另开终端启动 HDFS Consumer
python kafka/kafka_consumer_hdfs.py

# 终端 3：再启动 Producer（默认 5w 条演示模式）
python kafka/kafka_producer.py
```

`kafka_producer.py` 支持多种启动模式：

```bash
# 默认 5w 条
python kafka/kafka_producer.py

# 50w 条
KAFKA_MAX_MESSAGES=500000 KAFKA_SEND_RATE=2000 python kafka/kafka_producer.py

# 3000w 条
KAFKA_MAX_MESSAGES=30000000 KAFKA_SEND_RATE=5000 python kafka/kafka_producer.py

# 按文件全部行发送
KAFKA_MAX_MESSAGES=0 KAFKA_SEND_RATE=5000 python kafka/kafka_producer.py
```

### 6. 生成可视化
```bash
python visualization/viz_all.py
python visualization/draw_png_local.py
```

### 7. 查看结果

```bash
# 浏览器打开综合 Dashboard
firefox output/html/dashboard.html

# Hive 查询验证
hive -e "SELECT * FROM ads.daily_pv_uv ORDER BY event_date;"
hive -e "SELECT * FROM ads.behavior_funnel;"
hive -e "SELECT * FROM ads.rfm_summary;"
```

## 七、12 个分析任务一览
| # | 任务 | 关键技术 | 输出表 |
|---|------|---------|--------|
| 1 | 每日 PV/UV 趋势 | COUNT(DISTINCT) 聚合 | ads.daily_pv_uv |
| 2 | 24 小时活跃分布 | GROUP BY event_hour | ads.hourly_distribution |
| 3 | 用户行为转化漏斗 | 各阶段 DISTINCT 用户 + 转化率 | ads.behavior_funnel |
| 4 | TOP100 热门商品 | 加权评分 pv×1+fav×3+cart×5+buy×10 | ads.top_items |
| 5 | TOP20 热门类目 | PV + 转化率 buy/pv | ads.top_categories |
| 6 | 工作日 vs 周末 | 按 is_weekend 派生字段 | ads.weekday_vs_weekend |
| 7 | 用户留存 | 自连接 + DATEDIFF | ads.retention |
| 8 | RFM 用户分群 | percentile_approx + 8 类标签 | ads.user_rfm / ads.rfm_summary |
| 9 | 用户行为路径 | LAG 窗口函数 | ads.user_path |
| 10 | 24h × 7d 热力图 | day_of_week × event_hour 双维聚合 | ads.heatmap_hour_dow |
| 11 | 用户复购率分布 | 用户购买次数分桶 | ads.repurchase_distribution |
| 12 | 类目内 TOP 商品 | 嵌套 ROW_NUMBER 窗口函数 | ads.category_top_items |
| 实时 | Kafka 实时 PV/UV | Spark Structured Streaming | 流式输出到控制台 |
| 可选 | Kafka 消息落 HDFS | kafka-python Consumer | /data/kafka_output |

## 八、关键运行数据
- 数据规模：ODS 30,000,000 行 -> DWD 29,983,682 行，入库率 99.95%
- 活跃用户：995,575；商品：2,615,769；类目：8,805
- 行为分布：pv 89.53% / cart 5.56% / fav 2.90% / buy 2.00%
- 全流程总耗时：约 13 分 33 秒（2 核 / 7.7 GiB 环境实测）

详细数据见 `logs/verification/` 中的验证查询结果文件。
