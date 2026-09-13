-- PRT661 Sydn2 Theme 2: Australian House Price Forecasting
-- Schema matching Section 3.3.1 of the Assessment 2 report

CREATE TABLE IF NOT EXISTS raw_sales (
    sale_id           BIGSERIAL PRIMARY KEY,
    district_code     VARCHAR(10),
    property_id       BIGINT,
    sale_counter      BIGINT,
    download_datetime VARCHAR(30),
    house_number      VARCHAR(20),
    street_name       VARCHAR(100),
    suburb            VARCHAR(100),
    postcode          INTEGER,
    area              DOUBLE PRECISION,
    area_type         VARCHAR(5),
    contract_date     VARCHAR(20),
    settlement_date   VARCHAR(20),
    purchase_price    BIGINT,
    zoning            VARCHAR(10),
    nature_of_property VARCHAR(5),
    primary_purpose   VARCHAR(50),
    dealing_number    VARCHAR(20),
    source_file       TEXT,
    source_year_archive INTEGER
);

CREATE TABLE IF NOT EXISTS suburb_dim (
    suburb            VARCHAR(100),
    postcode          INTEGER,
    region            VARCHAR(20),      -- 'sydney' or 'rest_nsw' (postcode-range classification, Section 3.7)
    PRIMARY KEY (suburb, postcode)
);

CREATE TABLE IF NOT EXISTS abs_benchmark (
    quarter                       DATE,
    state                         VARCHAR(5) DEFAULT 'NSW',
    tvd_households_m              DOUBLE PRECISION,
    median_price_house_sydney     DOUBLE PRECISION,
    median_price_house_rest_nsw   DOUBLE PRECISION,
    tvd_households_qoq_pct        DOUBLE PRECISION,
    median_price_house_sydney_qoq_pct    DOUBLE PRECISION,
    median_price_house_rest_nsw_qoq_pct  DOUBLE PRECISION,
    PRIMARY KEY (quarter, state)
);

CREATE TABLE IF NOT EXISTS cleaned_sales (
    dealing_number    VARCHAR(20) PRIMARY KEY,
    district_code     VARCHAR(10),
    property_id       BIGINT,
    suburb            VARCHAR(100),
    postcode          INTEGER,
    contract_date     DATE,
    settlement_date   DATE,
    purchase_price    BIGINT,
    area              DOUBLE PRECISION,
    area_type         VARCHAR(5),
    price_per_sqm     DOUBLE PRECISION,
    zoning            VARCHAR(10),
    is_outlier_flag   BOOLEAN
);

CREATE TABLE IF NOT EXISTS feature_store (
    suburb                  VARCHAR(100),
    postcode                INTEGER,
    region                  VARCHAR(20),
    quarter                 DATE,
    quarter_of_year         INTEGER,
    n_sales                 INTEGER,
    median_price            DOUBLE PRECISION,
    median_price_per_sqm    DOUBLE PRECISION,
    qoq_pct_change          DOUBLE PRECISION,
    lag_1_price             DOUBLE PRECISION,
    lag_2_price             DOUBLE PRECISION,
    lag_3_price             DOUBLE PRECISION,
    lag_4_price             DOUBLE PRECISION,
    lag_1_qoq_pct           DOUBLE PRECISION,
    lag_2_qoq_pct           DOUBLE PRECISION,
    lag_3_qoq_pct           DOUBLE PRECISION,
    lag_4_qoq_pct           DOUBLE PRECISION,
    rolling_mean_4q         DOUBLE PRECISION,
    rolling_std_4q          DOUBLE PRECISION,
    state_benchmark_growth  DOUBLE PRECISION,
    nsw_tvd_qoq_pct         DOUBLE PRECISION,
    missing_benchmark_flag  INTEGER,
    is_q1 INTEGER, is_q2 INTEGER, is_q3 INTEGER, is_q4 INTEGER,
    flag_covid_period       INTEGER,
    flag_rate_hike_period   INTEGER,
    n_outliers_excluded_candidate INTEGER,
    PRIMARY KEY (suburb, postcode, quarter)
);

CREATE INDEX IF NOT EXISTS idx_cleaned_sales_suburb ON cleaned_sales(suburb);
CREATE INDEX IF NOT EXISTS idx_cleaned_sales_settlement_date ON cleaned_sales(settlement_date);
CREATE INDEX IF NOT EXISTS idx_feature_store_suburb ON feature_store(suburb);
CREATE INDEX IF NOT EXISTS idx_feature_store_quarter ON feature_store(quarter);
