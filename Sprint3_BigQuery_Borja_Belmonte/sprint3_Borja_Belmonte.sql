-- NIVELL 1
-- Ejercicio 1
--Dataset Físic sprint3_silver → Capa Lògica Silver (Dades Netes)
-- Funció: Dades netes, tipades i deduplicades.
-- Mètode: Utilitza codi SQL (CREATE SCHEMA). 

CREATE SCHEMA `sprint3-analytics-borja-b.sprint3_silver` 
OPTIONS(
    location = 'EU'
);
-- Dataset Físic sprint3_gold → Capa Lògica Gold (Dades de Negoci)
-- Funció: Dades agregades llestes per a informes i panells de control (dashboards).
-- Mètode: Utilitza Cloud Shell (Línia d'ordres bq).

bq --location=’EU’ mk -d sprint3-analytics-borja-b:sprint3_golden

-- Ejercicio 2
-- Escriu i executa les sentències CREATE EXTERNAL TABLE per connectar els següents fitxers al dataset sprint3_bronze. Para molta atenció a les "Notes Tècniques", ja que no tots els arxius tenen el mateix format.

-- Miro de qué campos se compone la tabla
CREATE OR REPLACE EXTERNAL TABLE `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw`
OPTIONS(
  format='CSV',
  uris = ['gs://bootcamp-data-analytics-public/ERP/transactions.csv'],
  field_delimiter = ';'
  );

CREATE OR REPLACE EXTERNAL TABLE `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw`(
  id STRING,
  card_id STRING,
  business_id STRING,
  timestamp STRING,
  amount STRING,
  declined STRING,
  product_ids STRING,
  user_id STRING,
  lat STRING,
  longitude STRING
)  
OPTIONS(
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/ERP/transactions.csv'],
  field_delimiter = ';',
  skip_leading_rows = 1
);

-- Ejercicio 4
-- A)
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw_native`
AS
SELECT * FROM `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw`;

-- B)
SELECT id FROM `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw`;
SELECT id FROM `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw_native`;

--C)
SELECT * FROM `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw_native`;
SELECT * FROM `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw_native` LIMIT 10;

-- Ejercicio 5
SELECT SUBSTR(timestamp, 1, 10) AS date,
       ROUND(SUM(CAST(amount AS FLOAT64)), 2) AS total_amount
FROM `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw`
WHERE SUBSTR(timestamp,1,4) = '2021'
AND declined = '0'
GROUP BY date
ORDER BY total_amount DESC
LIMIT 5;

-- Ejercicio 6

SELECT c.company_name,c.country,FORMAT_DATE('%d-%m-%Y',PARSE_DATE('%Y-%m-%d',SUBSTR(t.timestamp,1,10))) AS fecha_inversa,
FROM  `sprint3-analytics-borja-b.sprint3_bronze.transactions_raw_native` AS t
INNER JOIN `sprint3-analytics-borja-b.sprint3_bronze.companies_raw` AS c
ON t.business_id=c.company_id
WHERE t.declined = '0'
AND CAST(t.amount AS FLOAT64) BETWEEN 100 AND 200
AND FORMAT_DATE('%d-%m-%Y',PARSE_DATE('%Y-%m-%d',SUBSTR(t.timestamp,1,10)))IN ('29-04-2015','20-07-2018','13-03-2024')
ORDER BY fecha_inversa;

-- NIVELL 2
-- Ejercicio 1

CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_silver.products_clean` AS
SELECT
id AS product_id,
product_name AS name,
price,
colour,
weight,
SAFE_CAST(SUBSTR(warehouse_id,4) AS INT64) AS warehouse_id,
category,
brand,
cost,
launch_date
FROM 
`sprint3-analytics-borja-b.sprint3_bronze.products_raw`;
 

-- Ejercicio 2
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_silver.transactions_clean` AS
SELECT
id AS transaction_id,
card_id,
business_id,
SAFE_CAST(timestamp AS TIMESTAMP) AS timestamp,
IFNULL(SAFE_CAST(amount AS FLOAT64),0) AS amount,
declined,
ARRAY(SELECT SAFE_CAST(product_id AS INT64) FROM UNNEST(SPLIT(product_ids,', ')) AS product_id) AS product_ids,
user_id,
SAFE_CAST(lat AS FLOAT64) AS lat,
SAFE_CAST(longitude AS FLOAT64) AS longitude
FROM 
`sprint3-analytics-borja-b.sprint3_bronze.transactions_raw`;

-- Ejercicio 3
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_silver.users_combined` AS
SELECT
id_us AS user_id,
name,
surname,
phone,
email,
birth_date,
country,
city,
postal_code,
address,
'America' AS origin
FROM
`sprint3-analytics-borja-b.sprint3_bronze.american_users_raw`
UNION ALL
SELECT
id_eu AS user_id,
name,
surname,
phone,
email,
birth_date,
country,
city,
postal_code,
address,
'Europe' AS origin
FROM
`sprint3-analytics-borja-b.sprint3_bronze.european_users_raw`;

-- Ejercicio 4
CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_silver.companies_clean` AS
SELECT 
company_id,
company_name,
phone,
email,
country,
website
FROM
`sprint3-analytics-borja-b.sprint3_bronze.companies_raw`;

CREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_silver.credit_cards_clean` AS
SELECT
cc_id AS card_id,
user_id,
iban,
pan,
pin,
cvv,
track1,
track2,
expiring_date
FROM
`sprint3-analytics-borja-b.sprint3_bronze.credit_cards_raw`;

-- Nivell 3
-- Ejercicio 1
CREATE OR REPLACE VIEW `sprint3-analytics-borja-b.sprint3_golden.v_marketing_kpis` AS
SELECT
c.company_name,
c.phone,
c.country,
ROUND(AVG(t.amount),2) AS mitja_compra,
CASE
WHEN AVG(t.amount) > 260 THEN 'Premium'
ELSE 'Standard'
END AS client_tier
FROM
`sprint3-analytics-borja-b.sprint3_silver.companies_clean` AS c
INNER JOIN
`sprint3-analytics-borja-b.sprint3_silver.transactions_clean` AS t
ON c.company_id=t.business_id
WHERE t.declined = '0'
GROUP BY
c.company_name,
c.phone,
c.country;

SELECT * FROM `sprint3-analytics-borja-b.sprint3_golden.v_marketing_kpis` 
ORDER BY client_tier ASC, mitja_compra DESC;

-- Ejercicio 2
CCREATE OR REPLACE TABLE `sprint3-analytics-borja-b.sprint3_golden.product_sales_ranking` AS
SELECT
p.product_id,
p.name,
p.price,
p.colour,
COUNT(t.id_aplanado) AS total_sold
FROM `sprint3-analytics-borja-b.sprint3_silver.products_clean` AS p
LEFT JOIN(
  SELECT 
id_aplanado
FROM `sprint3-analytics-borja-b.sprint3_silver.transactions_clean`,
UNNEST(product_ids) AS id_aplanado
) AS t
ON p.product_id=t.id_aplanado
GROUP BY
p.product_id,
p.name,
p.price,
p.colour
ORDER BY 
total_sold DESC;