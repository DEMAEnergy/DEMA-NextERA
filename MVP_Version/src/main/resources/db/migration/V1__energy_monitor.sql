set schema 'public';

create table if not exists locations
(
    id      integer not null primary key,
    country text    not null,
    state   text,
    region  text,
    city    text    not null,
    created_at timestamp not null
);

insert into locations
values (1, 'USA', 'TEXAS', null, 'AUSTIN', now());

create table if not exists plc
(
    id         integer   not null
        primary key,
    ip         text      not null,
    port       integer   not null,
    register   integer   not null,
    location   integer   not null references locations (id),
    delay      integer   not null,
    created_at timestamp not null,
    updated_at integer
);

insert into plc
values (1, '192.168.110.201', 502, 332, 1, 30, now(), null);

create table wattage_meter
(
    consumption_id uuid DEFAULT gen_random_uuid()
        primary key,
    wattage        integer   not null,
    created_at      timestamp not null,
    plc_id         integer   not null references plc (id)
);

create table apis
(
    id         integer   not null
        primary key,
    path       text      not null,
    endpoint   text      not null,
    api_key    text,
    location   integer references locations (id),
    delay      integer   not null,
    created_at timestamp not null,
    updated_at timestamp
);

insert into apis
values (1, 'https://linkedupenergy.com/api/APIREST.php', 'getercotersactiveevent',
        'ZmFyaXNAZGVtYWVuZXJneS5jb20uc2E6REVNQTIwMjN0ZXhhc0BAQA', 1, 30, now(), null),
       (2, 'https://linkedupenergy.com/api/APIREST.php', 'getcurrentlmp',
        'ZmFyaXNAZGVtYWVuZXJneS5jb20uc2E6REVNQTIwMjN0ZXhhc0BAQA', 1, 30, now(), null);

create table emergency_events
(
    event_id  uuid DEFAULT gen_random_uuid()
        primary key,
    active    integer   not null,
    created_at timestamp not null,
    api_id    integer   not null references apis (id)
);


create table if not exists market_prices
(
    id        uuid DEFAULT gen_random_uuid() primary key,
    price     float     not null,
    created_at timestamp not null,
    api_id    integer   not null references apis (id)
);

create table if not exists market_predictions
(
    id             uuid DEFAULT gen_random_uuid() primary key,
    rtd_datetime   timestamp not null,
    price          float     not null,
    price_5  float     not null,
    price_10 float     not null,
    price_15 float     not null,
    price_20 float     not null,
    price_25 float     not null,
    price_30 float     not null,
    price_35 float     not null,
    price_40 float     not null,
    price_45 float     not null,
    price_50 float     not null,
    price_55 float     not null,
    created_at    timestamp not null
);

create table if not exists day_ahead_market
(
    id               uuid DEFAULT gen_random_uuid() primary key,
    bid_id           text      not null,
    start_time       timestamp not null,
    end_time         timestamp not null,
    settlement_point text      not null,
    awarded_mwh      float     not null,
    spp              float     not null,
    created_at        timestamp not null
);
