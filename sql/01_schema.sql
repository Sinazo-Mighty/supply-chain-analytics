-- Star schema for the DataCo supply chain project (PostgreSQL / Supabase)
-- Grain of fact_order_item: one row per order line item.

CREATE TABLE dim_customer (
    customer_id       INT PRIMARY KEY,
    customer_segment  TEXT,
    customer_city     TEXT,
    customer_state    TEXT,
    customer_country  TEXT
);

CREATE TABLE dim_product (
    product_card_id   INT PRIMARY KEY,
    product_name      TEXT,
    category_id       INT,
    category_name     TEXT,
    department_id     INT,
    department_name   TEXT,
    product_price     NUMERIC(10,2),
    product_status    INT
);

CREATE TABLE dim_location (
    location_key      INT PRIMARY KEY,
    order_city        TEXT,
    order_state       TEXT,
    order_country     TEXT,
    order_region      TEXT,
    market            TEXT
);

CREATE TABLE dim_date (
    date_key          INT PRIMARY KEY,   -- yyyymmdd
    date              DATE NOT NULL,
    year              INT,
    quarter           INT,
    month             INT,
    month_name        TEXT,
    day_of_week       TEXT,
    is_weekend        BOOLEAN
);

CREATE TABLE fact_order_item (
    order_item_id        INT PRIMARY KEY,
    order_id             INT NOT NULL,
    order_date           TIMESTAMP,
    order_date_key       INT REFERENCES dim_date(date_key),
    shipping_date        TIMESTAMP,
    customer_id          INT REFERENCES dim_customer(customer_id),
    product_card_id      INT REFERENCES dim_product(product_card_id),
    location_key         INT REFERENCES dim_location(location_key),
    shipping_mode        TEXT,
    order_status         TEXT,
    delivery_status      TEXT,
    scheduled_ship_days  INT,
    actual_ship_days     INT,
    is_late              INT,            -- 1 = late delivery (also the ML target)
    quantity             INT,
    unit_price           NUMERIC(10,2),
    discount_amount      NUMERIC(10,2),
    discount_rate        NUMERIC(6,4),
    sales                NUMERIC(12,2),  
    item_total           NUMERIC(12,2),  
    profit               NUMERIC(12,2),
    profit_ratio         NUMERIC(8,4)
);

CREATE INDEX idx_fact_order_id   ON fact_order_item(order_id);
CREATE INDEX idx_fact_customer   ON fact_order_item(customer_id);
CREATE INDEX idx_fact_product    ON fact_order_item(product_card_id);
CREATE INDEX idx_fact_location   ON fact_order_item(location_key);
CREATE INDEX idx_fact_date       ON fact_order_item(order_date_key);
