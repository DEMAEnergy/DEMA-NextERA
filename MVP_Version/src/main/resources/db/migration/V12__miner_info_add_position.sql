set schema 'public';

alter table miner_info
    add column miner_position uuid references positions (id);
