# databricks/01_bronze/00_auth_setup.py

# 1. Define variables
storage_account_name = "stalakehousedev"
secret_scope = "kv-lakehouse-scope"

# 2. Fetch secrets directly from Azure Key Vault
client_id = dbutils.secrets.get(scope=secret_scope, key="sp-client-id")
tenant_id = dbutils.secrets.get(scope=secret_scope, key="sp-tenant-id")
client_secret = dbutils.secrets.get(scope=secret_scope, key="sp-client-secret")

# 3. Configure Spark Session for direct ABFSS access (Senior Best Practice)
spark.conf.set(f"fs.azure.account.auth.type.{storage_account_name}.dfs.core.windows.net", "OAuth")
spark.conf.set(f"fs.azure.account.oauth.provider.type.{storage_account_name}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
spark.conf.set(f"fs.azure.account.oauth2.client.id.{storage_account_name}.dfs.core.windows.net", client_id)
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{storage_account_name}.dfs.core.windows.net", client_secret)
spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{storage_account_name}.dfs.core.windows.net", f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")

print("✅ Spark session successfully authenticated with Azure Data Lake using Service Principal.")

# 4. (Optional Test) List the Bronze directory to verify access
# display(dbutils.fs.ls(f"abfss://bronze@{storage_account_name}.dfs.core.windows.net/"))
