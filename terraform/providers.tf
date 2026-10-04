terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "sttfstateprod0987" # Use the exact name you used in Step 1
    container_name       = "tfstate"
    key                  = "lakehouse.prod.tfstate"
  }
}

provider "azurerm" {
  features {}
}
