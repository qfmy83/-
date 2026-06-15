"""
分析任务 8: RFM 用户分群
R(Recency): 最近一次购买距数据集结束日期的天数（越小越近）
F(Frequency): 购买总次数（越大越好）
M(Monetary): 购买次数 + 加购次数*0.3 加权代替（数据集无金额字段）
评分规则: 各维度按"中位数"和"中位数×2"两道阈值划分 1/2/3 三档，得到 3^3 = 27 类组合
分群标签: 简化为 8 类经典 RFM 用户标签
输出: ads.user_rfm + ads.rfm_summary + CSV
运行: spark-submit analysis/08_rfm.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
from config import get_spark_session, OUTPUT_CSV_DIR, DATE_END
from pyspark.sql import functions as F


def main():
    spark = get_spark_session("Analysis_08_RFM")
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS ads")

        print("=" * 60)
        print("分析任务 8: RFM 用户分群")
        print("=" * 60)

        # 计算 R、F、M 值（仅针对至少有一次购买行为的用户，HAVING 过滤）
        # DATEDIFF 用 DATE_END 作为参考点（数据集结束日期），保证 R 值非负
        rfm_raw = spark.sql(f"""
            SELECT
                user_id,
                DATEDIFF('{DATE_END}', MAX(CASE WHEN behavior = 'buy' THEN event_date END)) AS recency,
                SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS frequency,
                ROUND(SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END)
                    + SUM(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) * 0.3, 2) AS monetary
            FROM dwd.user_behavior_detail
            GROUP BY user_id
            HAVING SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) > 0
        """)

        rfm_raw.cache()
        raw_count = rfm_raw.count()
        if raw_count == 0:
            print("[WARN] 无任何用户产生购买行为，RFM 分析跳过（可能因为样本数据时间窗口过窄）。")
            return
        print(f"[INFO] 参与 RFM 分析的购买用户数: {raw_count:,}")

        rfm_raw.createOrReplaceTempView("rfm_raw")

        # 计算中位数作为阈值。percentile_approx 在样本极少时可能返回 None，需做防御
        medians = rfm_raw.selectExpr(
            "percentile_approx(recency, 0.5) AS r_median",
            "percentile_approx(frequency, 0.5) AS f_median",
            "percentile_approx(monetary, 0.5) AS m_median"
        ).collect()[0]

        # 兜底：若中位数为 None 或 0，按业务给一个保守阈值，避免 SQL 拼接失败
        r_med = medians["r_median"] if medians["r_median"] is not None else 1
        f_med = medians["f_median"] if medians["f_median"] is not None and medians["f_median"] > 0 else 1
        m_med = float(medians["m_median"]) if medians["m_median"] is not None and medians["m_median"] > 0 else 1.0

        print(f"[INFO] RFM 中位数 - R: {r_med}, F: {f_med}, M: {m_med}")

        # RFM 评分：每个维度按"<= 中位数"得 3 分，"<= 中位数*2"得 2 分，否则 1 分
        # R 越小越好（最近购买），F、M 越大越好
        rfm_scored = spark.sql(f"""
            SELECT
                user_id, recency, frequency, monetary,
                CASE WHEN recency <= {r_med} THEN 3
                     WHEN recency <= {r_med * 2} THEN 2 ELSE 1 END AS r_score,
                CASE WHEN frequency >= {f_med * 2} THEN 3
                     WHEN frequency >= {f_med} THEN 2 ELSE 1 END AS f_score,
                CASE WHEN monetary >= {m_med * 2} THEN 3
                     WHEN monetary >= {m_med} THEN 2 ELSE 1 END AS m_score
            FROM rfm_raw
        """)

        # 8 类经典 RFM 标签：通过 r/f/m 三个维度的高低组合
        # 行业惯例：M 高 = "重要"，M 低 = "一般"；R 高 + F 高 = "价值"
        rfm_result = rfm_scored.withColumn("segment",
            F.when((F.col("r_score") >= 2) & (F.col("f_score") >= 2) & (F.col("m_score") >= 2), "重要价值客户")
            .when((F.col("r_score") >= 2) & (F.col("f_score") < 2) & (F.col("m_score") >= 2), "重要发展客户")
            .when((F.col("r_score") < 2) & (F.col("f_score") >= 2) & (F.col("m_score") >= 2), "重要保持客户")
            .when((F.col("r_score") < 2) & (F.col("f_score") < 2) & (F.col("m_score") >= 2), "重要挽留客户")
            .when((F.col("r_score") >= 2) & (F.col("f_score") >= 2) & (F.col("m_score") < 2), "一般价值客户")
            .when((F.col("r_score") >= 2) & (F.col("f_score") < 2) & (F.col("m_score") < 2), "一般发展客户")
            .when((F.col("r_score") < 2) & (F.col("f_score") >= 2) & (F.col("m_score") < 2), "一般保持客户")
            .otherwise("一般挽留客户")
        )

        rfm_result.write.mode("overwrite").saveAsTable("ads.user_rfm")

        # 分群汇总：每类用户的人数和 R/F/M 平均值
        summary = rfm_result.groupBy("segment").agg(
            F.count("*").alias("user_count"),
            F.round(F.avg("recency"), 2).alias("avg_recency"),
            F.round(F.avg("frequency"), 2).alias("avg_frequency"),
            F.round(F.avg("monetary"), 2).alias("avg_monetary")
        ).orderBy(F.desc("user_count"))

        summary.show(truncate=False)
        summary.write.mode("overwrite").saveAsTable("ads.rfm_summary")

        os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
        summary.toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "08_rfm_summary.csv"), index=False)
        # detail 表只导前 500 行，避免单 CSV 过大
        rfm_result.limit(500).toPandas().to_csv(os.path.join(OUTPUT_CSV_DIR, "08_rfm_detail.csv"), index=False)

        rfm_raw.unpersist()
        print("[SUCCESS] 任务 8 完成！")
    except Exception as e:
        print(f"[ERROR] 任务 8 失败: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
