CREATE DATABASE bill_db;

USE bill_db;

CREATE TABLE Bills (
    BillNo VARCHAR(20) PRIMARY KEY,
    BillDate DATE,
    BillTime TIME
);

CREATE TABLE BillItems (
    ItemID INT AUTO_INCREMENT PRIMARY KEY,
    BillNo VARCHAR(20),
    ItemName VARCHAR(100),
    MRP DECIMAL(10,2),
    Quantity DECIMAL(10,2),
    Price DECIMAL(10,2),
    Amount DECIMAL(10,2),
    FOREIGN KEY (BillNo) REFERENCES Bills(BillNo)
);

SELECT * FROM Bills;
SELECT * FROM BillItems;

-- DROP table BillItems;
-- DROP Table Bills;

-- delete from BillItems;
-- delete from Bills;

-- SET SQL_SAFE_UPDATES = 0;

-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE BillItems;
-- SET FOREIGN_KEY_CHECKS = 1;

-- TRUNCATE TABLE Bills;
-- TRUNCATE TABLE BillItems;
