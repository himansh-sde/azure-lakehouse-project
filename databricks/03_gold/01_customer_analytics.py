# Databricks notebook source
# Databricks notebook source
# databricks/03_gold/01_customer_analytics.py

# 1. Define storage account
storage_account = "stalakehousedev"

# 2. Fetch all Service Principal details dynamically from Key Vault
client_id = dbutils.secrets.get(scope="kv-lakehouse-scope", key="sp-client-id")
tenant_id = dbutils.secrets.get(scope="kv-lakehouse-scope", key="sp-tenant-id")
sp_secret = dbutils.secrets.get(scope="kv-lakehouse-scope", key="sp-client-secret")

# 3. Authenticate the Spark session using OAuth and the Service Principal
spark.conf.set(f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net", "OAuth")
spark.conf.set(f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
spark.conf.set(f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net", client_id)
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net", sp_secret)
spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net", f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")

from pyspark.sql.functions import col, count, when

# 4. Define paths
storage_account = "stalakehousedev"
silver_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/saleslt/customer/"
gold_path = f"abfss://gold@{storage_account}.dfs.core.windows.net/analytics/customer_summary/"

# 5. Read Silver Data
df_silver = spark.read.format("delta").load(silver_path)

# 6. Create Business Aggregations
df_gold = (df_silver
    .groupBy("CompanyName")
    .agg(
        count("CustomerID").alias("TotalCustomers"),
        count(when(col("EmailAddress").isNotNull(), True)).alias("CustomersWithEmail")
    )
    .filter(col("CompanyName").isNotNull())
)

# 7. Write to Gold
(df_gold.write
    .format("delta")
    .mode("overwrite")
    .option("path", gold_path)
    .saveAsTable("gold_customer_summary")
)
print(f"✅ Gold analytics table created at: {gold_path}")

# 8. Senior Best Practice: Performance Tuning
# OPTIMIZE compacts small Parquet files under the hood.
# ZORDER physically clusters the data to skip irrelevant files during queries.
spark.sql(f"OPTIMIZE delta.`{gold_path}` ZORDER BY (CompanyName)")
print("✅ Delta table optimized and Z-Ordered.")