-- Run as a superuser:  psql -d prt661_housing -v pw_ahsan=... -v pw_ferdous=... -v pw_raiyan=... -v pw_abrar=... -v pw_app=... -f create_member_logins.sql
-- Passwords are passed at run time and never committed to Git.
CREATE ROLE ahsan_uddin    LOGIN PASSWORD :'pw_ahsan'   IN ROLE prt661_etl;      -- acquisition owner
CREATE ROLE ferdous_anik   LOGIN PASSWORD :'pw_ferdous' IN ROLE prt661_etl;      -- data engineering owner
CREATE ROLE raiyan_mohd    LOGIN PASSWORD :'pw_raiyan'  IN ROLE prt661_analyst;  -- modelling (read-only)
CREATE ROLE abrar_khaiyum  LOGIN PASSWORD :'pw_abrar'   IN ROLE prt661_analyst;  -- app & docs (read-only)
CREATE ROLE prt661_app     LOGIN PASSWORD :'pw_app'     IN ROLE prt661_app_ro CONNECTION LIMIT 20;
