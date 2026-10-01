# databricks/02_silver/01_cleanse_customer.py

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, TimestampType
from pyspark.sql.functions import col, current_timestamp, trim, lower

# 1. Define explicit schema (Senior Best Practice)
customer_schema = StructType([
    StructField("CustomerID", IntegerType(), False),
    StructField("NameStyle", StringType(), True),
    StructField("Title", StringType(), True),
    StructField("FirstName", StringType(), False),
    StructField("MiddleName", StringType(), True),
    StructField("LastName", StringType(), False),
    StructField("Suffix", StringType(), True),
    StructField("CompanyName", StringType(), True),
    StructField("SalesPerson", StringType(), True),
    StructField("EmailAddress", StringType(), True),
    StructField("Phone", StringType(), True),
    StructField("ModifiedDate", TimestampType(), False)
])

# 2. Define storage paths
storage_account = "stalakehousedev"
bronze_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/saleslt/customer/"
silver_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/saleslt/customer/"

# 3. Read Bronze Parquet with enforced schema
df_raw = (spark.read
    .schema(customer_schema)
    .option("badRecordsPath", f"abfss://bronze@{storage_account}.dfs.core.windows.net/bad_records/customer/") 
    .parquet(bronze_path)
)

# 4. Cleansing Transformations
df_clean = (df_raw
    .dropDuplicates(["CustomerID", "ModifiedDate"]) # Handle duplicate events
    .filter(col("CustomerID").isNotNull())          # Drop phantom records
    .withColumn("EmailAddress", lower(trim(col("EmailAddress")))) # Standardize text
    .withColumn("SilverLoadDate", current_timestamp())            # Audit column
)

# 5. Write to Silver as a Delta Table
# Using mode("overwrite") for the initial baseline load. 
# Day 5 will cover the incremental UPSERT (MERGE) logic.
(df_clean.write
    .format("delta")
    .mode("overwrite")
    .option("path", silver_path)
    .saveAsTable("silver_customer") # Registers in Unity Catalog / Hive Metastore
)

print(f"✅ Customer data successfully cleansed and written to Silver Delta at: {silver_path}")
