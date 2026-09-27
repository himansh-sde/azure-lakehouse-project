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
