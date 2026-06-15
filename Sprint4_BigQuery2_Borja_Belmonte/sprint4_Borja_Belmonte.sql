-- Nivell 1
-- Ejercicio 1
SELECT c.company_name,t.* FROM 
`sprint3-analytics-borja-b.sprint3_silver.companies_clean` c
INNER JOIN `sprint3-analytics-borja-b.sprint3_silver.transactions_clean` t
ON c.company_id=t.business_id
WHERE c.country = 'Germany'
AND t.timestamp = '2022-03-12';

--Ejercicio 2
--Pas1
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_silver.transactions_recent` AS
SELECT 
* EXCEPT(timestamp),
TIMESTAMP_SUB(
  CURRENT_TIMESTAMP(),
  INTERVAL CAST(RAND() * 50 AS INT64) DAY
) AS timestamp
FROM `sprint3-analytics-borja-b.sprint3_silver.transactions_clean`;
--Pas 2
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_golden.fact_transactions_optimized` 
PARTITION BY
DATE(timestamp)
CLUSTER BY
business_id 
AS 
SELECT *
FROM 
`sprint3-analytics-borja-b.sprint3_silver.transactions_recent`;

--Ejercicio 3
--pas1
SELECT * FROM `sprint3-analytics-borja-b.sprint3_silver.transactions_recent`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
--pas2
SELECT * FROM `sprint3-analytics-borja-b.sprint3_golden.fact_transactions_optimized`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

--Ejercicio 4
CREATE OR REPLACE MATERIALIZED VIEW `sprint3-analytics-borja-b.sprint3_golden.mv_daily_sales` AS
SELECT 
SUM(amount) AS total_vendes,
DATE(timestamp) AS fecha
FROM `sprint3-analytics-borja-b.sprint3_golden.fact_transactions_optimized`
GROUP BY fecha;

SELECT 
ROUND(total_vendes,2) AS total_vendes,
fecha 
FROM `sprint3-analytics-borja-b.sprint3_golden.mv_daily_sales` 
ORDER BY fecha DESC;

-- Nivel 2
--Ejercicio 1
WITH VIP_Stats AS(
  SELECT
  ROUND(SUM(t.amount),2) AS total_gastat,
  COUNT(t.transaction_id) AS num_compres,
  ROUND(AVG(t.amount),2) AS tiquet_mitja,
  MAX(t.amount) AS compra_maxima,
  u.user_id,
  u.name,
  u.surname,
  u.email
FROM `sprint3-analytics-borja-b.sprint3_silver.transactions_recent` AS t
INNER JOIN `sprint3-analytics-borja-b.sprint3_silver.users_combined` AS u 
ON t.user_id = u.user_id
WHERE t.declined = '0'
GROUP BY 
  u.user_id,
  u.name,
  u.surname,
  u.email
HAVING total_gastat > 500
)
SELECT
user_id,
CONCAT(name,' ',surname) AS nom_complet,
email,
total_gastat,
num_compres,
tiquet_mitja,
compra_maxima
FROM VIP_Stats
ORDER BY total_gastat DESC;

--Ejercicio 2
WITH Sales_History AS(
  SELECT
  fecha AS data,
  total_vendes AS Vendes_Avui,
  LAG(total_vendes) OVER (ORDER BY fecha ASC) AS Vendes_Ahir
  FROM `sprint3-analytics-borja-b.sprint3_golden.mv_daily_sales`
)
SELECT 
data AS Data,
ROUND(Vendes_Avui,2) AS Vendes_Avui,
ROUND(Vendes_Ahir,2) AS Vendes_Ahir,
ROUND(SAFE_DIVIDE(Vendes_Avui - Vendes_Ahir, Vendes_Ahir) * 100, 2) AS Diff_Percentual
FROM Sales_History
ORDER BY Data ASC;

--Ejercicio 3
WITH History_Sales AS(
  SELECT
  fecha AS Data,
  ROUND(total_vendes,2) AS Vendes_del_Dia
  FROM `sprint3-analytics-borja-b.sprint3_golden.mv_daily_sales`
)
SELECT
Data,
Vendes_del_Dia,
ROUND(
  SUM(Vendes_del_Dia) OVER(
  PARTITION BY EXTRACT (year FROM Data) ORDER BY Data ASC
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
),2
) AS Vendes_Acumulades_YTD
FROM History_Sales
ORDER BY Data ASC;

-- Ejercicio4
WITH Client_VIP AS(
  SELECT
  u.user_id,
  CONCAT(u.name,' ',u.surname) AS nom_complet,
  u.email,
  t.amount AS import_3a_compra,
  AVG(t.amount) OVER(PARTITION BY u.user_id ORDER BY t.timestamp ASC) AS compra_media,
  t.timestamp AS data_3a_compra,
  ROW_NUMBER() OVER(PARTITION BY u.user_id ORDER BY t.timestamp ASC) AS num_compra
  FROM `sprint3-analytics-borja-b.sprint3_silver.users_combined` AS u
  INNER JOIN `sprint3-analytics-borja-b.sprint3_silver.transactions_recent` AS t
  ON u.user_id = t.user_id
  WHERE t.declined = '0'
   
)
SELECT
user_id,
nom_complet,
email,
ROUND(compra_media,2) AS compra_media,
import_3a_compra,
data_3a_compra,
FROM Client_VIP
QUALIFY ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY data_3a_compra ASC) = 3

-- NIVEL3
-- Ejercicio 1
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_golden.dim_transactions_flat` AS(
SELECT
t.transaction_id,
t.timestamp,
t.amount AS total_ticket,
product_id_aplanado AS product_sku,
p.name AS product_name,
p.price AS product_price,
p.category
FROM `sprint3-analytics-borja-b.sprint3_silver.transactions_recent` AS t
CROSS JOIN UNNEST(t.product_ids) AS product_id_aplanado
INNER JOIN `sprint3-analytics-borja-b.sprint3_silver.products_clean` AS p
ON product_id_aplanado = p.product_id
);

-- Ejercicio 2
SELECT product_name,COUNT(product_sku) AS total_vendido
FROM `sprint3-analytics-borja-b.sprint3_golden.dim_transactions_flat`
GROUP BY product_name
ORDER BY total_vendido DESC
LIMIT 5;

--Ejercicio 3
CREATE OR REPLACE FUNCTION `sprint3-analytics-borja-b.sprint3_golden.calculate_tax` (amount FLOAT64)
RETURNS FLOAT64
AS(
  amount * 1.21
);

CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_golden.dim_transactions_flat` AS(
SELECT
t.transaction_id,
t.timestamp,
t.amount AS total_ticket,
product_id_aplanado AS product_sku,
p.name AS product_name,
p.price AS product_price,
`sprint3-analytics-borja-b.sprint3_golden.calculate_tax`(p.price) AS producto_price_tax_inc,
p.category
FROM `sprint3-analytics-borja-b.sprint3_silver.transactions_recent` AS t
CROSS JOIN UNNEST(t.product_ids) AS product_id_aplanado
INNER JOIN `sprint3-analytics-borja-b.sprint3_silver.products_clean` AS p
ON product_id_aplanado = p.product_id
WHERE t.declined = '0'
);

--Link al documento
https://datastudio.google.com/reporting/26fa06f3-b3d3-4ee6-88c1-f6a7b654f2b1