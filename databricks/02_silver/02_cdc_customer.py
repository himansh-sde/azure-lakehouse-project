# Databricks notebook source
# Databricks notebook source
# databricks/02_silver/02_cdc_customer.py

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

from delta.tables import DeltaTable
from pyspark.sql.functions import col, current_timestamp, lower, trim

# 4. Define paths
storage_account = "stalakehousedev"
bronze_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/saleslt/customer/"
silver_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/saleslt/customer/"

# 5. Read the latest increment from Bronze
df_updates = (spark.read.parquet(bronze_path)
    .filter(col("CustomerID").isNotNull())
    .withColumn("EmailAddress", lower(trim(col("EmailAddress"))))
    .withColumn("SilverLoadDate", current_timestamp())
)

# 6. Perform the UPSERT (Merge) into the Silver Delta Table
if DeltaTable.isDeltaTable(spark, silver_path):
    target_table = DeltaTable.forPath(spark, silver_path)
    
    (target_table.alias("target")
        .merge(
            df_updates.alias("source"),
            "target.CustomerID = source.CustomerID" # The unique matching key
        )
        .whenMatchedUpdateAll() # If ID exists, update the record
        .whenNotMatchedInsertAll() # If ID is new, insert the record
        .execute()
    )
    print("✅ Incremental CDC Merge completed successfully.")
else:
    # Fallback for the very first time the table is created
    df_updates.write.format("delta").mode("overwrite").save(silver_path)
    print("✅ Initial Silver Delta table created.")