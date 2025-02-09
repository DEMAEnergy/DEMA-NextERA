set schema 'public';

create table if not exists ms_optimization
(
    id     varchar not null primary key,
    status  varchar not null,
    energy_price double precision not null,
    hash_price double precision not null,
    machine_data       json not null,
    target_power     double precision not null,
    created_at       timestamp not null,
    updated_at       timestamp
);