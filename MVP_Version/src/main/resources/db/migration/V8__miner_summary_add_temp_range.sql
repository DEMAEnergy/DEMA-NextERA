set schema 'public';

alter table miner_report
    add chip_min_temp int not null default 0,
    add chip_max_temp int not null default 0,
    add pcb_min_temp  int not null default 0,
    add pcb_max_temp  int not null default 0