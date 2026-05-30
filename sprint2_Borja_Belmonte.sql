-- Exercici 2
-- Llistat de països que estan realitzant vendes

SELECT  c.country FROM company c
INNER JOIN transaction t
ON c.id=t.company_id
WHERE t.declined = 0
ORDER BY c.country;

-- Des de quants països es generen les vendes

SELECT COUNT(DISTINCT c.country) FROM company c
INNER JOIN transaction t
ON c.id=t.company_id
WHERE t.declined = 0;

-- Identifica la companyia amb la mitjana més gran de vendes.

SELECT c.company_name, ROUND(AVG(t.amount),2) AS mitja_superior_vendes FROM company c
INNER JOIN transaction t
ON c.id=t.company_id
WHERE t.declined = 0
GROUP BY c.company_name
ORDER BY mitja_superior_vendes DESC
LIMIT 1;

-- Exercici 3
-- Mostra totes les transaccions realitzades per empreses d'Alemanya

SELECT * FROM transactions.transaction 
WHERE company_id IN (
					SELECT id 
                    FROM transactions.company 
                    WHERE country='Germany');
SELECT * 
FROM transaction 
WHERE EXISTS (
				SELECT id 
                FROM company 
                WHERE country='Germany'
                ) AND declined=0;                    

-- Llista les empreses que han realitzat transaccions per un amount superior a la mitjana de totes les transaccions.

SELECT company_name FROM transactions.company
WHERE id IN (
			SELECT company_id 
            FROM transactions.transaction 
            WHERE amount > (
				SELECT AVG(amount) 
                FROM transactions.transaction));

-- Eliminaran del sistema les empreses que no tenen transaccions registrades, entrega el llistat d'aquestes empreses.

SELECT * FROM company c     
WHERE NOT EXISTS (
				SELECT company_id 
                FROM transaction t
                WHERE c.id=t.company_id
                );

-- Exercici 4
CREATE TABLE IF NOT EXISTS credit_card(
id VARCHAR(15) PRIMARY KEY,
iban VARCHAR(255),
pan VARCHAR(255),
pin VARCHAR(10),
cvv VARCHAR(4),
expiring_date VARCHAR(10)
);

ALTER TABLE transaction
ADD CONSTRAINT fk_card_transaction
FOREIGN KEY (credit_card_id) REFERENCES credit_card(id)
ON UPDATE CASCADE;

-- Exercici 5
UPDATE credit_card
SET iban = 'TR323456312213576817699999'
WHERE id = 'CcU-2938';

SELECT * FROM credit_card WHERE id = 'CcU-2938';

-- Exercici 6
-- En la taula "transaction" ingressa una nova transacció amb la següent informació:
INSERT INTO company (id) VALUES ('b-9999');
INSERT INTO credit_card (id) VALUES ('CcU-9999');
INSERT INTO transaction (id, credit_card_id, company_id, user_id, lat, longitude, amount, declined)
VALUES ('108B1D1D-5B23-A76C-55EF-C568E49A99DD','CcU-9999','b-9999','9999','829.999','-117.999','111.11','0');
SELECT * FROM transaction WHERE credit_card_id = 'CcU-9999';

-- Exercici 7
ALTER TABLE credit_card
DROP COLUMN pan;
SELECT * FROM credit_card;

--Exercici 8
CREATE TABLE IF NOT EXISTS transaction(
id VARCHAR(100) PRIMARY KEY,
card_id VARCHAR(50),
business_id VARCHAR(15),
timestamp timestamp,
amount DECIMAL(10,2),
declined BOOLEAN NOT NULL DEFAULT 0,
product_ids VARCHAR(255) NOT NULL,
user_id INT NOT NULL,
lat FLOAT DEFAULT NULL,
longitude FLOAT DEFAULT NULL,
discount_amount DECIMAL(10,2),
tax_amount DECIMAL(10,2),
shipping_amount DECIMAL(10,2),
channel VARCHAR(50),
campaign_id VARCHAR(50),
device_type VARCHAR(20),
is_international BOOLEAN NOT NULL DEFAULT 0,
decline_reason VARCHAR(150),
distance_km DECIMAL(10,2)
);	

CREATE TABLE IF NOT EXISTS users(
id INT PRIMARY KEY,
name VARCHAR(100) NOT NULL,
surname VARCHAR(100) NOT NULL,
phone VARCHAR(50),
email VARCHAR(100) NOT NULL,
birth_date VARCHAR(50),
country VARCHAR (50) NOT NULL,
city VARCHAR (50) NOT NULL,
postal_code VARCHAR (20) NOT NULL,
address VARCHAR (150) NOT NULL,
signup_date VARCHAR(50) NOT NULL,
user_segment VARCHAR (50) NOT NULL,
income_band VARCHAR (20)
);

ALTER TABLE users
ADD continent VARCHAR(50);
UPDATE users
SET continent = CASE
	WHEN country IN ('United States', 'Canada') THEN 'America'
    ELSE 'Europe'
END;    


CREATE TABLE IF NOT EXISTS companies(
company_id VARCHAR(15) PRIMARY KEY,
company_name VARCHAR (255) NOT NULL,
phone VARCHAR (20),
email VARCHAR (100) NOT NULL,
country VARCHAR (50) NOT NULL,
website VARCHAR (100) NOT NULL,
merchant_category VARCHAR (50) NOT NULL,
merchant_price_position VARCHAR (50) NOT NULL
);

DROP TABLE credit_cards;
CREATE TABLE IF NOT EXISTS credit_cards(
id VARCHAR(50) PRIMARY KEY,
user_id INT NOT NULL,
iban VARCHAR(100) NOT NULL,
pan VARCHAR(20) NOT NULL,
pin VARCHAR(6) NOT NULL,
cvv VARCHAR(4) NOT NULL,
track1 VARCHAR(100),
track2 VARCHAR(100),
expiring_date DATE,
card_type VARCHAR(30) NOT NULL,
card_renewal_flag BOOLEAN NOT NULL DEFAULT 0
);

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/N1-Ex.8__credit_cards.csv'
INTO TABLE credit_cards
FIELDS TERMINATED BY ','
IGNORE 1 LINES
(id, user_id, iban, pan, pin, cvv, track1, track2, @var_fecha, card_type, card_renewal_flag)
SET expiring_date = STR_TO_DATE (@var_fecha, '%m/%d/%y');

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/N1-Ex.8__companies.csv'
INTO TABLE companies
FIELDS TERMINATED BY ','
IGNORE 1 LINES;

TRUNCATE TABLE users;
LOAD DATA
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/N1-Ex.8__american_users.csv'
INTO TABLE users
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/N1-Ex.8__european_users.csv'
INTO TABLE users
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/N1-Ex.8__transactions.csv'
INTO TABLE transaction
FIELDS TERMINATED BY ';'
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

ALTER TABLE transaction
ADD CONSTRAINT fk_transaction_users
FOREIGN KEY (user_id) REFERENCES users(id)
ON UPDATE CASCADE;

ALTER TABLE transaction
ADD CONSTRAINT fk_transaction_companies
FOREIGN KEY (business_id) REFERENCES companies(company_id)
ON UPDATE CASCADE;

ALTER TABLE transaction
ADD CONSTRAINT fk_transaction_card
FOREIGN KEY (card_id) REFERENCES credit_cards(id)
ON UPDATE CASCADE;


-- Exercici 9
SELECT * 
FROM users 
WHERE EXISTS(
			SELECT COUNT(id) AS total_transacciones 
            FROM transaction 
            WHERE transaction.user_id = users.id 
            GROUP BY user_id 
            HAVING COUNT(id) > 80); 

-- Exercici 10
SELECT cc.iban, ROUND(AVG(t.amount),2) AS media_gasto
FROM credit_cards cc
INNER JOIN transaction t
ON cc.id=t.card_id
INNER JOIN companies c
ON t.business_id=c.company_id
WHERE c.company_name='Donec Ltd'
GROUP BY cc.iban;   

-- NIVELL 2
-- Exercici 1
SELECT DATE(transaction.timestamp) AS fechas_ventas, SUM(transaction.amount) AS total_ventas
FROM transaction
GROUP BY DATE(transaction.timestamp)
ORDER BY total_ventas DESC
LIMIT 5;              

--Exercici 2
SELECT companies.company_name, companies.phone, companies.country, DATE(transaction.timestamp) AS fecha_transaccion, transaction.amount
FROM companies
INNER JOIN transaction
ON companies.company_id=transaction.business_id
WHERE transaction.amount BETWEEN 350 AND 400
AND DATE(transaction.timestamp) IN ('2015-04-29','2018-07-20','2024-03-13') 
ORDER BY transaction.amount DESC;

--Exercici 3
 SELECT c.company_name,COUNT(t.id) AS total_transacciones,
	CASE
		WHEN COUNT(t.id) >= 400 THEN '400 o més transaccions'
		ELSE 'Menys de 400 transaccions'
	END AS capacidad_operativa
FROM companies c
INNER JOIN transaction t
ON c.company_id=t.business_id
GROUP BY c.company_name
ORDER BY total_transacciones;

--Exercici 4
DELETE FROM transaction
WHERE id='000447FE-B650-4DCF-85DE-C7ED0EE1CAAD';
SELECT * FROM transaction WHERE id='000447FE-B650-4DCF-85DE-C7ED0EE1CAAD';

-- Exercici 5

CREATE VIEW VistaMarketing AS 
SELECT c.company_name, c.phone, c.country, ROUND(AVG(t.amount),2) AS mitjana_vendes
FROM companies c
INNER JOIN transaction t
ON c.company_id=t.business_id
WHERE t.declined=0
GROUP BY c.company_name, c.phone, c.country
ORDER BY mitjana_vendes DESC;

-- Nivell 3
-- Exercici 1
CREATE TABLE estat_targetes AS
WITH estat_targeta AS(
SELECT id, card_id, declined,
	ROW_NUMBER() OVER(PARTITION BY card_id ORDER BY id DESC)  AS orden_transaccion
FROM transaction
),
resum_estat AS(
SELECT card_id,
		CASE
			WHEN SUM(CASE WHEN declined = 0 THEN 1 ELSE 0 END) > 0 THEN 'Activa'
            ELSE 'Inactiva'
        END AS tarjetas_activas
FROM estat_targeta
WHERE orden_transaccion <=3        
GROUP BY card_id
)
SELECT COUNT(*) AS total_tarjetas_activas
FROM resum_estat
WHERE tarjetas_activas = 'Activa';
SELECT * FROM estat_targetes;

-- Exercici 2
CREATE TABLE IF NOT EXISTS products(
id INT PRIMARY KEY,
product_name VARCHAR(150),
price VARCHAR(20),
colour VARCHAR(30),
weight DECIMAL(5,2),
warehouse_id VARCHAR(10),
category VARCHAR(50),
brand VARCHAR(50),
cost VARCHAR(20),
launch_date DATE
);        

LOAD DATA
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/N1-Ex.8__products.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

SELECT p.id, p.product_name, COUNT(*) AS veces_vendido
FROM transaction t
INNER JOIN products p
ON FIND_IN_SET(p.id, REPLACE(t.product_ids, ' ','')) >0
GROUP BY p.id, p.product_name
ORDER BY p.id;






