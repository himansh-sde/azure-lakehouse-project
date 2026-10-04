variable "environment" {
  type    = string
  default = "prod"
}

variable "location" {
  type    = string
  default = "centralindia"
}

# 1. Production Resource Group (scoped to your subscription)
resource "azurerm_resource_group" "lakehouse_rg" {
  name     = "rg-lakehouse-${var.environment}"
  location = var.location
}

# 2. Production ADLS Gen2 Storage Account (must be globally unique, 3-24 lowercase alphanumeric)
resource "azurerm_storage_account" "datalake" {
  name                     = "stalakehouse${var.environment}0987"
  resource_group_name      = azurerm_resource_group.lakehouse_rg.name
  location                 = azurerm_resource_group.lakehouse_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true # Required for ADLS Gen2 Hierarchical Namespace

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# 3. Medallion Containers
resource "azurerm_storage_data_lake_gen2_filesystem" "containers" {
  for_each           = toset(["bronze", "silver", "gold"])
  name               = each.key
  storage_account_id = azurerm_storage_account.datalake.id
}

# 4. Production Data Factory (must be globally unique across Azure)
resource "azurerm_data_factory" "adf" {
  name                = "adf-lakehouse-${var.environment}-0987"
  location            = azurerm_resource_group.lakehouse_rg.location
  resource_group_name = azurerm_resource_group.lakehouse_rg.name

  identity {
    type = "SystemAssigned"
  }
}
