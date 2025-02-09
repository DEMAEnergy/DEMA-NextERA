set schema 'public';

create table if not exists public.strike_price
(
    id               varchar          not null
        constraint id
            primary key,
    miner_hash_rate  double precision not null,
    miner_efficiency double precision not null,
    hash_price       double precision not null,
    strike_price     double precision not null,
    miner_id         varchar          not null,
    created_at       timestamp
);

CREATE UNIQUE INDEX IF NOT EXISTS strike_price_id_uindex
    on public.strike_price (id);


create table if not exists  public.strike_price_calculation
(
    id         varchar          not null
        constraint strike_price_calculation_pkey
            primary key,
    c1         double precision not null,
    c2         double precision not null,
    c3         double precision not null,
    created_at timestamp,
    equation   varchar          not null

);

insert into strike_price_calculation (id, c1, c2, c3, created_at, equation)
values (gen_random_uuid(),
        0.0559,
        20.541,
        490.57,
        now(),
        'y = 0.0559x2 + 20.541x + 490.57') ON CONFLICT DO NOTHING;


create table if not exists  public.economic_dispatcher
(
    id         varchar          not null
        constraint economic_dispatcher_pkey
            primary key,
    RTM_Price      double precision not null,
    optimizedPowerTarget double precision not null,
    strikePrices   jsonb,
    minersPowerUsages jsonb,
    created_at timestamp
);

create unique index IF NOT EXISTS economic_dispatcher_id_uindex
    on public.economic_dispatcher (id);
