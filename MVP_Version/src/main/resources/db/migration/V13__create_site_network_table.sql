set schema 'public';


create table if not exists site_network (
    id integer not null primary key,
    location    integer references locations (id),
    path        varchar not null,
    created_at  timestamp not null
);

insert into site_network (id, location, path, created_at)
values
(1, 1, '192.168.110.22/32', CURRENT_TIMESTAMP);

UPDATE locations
SET
    country = 'KSA',
    state = NULL,
    region = 'Eastern Province',
    city = 'Dhahran'
WHERE
    id = 1;
