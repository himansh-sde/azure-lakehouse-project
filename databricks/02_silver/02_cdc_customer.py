# databricks/02_silver/02_cdc_customer.py

from delta.tables import DeltaTable
from pyspark.sql.functions import col, current_timestamp, lower, trim

# 1. Define paths
storage_account = "stalakehousedev"
bronze_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/saleslt/customer/"
silver_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/saleslt/customer/"

# 2. Read the latest increment from Bronze
df_updates = (spark.read.parquet(bronze_path)
    .filter(col("CustomerID").isNotNull())
    .withColumn("EmailAddress", lower(trim(col("EmailAddress"))))
    .withColumn("SilverLoadDate", current_timestamp())
)

# 3. Perform the UPSERT (Merge) into the Silver Delta Table
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
