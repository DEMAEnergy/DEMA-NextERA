set schema 'public';

alter table miner_report
    add desired_state varchar(20) default 'MINING' not null;

alter table miner_info
    add desired_state varchar(20) default 'MINING' not null;

