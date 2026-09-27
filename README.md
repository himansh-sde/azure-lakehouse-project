# Azure Medallion Lakehouse

# Enterprise Azure Data Lakehouse Platform (Medallion Architecture)

[![Terraform](https://img.shields.io/badge/IaC-Terraform-623CE4?logo=terraform&logoColor=white)](#infrastructure-as-code)
[![Azure Data Factory](https://img.shields.io/badge/Orchestration-Azure%20Data%20Factory-0078D4?logo=microsoftazure&logoColor=white)](#data-pipeline-architecture)
[![Azure Databricks](https://img.shields.io/badge/Compute-Azure%20Databricks-FF3621?logo=databricks&logoColor=white)](#processing-engine)
[![Delta Lake](https://img.shields.io/badge/Storage%20Format-Delta%20Lake-00ADD8?logo=delta&logoColor=white)](#delta-lake-implementation)
[![Azure Synapse](https://img.shields.io/badge/Serving-Synapse%20Serverless%20SQL-0089D6?logo=microsoftazure&logoColor=white)](#serving-layer)

An end-to-end modern data engineering platform deployed on Microsoft Azure using the Medallion Architecture pattern (Bronze → Silver → Gold). 

This platform orchestrates dynamic, metadata-driven data ingestion, implements Change Data Capture (CDC) via Delta Lake `MERGE` operations, enforces enterprise identity governance via Microsoft Entra ID and Azure Key Vault, and serves analytical models through Azure Synapse Serverless SQL without persistent compute costs.

---

## Architecture

```text
[ Data Sources ]
  │ (APIs, RDBMS, Flat Files)
  ▼
[ Azure Data Factory ] ── (Dynamic Parameterized Pipelines via Metadata JSON)
  │
  ▼
[ ADLS Gen2: Bronze Zone ] (Raw Ingestion / Append-Only Parquet)
  │
  ▼
[ Azure Databricks (PySpark) ] ── (Schema Validation, Deduplication, CDC / UPSERTs)
  │
  ▼
[ ADLS Gen2: Silver Zone ] (Cleaned, Conformed Delta Tables)
  │
  ▼
[ Azure Databricks (PySpark) ] ── (Business Aggregates, Z-ORDER Clustering, OPTIMIZE)
  │
  ▼
[ ADLS Gen2: Gold Zone ] (Curated Analytics-Ready Delta Tables)
  │
  ├──► [ Azure Synapse Serverless SQL ] (Logical Views over Delta / Zero Idle Cost)
  │           │
  │           ▼
  └────► [ Power BI Dashboard ] (Direct Lake / Import BI Models)
```

---

## Key Platform Features

* **Metadata-Driven Ingestion:** Eliminates hardcoded ETL pipelines by using ADF `Lookup` and `ForEach` activities governed by JSON manifests, allowing automated onboarding of new datasets.
* **ACID Lakehouse Transactions:** Uses Delta Lake on ADLS Gen2 to support concurrent reads/writes, time-travel audits, and atomic rollbacks.
* **Change Data Capture (CDC):** Handles incremental data loads and late-arriving dimensions using PySpark `MERGE INTO` (SCD Type 1 / UPSERT logic).
* **Storage & Compute Performance Tuning:** Implements file compaction via Delta `OPTIMIZE` and spatial data co-locality via `Z-ORDER` indexing to reduce query scan times by up to 70%.
* **Zero Idle Serving Compute:** Decouples storage from compute by creating Synapse Serverless SQL views directly over Delta files, bypassing the expensive uptime requirements of Synapse Dedicated Pools.
* **Enterprise Identity & Secrets:** Replaces raw storage access keys with Microsoft Entra ID Service Principals (`Storage Blob Data Contributor`) and Databricks Key Vault Secret Scopes.
* **Automated Infrastructure:** Full cloud footprint provisioned reproducibly using Terraform with remote state separation.

---

## Repository Structure

```text
azure-lakehouse-project/
├── .github/
│   └── workflows/              # GitHub Actions CI/CD pipelines
├── adf/                        # Azure Data Factory pipeline definitions & ARM templates
├── config/
│   └── ingestion_list.json     # Metadata configuration driving ADF ingestion
├── databricks/
│   ├── 01_bronze/              # Raw data extraction and staging PySpark notebooks
│   ├── 02_silver/              # Schema validation, cleansing, and CDC merge logic
│   └── 03_gold/                # Star schema dimension/fact modeling and aggregations
├── infrastructure/             # Terraform infrastructure definitions
│   ├── main.tf                 # Core Azure resources (ADLS, Databricks, ADF, Key Vault)
│   └── .gitignore              # Ignores local state files and provider binaries
├── synapse/
│   └── serverless_views.sql    # DDL scripts for logical views over Gold Delta tables
├── .gitignore
└── README.md
```

---

## Data Pipeline Flow

| Stage | Storage Zone | Engine | Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | `adls/bronze` | ADF Copy Activity | Parquet / JSON | Dynamic, metadata-parameterized pipeline landing raw data without schema modification. |
| **Cleansing** | `adls/silver` | Databricks (PySpark) | Delta Lake | Explicit schema casting, NULL handling, deduplication, and transactional UPSERTs (`MERGE`). |
| **Curated** | `adls/gold` | Databricks (PySpark) | Delta Lake | Aggregated business metrics, star schema modeling, file compaction (`OPTIMIZE`), and `Z-ORDER` indexing. |
| **Serving** | Analytical Layer | Synapse Serverless SQL | SQL Views | On-demand relational views reading directly from Gold Delta storage files. |

---

## Infrastructure as Code (Terraform)

The cloud infrastructure is defined declaratively using Terraform:

* **Resource Group:** Regional container for lifecycle isolation.
* **ADLS Gen2:** Storage Account configured with `is_hns_enabled = true` and `LRS` redundancy to optimize cost.
* **Containers:** Automated provisioning of `bronze`, `silver`, and `gold` file systems.
* **Azure Key Vault:** RBAC-enabled secrets engine protecting tenant credentials and service principal secrets.
* **Databricks Workspace:** Provisioned under the Premium tier to enable credential passthrough and native Secret Scope integrations.
* **Azure Data Factory:** V2 deployment wired for continuous deployment and Git integration.

---

## Getting Started

### Prerequisites
* [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated (`az login`)
* [Terraform CLI](https://developer.hashicorp.com/terraform/install) (v1.5+)
* Python 3.10+ & PySpark

### 1. Infrastructure Deployment
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### 2. Service Principal & Secrets Setup
Assign the Service Principal role to the Data Lake:
```bash
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <SERVICE_PRINCIPAL_CLIENT_ID> \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-lakehouse-dev/providers/Microsoft.Storage/storageAccounts/stalakehousedev"
```

Save secrets in Azure Key Vault:
```bash
az keyvault secret set --vault-name kv-lakehouse-dev --name "sp-client-id" --value "<CLIENT_ID>"
az keyvault secret set --vault-name kv-lakehouse-dev --name "sp-client-secret" --value "<CLIENT_SECRET>"
az keyvault secret set --vault-name kv-lakehouse-dev --name "sp-tenant-id" --value "<TENANT_ID>"
```

### 3. Pipeline Execution
1. Link Azure Data Factory to this repository under the `adf/` directory.
2. Trigger the master pipeline `pipeline_master_orchestrator` to ingest Bronze sources.
3. Databricks Workflows execute the Silver cleansing jobs and Gold aggregations.
4. Run `synapse/serverless_views.sql` to expose views to downstream BI platforms.
