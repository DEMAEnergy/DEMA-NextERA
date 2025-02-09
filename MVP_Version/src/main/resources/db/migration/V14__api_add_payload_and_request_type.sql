set schema 'public';

ALTER TABLE apis
ADD COLUMN payload text;

ALTER TABLE apis
ADD COLUMN request_type text;
