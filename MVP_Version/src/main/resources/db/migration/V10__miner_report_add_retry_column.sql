set schema 'public';

alter table miner_report
    add column desired_state_retry_count integer not null default 0;
