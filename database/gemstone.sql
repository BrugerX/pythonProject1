DROP TABLE CASCADE IF EXISTS bid_data;
DROP TABLE IF EXISTS colored_gemstone_specs;
DROP TABLE IF EXISTS shipping_data;
DROP TABLE IF EXISTS image_data;
DROP TABLE IF EXISTS auction_data;
DROP TABLE IF EXISTS meta_data;

CREATE TABLE meta_data (
  LID VARCHAR PRIMARY KEY,
  lot_url_used VARCHAR NOT NULL,
  errors_processing VARCHAR[] NOT NULL,
  scraping_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  is_closed BOOLEAN not null
);

create TABLE auction_data
(
    LID VARCHAR PRIMARY KEY,
    experts_estimate_min NUMERIC NOT NULL,
    experts_estimate_max NUMERIC NOT NULL,
    bidding_start_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    bidding_close_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    scraping_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    is_reserve_price_met BOOLEAN,
    is_closed_at_scraping boolean NOT NULL,
    favourite_count int,
    AID VARCHAR, /* Auction ID */
    is_buy_now_available BOOLEAN NOT NULL,
    FOREIGN KEY (LID) REFERENCES meta_data (LID) ON DELETE CASCADE
);

create TABLE bid_data
    (
        LID VARCHAR,
        currencies VARCHAR[] NOT NULL,
        bid_amount NUMERIC[] NOT NULL,
        BID VARCHAR PRIMARY KEY NOT NULL,
        is_latest_bid boolean NOT NULL,
        is_final_bid boolean NOT NULL ,
        is_closed_at_scraping boolean NOT NULL,
        is_reserve_price_met boolean NOT NULL,
        is_buy_now_available boolean NOT NULL,
        is_from_order boolean NOT NULL,
        favourite_count int NOT NULL,
        AID VARCHAR,
        bidder_name VARCHAR NOT NULL,
        bidder_country_code VARCHAR NOT NULL,
        bid_time_stamp TIMESTAMP WITH TIME ZONE NOT NULL,
        scraping_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        explanation_type text NOT NULL,
        bidder_token varchar NOT NULL,
        FOREIGN KEY (LID) REFERENCES meta_data (LID) ON DELETE CASCADE
);

CREATE TABLE image_data (
    RID SERIAL PRIMARY KEY,
    LID VARCHAR,
    url VARCHAR NOT NULL,
    orientation VARCHAR(20) CHECK (orientation IN ('landscape', 'portrait')),
    width INTEGER CHECK (width > 0),
    height INTEGER CHECK (height > 0),
    idx INTEGER NOT NULL,
    type VARCHAR,
    size VARCHAR(10) CHECK (size IN ('xs', 's', 'm', 'l', 'xl')),
    image_format VARCHAR,
    FOREIGN KEY (LID) REFERENCES meta_data (LID) ON DELETE CASCADE
);

CREATE TABLE meta (
    LID BIGINT PRIMARY KEY,
    category_int INT NOT NULL,
    category_name TEXT NOT NULL,
    currency_code CHAR(3) CHECK (currency_code IN ('USD', 'EUR', 'GBP')),
    estimated_delivery_times_days_lower INTEGER CHECK (estimated_delivery_times_days_lower >= 0),
    estimated_delivery_times_days_upper INTEGER CHECK (estimated_delivery_times_days_upper >= estimated_delivery_times_days_lower),
    price NUMERIC(10, 3) CHECK (price >= 0),
    combined_shipping_allowed BOOLEAN NOT NULL,
    FOREIGN KEY (LID) REFERENCES meta_data (LID) ON DELETE CASCADE
);




CREATE TABLE colored_gemstone_specs (
    LID VARCHAR PRIMARY KEY,
    total_carat_weight NUMERIC CHECK (total_carat_weight > 0),
    carat_weight_individual_stone NUMERIC CHECK (carat_weight_individual_stone > 0),
    gemstone_colour VARCHAR,
    gemstone_type VARCHAR,
    treatment VARCHAR,
    origin_as_given_on_certificate VARCHAR,
    laboratory_report VARCHAR,
    sealed VARCHAR,
    sealed_by_laboratory VARCHAR,
    transparency VARCHAR,
    cut_and_shape VARCHAR,
    cut_grade VARCHAR,
    cutting_style VARCHAR,
    stone VARCHAR,
    shape VARCHAR,
    clarity_grade VARCHAR,
    colour VARCHAR,
    nr_of_stones VARCHAR,
    optical_effect VARCHAR,
    title_additional_information VARCHAR,
    transparency_clarity VARCHAR,

    FOREIGN KEY (LID) REFERENCES meta_data (LID) ON DELETE CASCADE
);
