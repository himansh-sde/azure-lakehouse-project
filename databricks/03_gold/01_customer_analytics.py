# Databricks notebook source
# Databricks notebook source
# databricks/03_gold/01_customer_analytics.py

from pyspark.sql.functions import col, count, when

# 1. Define paths
storage_account = "stalakehousedev"
silver_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/saleslt/customer/"
gold_path = f"abfss://gold@{storage_account}.dfs.core.windows.net/analytics/customer_summary/"

# 2. Read Silver Data
df_silver = spark.read.format("delta").load(silver_path)

# 3. Create Business Aggregations
df_gold = (df_silver
    .groupBy("CompanyName")
    .agg(
        count("CustomerID").alias("TotalCustomers"),
        count(when(col("EmailAddress").isNotNull(), True)).alias("CustomersWithEmail")
    )
    .filter(col("CompanyName").isNotNull())
)

# 4. Write to Gold
(df_gold.write
    .format("delta")
    .mode("overwrite")
    .option("path", gold_path)
    .saveAsTable("gold_customer_summary")
)
print(f"✅ Gold analytics table created at: {gold_path}")

# 5. Senior Best Practice: Performance Tuning
# OPTIMIZE compacts small Parquet files under the hood.
# ZORDER physically clusters the data to skip irrelevant files during queries.
spark.sql(f"OPTIMIZE delta.`{gold_path}` ZORDER BY (CompanyName)")
print("✅ Delta table optimized and Z-Ordered.")