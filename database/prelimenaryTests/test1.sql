CREATE TABLE meta
(
    lid                     BIGINT PRIMARY KEY,
    category_int            INT                      NOT NULL,
    category_name           TEXT                     NOT NULL,
    meta_timestamp timestamp with time zone not null /* First time we scraped this lot */
);

ALTER TABLE meta
ADD COLUMN last_processed_timestamp TIMESTAMP WITH TIME ZONE,
ADD COLUMN status TEXT CHECK (status IN ('new', 'in_q', 'processing', 'idle', 'closed', 'processed'));




CREATE TABLE auction
(
    lid bigint primary key,
    experts_estimate_min NUMERIC,
    experts_estimate_max NUMERIC,
    bidding_start_timestamp TIMESTAMP with time zone not null,
    bidding_close_timestamp TIMESTAMP with time zone not null,
    realtime_channel varchar,
    aid bigint,
    latest_bid_timestamp timestamp with time zone not null,
    soup_timestamp timestamp with time zone not null,
    FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE
);

CREATE TABLE auction_history
(
    ahid serial primary key,
    lid bigint not null,
    is_closed boolean not null,
    time_to_close timestamp with time zone not null,
    is_buy_now_available boolean not null,
    latest_bid_timestamp timestamp with time zone not null,
    FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE
);

CREATE TABLE spec
(
    lid BIGINT primary key,
    spec_dict json not null,
    category_name text not null,
    category_int INT not null,
    soup_timestamp timestamp with time zone not null, /* Timestamp for the soup we downloaded */
    description text,
    sellers_story text,
    FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE
);

CREATE TABLE favorite_history
(
    lhid serial primary key,
    lid int not null,
    favorite_count int not null,
    latest_bid_timestamp timestamp with time zone not null,
    FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE
);

CREATE TABLE bid
(
    bid_id bigint primary key, /* bid id, lol */
    lid bigint not null,
    amount numeric not null CHECK (amount >= 0),
    currency_code CHAR(3) CHECK (currency_code IN ('USD', 'EUR', 'GBP')),
    from_order boolean not null,
    explanation_type text,
    bid_placed_timestamp timestamp with time zone not null, /* when the bid was placed */
    bidder_name varchar not null,
    bidder_token varchar not null,
    bidder_country_code text not null,
    bid_api_timestamp timestamp with time zone not null, /* When we downloaded the api data */
    is_final_bid boolean not null,
    is_reserve_price_met int not null,
    favorite_count int not null,
    aid bigint not null,
    latest_bid_timestamp timestamp with time zone not null,
    FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE
);

CREATE TABLE image
(
    iid serial primary key,
    lid bigint not null,
    image_idx int not null,
    image_type text not null,
    size text not null CHECK (size IN ('xs', 's', 'm', 'l', 'xl')),
    url varchar unique not null,
    orientation text not null,
    width int not null CHECK (width > 0),
    height int not null CHECK (height > 0),
    images_timestamp timestamp with time zone not null,
    FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE
);

CREATE TABLE shipping
(
  sid SERIAL PRIMARY KEY,
  lid BIGINT NOT NULL,
  region_code TEXT NOT NULL,
  region_name TEXT NOT NULL,
  price NUMERIC NOT NULL CHECK (price >= 0),
  currency_code CHAR(3) CHECK (currency_code IN ('USD', 'EUR', 'GBP')),
  estimated_delivery_from_days INT NOT NULL, /* Earliest number of days to deliver */
  estimated_delivery_to_days INT NOT NULL, /* Latest number of days to deliver */
  destination_country_name TEXT NOT NULL,
  destination_country_short_code TEXT NOT NULL,
  combined_shipping_allowed BOOL NOT NULL,
  delivery_methods TEXT NOT NULL,
  extra_insurance BOOLEAN NOT NULL,
  provider_id INT NOT NULL,
  is_pickup_preferable BOOLEAN NOT NULL,
  is_pickup_only BOOLEAN NOT NULL,
  pickup_location_country_code TEXT,
  pickup_location_city TEXT,
  shipping_timestamp TIMESTAMP WITH TIME ZONE NOT NULL, /* Timestamp for when we request the shipping API */
  FOREIGN KEY (lid) REFERENCES meta (lid) ON DELETE CASCADE,
  UNIQUE (lid, price, region_code,currency_code)
);



SELECT pg_backend_pid();

ALTER TABLE spec ADD COLUMN description text;

select pid, pg_blocking_pids(pid) as blocked_by, query as blocked_query
from pg_stat_activity
where pg_blocking_pids(pid)::text != '{}';

VACUUM (VERBOSE, ANALYZE) spec;