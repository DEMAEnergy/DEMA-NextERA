set schema 'public';

create table if not exists containers
(
    id          integer not null primary key,
    created_at  timestamp not null,
    location    integer references locations (id)
);

create table if not exists tanks
(
    id          integer not null primary key,
    created_at  timestamp not null,
    container   integer references containers (id)
    );


create table if not exists positions
(
    id          uuid DEFAULT gen_random_uuid() primary key,
    row         integer not null,
    col         varchar not null,    created_at  timestamp not null,
    tank        integer references tanks (id)
);

insert into containers (id, location, created_at)
values (1 ,1, CURRENT_TIMESTAMP);

insert into tanks (id, container, created_at)
values (1 ,1, CURRENT_TIMESTAMP);

insert into positions (row, col, created_at, tank)
values
(1, 'A', CURRENT_TIMESTAMP, 1),
(1, 'B', CURRENT_TIMESTAMP, 1),
(2, 'A', CURRENT_TIMESTAMP, 1),
(2, 'B', CURRENT_TIMESTAMP, 1),
(3, 'A', CURRENT_TIMESTAMP, 1),
(3, 'B', CURRENT_TIMESTAMP, 1),
(4, 'A', CURRENT_TIMESTAMP, 1),
(4, 'B', CURRENT_TIMESTAMP, 1),
(5, 'A', CURRENT_TIMESTAMP, 1),
(5, 'B', CURRENT_TIMESTAMP, 1),
(6, 'A', CURRENT_TIMESTAMP, 1),
(6, 'B', CURRENT_TIMESTAMP, 1),
(7, 'A', CURRENT_TIMESTAMP, 1),
(7, 'B', CURRENT_TIMESTAMP, 1),
(8, 'A', CURRENT_TIMESTAMP, 1),
(8, 'B', CURRENT_TIMESTAMP, 1),
(9, 'A', CURRENT_TIMESTAMP, 1),
(9, 'B', CURRENT_TIMESTAMP, 1),
(10, 'A', CURRENT_TIMESTAMP, 1),
(10, 'B', CURRENT_TIMESTAMP, 1),
(11, 'A', CURRENT_TIMESTAMP, 1),
(11, 'B', CURRENT_TIMESTAMP, 1),
(12, 'A', CURRENT_TIMESTAMP, 1),
(12, 'B', CURRENT_TIMESTAMP, 1),
(13, 'A', CURRENT_TIMESTAMP, 1),
(13, 'B', CURRENT_TIMESTAMP, 1),
(14, 'A', CURRENT_TIMESTAMP, 1),
(14, 'B', CURRENT_TIMESTAMP, 1),
(15, 'A', CURRENT_TIMESTAMP, 1),
(15, 'B', CURRENT_TIMESTAMP, 1);