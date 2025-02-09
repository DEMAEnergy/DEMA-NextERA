set schema 'public';

create table if not exists consumption_calculation
(
    id     varchar not null primary key,
    hash_rate double precision not null,
    coff1     double precision not null,
    coff2     double precision not null,
    coff3     double precision not null,
    preset_consumption double precision not null,
    calculated_consumption     double precision,
    created_at   timestamp not null
);