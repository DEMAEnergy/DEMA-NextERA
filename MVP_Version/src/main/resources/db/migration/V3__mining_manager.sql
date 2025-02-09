set schema 'public';

create table if not exists miner_info (
    miner_id text not null primary key,
    miner_ip text not null,
    miner_port integer not null,
    created_at    timestamp not null,
    updated_at    timestamp
);

create table if not exists miner_report (
    id             uuid DEFAULT gen_random_uuid() primary key,
    miner_id text not null references miner_info(miner_id),
    miner_state text not null,
    miner_uptime text not null,
    miner_type text not null,
    average_hashrate text not null,
    instant_hashrate text not null,
    power_usage int not null,
    power_efficiency float not null,
    created_at    timestamp not null
);