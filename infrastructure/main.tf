terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Fetch the current Azure client configuration (Tenant ID, Subscription ID)
data "azurerm_client_config" "current" {}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "rg-lakehouse-dev"
  location = "Central India"
}

# 2. Azure Data Lake Storage Gen2 (Hierarchical Namespace enabled)
resource "azurerm_storage_account" "adls" {
  name                     = "stalakehousedev" # Must be globally unique, change if taken
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # Keeps cost low for dev/trial
  is_hns_enabled           = true  # Critical: Enables Data Lake Gen2 functionality

  tags = {
    environment = "dev"
    project     = "medallion-lakehouse"
  }
}

# 2a. ADLS Containers (Bronze, Silver, Gold)
resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.adls.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.adls.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.adls.id
}

# 3. Azure Key Vault
resource "azurerm_key_vault" "kv" {
  name                        = "kv-lakehouse-dev27" # Must be globally unique
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  enable_rbac_authorization   = true # Modern secure access model
}

# 4. Azure Databricks Workspace
resource "azurerm_databricks_workspace" "dbw" {
  name                        = "dbw-lakehouse-dev27"
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = azurerm_resource_group.rg.location
  sku                         = "premium" # Required to access the 14-day free DBU trial
  
  tags = {
    environment = "dev"
  }
}

# 5. Azure Data Factory
resource "azurerm_data_factory" "adf" {
  name                = "adf-lakehouse-dev27" # Must be globally unique
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}
