-- synapse/serverless_views.sql

-- 1. Create a logical database for your BI semantic layer
CREATE DATABASE LakehouseAnalytics;
GO

USE LakehouseAnalytics;
GO

-- 2. Create a View over the Gold Delta Table using OPENROWSET
CREATE OR ALTER VIEW vw_customer_summary
AS
SELECT *
FROM OPENROWSET(
    BULK 'abfss://gold@stalakehousedev.dfs.core.windows.net/analytics/customer_summary/',
    FORMAT = 'DELTA'
) AS [result];
GO

-- 3. Test the View (This is what Power BI will run)
SELECT TOP 100 * FROM vw_customer_summary;
