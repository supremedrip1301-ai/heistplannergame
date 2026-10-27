-- =====================================================================
-- Heist Planner Game - create the application user HEIST
-- ---------------------------------------------------------------------
-- Run ONCE as SYSTEM, connected to the pluggable database FREEPDB1:
--
--   Windows installer (Route A), from the project folder:
--     sqlplus system@localhost:1521/FREEPDB1 @database\create_oracle_user.sql
--   WSL 2 container (Route B):
--     podman exec -it oracle26ai sqlplus system@FREEPDB1 @/tmp/create_oracle_user.sql
--
-- SQL*Plus asks for the new HEIST password, so no password is stored in
-- this file. The game itself never connects as SYS or SYSTEM.
-- Works on Oracle AI Database 26ai Free and on Oracle Database 19c.
-- =====================================================================
SET SERVEROUTPUT ON
SET VERIFY OFF

ACCEPT heist_password CHAR PROMPT 'Choose a password for the HEIST user: ' HIDE

-- Create the user; if it already exists, keep it and just refresh the grants.
DECLARE
    user_exists EXCEPTION;
    PRAGMA EXCEPTION_INIT(user_exists, -1920);
BEGIN
    EXECUTE IMMEDIATE 'CREATE USER heist IDENTIFIED BY "&heist_password" '
                   || 'DEFAULT TABLESPACE users QUOTA UNLIMITED ON users';
    DBMS_OUTPUT.PUT_LINE('User HEIST created.');
EXCEPTION
    WHEN user_exists THEN
        DBMS_OUTPUT.PUT_LINE('User HEIST already exists - password unchanged, grants refreshed.');
END;
/

ALTER USER heist QUOTA UNLIMITED ON users;

-- Only the privileges the game's objects need.
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE PROCEDURE,
      CREATE TRIGGER, CREATE VIEW TO heist;

PROMPT Done. Next: connect as HEIST and run database/setup_oracle.sql
