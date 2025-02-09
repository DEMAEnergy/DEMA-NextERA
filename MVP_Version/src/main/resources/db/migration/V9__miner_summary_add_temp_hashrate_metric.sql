set schema 'public';

alter table miner_report
    add column temp_frequency_metric jsonb;
