# infrastructure/source_db.tf

# 1. Generate a secure random password for the SQL Admin
resource "random_password" "sql_admin_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# 2. Save the SQL Admin password to our existing Key Vault
resource "azurerm_key_vault_secret" "sql_admin_password_secret" {
  name         = "sql-admin-password"
  value        = random_password.sql_admin_password.result
  key_vault_id = azurerm_key_vault.kv.id
  
  depends_on = [
    azurerm_key_vault.kv
  ]
}

# 3. Create the Azure SQL Server
resource "azurerm_mssql_server" "sql_server" {
  name                         = "sqlserver-source-dev-${random_password.sql_admin_password.result != "" ? "986" : "986"}" # Ensure unique naming; replace "123" with your initials/numbers
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = azurerm_resource_group.rg.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = random_password.sql_admin_password.result

  tags = {
    environment = "dev"
  }
}

# 4. Create the Database with the AdventureWorks Sample Data
resource "azurerm_mssql_database" "sql_db" {
  name           = "sqldb-source-dev"
  server_id      = azurerm_mssql_server.sql_server.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  sku_name       = "Basic" # Costs ~$5/month, perfect for trials
  sample_name    = "AdventureWorksLT" # Crucial: Auto-installs the sample tables

  tags = {
    environment = "dev"
  }
}

# 5. Allow Azure Services (like ADF) to access the SQL Server
resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
