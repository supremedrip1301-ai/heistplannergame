SET SERVEROUTPUT ON
-- =====================================================================
-- Heist Planner Game - manual Oracle test (run as HEIST after setup_oracle.sql)
--   Windows installer (Route A), from the project folder:
--     sqlplus heist@localhost:1521/FREEPDB1 @database\oracle_manual_test.sql
--   WSL 2 container (Route B):
--     podman cp database/oracle_manual_test.sql oracle26ai:/tmp/
--     podman exec -it oracle26ai sqlplus heist@FREEPDB1 @/tmp/oracle_manual_test.sql
--
-- Everything this test inserts is removed again by the ROLLBACK at the end,
-- so it never pollutes the game history.
-- =====================================================================
SET LINESIZE 160
SET PAGESIZE 50

PROMPT === 1. HP_SAVE_RUN saves a run and returns its ID ===
DECLARE
    v_run_id NUMBER;
BEGIN
    hp_save_run('SQLPLUS_TEST', 'gallery', 'SUCCESS', 810, 24, 28,
                'Pocket Scanner, Mobility Boots, Repair Module', 'N', v_run_id);
    DBMS_OUTPUT.PUT_LINE('OK  - saved run ' || v_run_id);
    hp_save_run('SQLPLUS_TEST', 'relay', 'ABANDONED', 0, 7, 9, 'None', 'Y', v_run_id);
    DBMS_OUTPUT.PUT_LINE('OK  - saved abandoned run ' || v_run_id
                         || ' (same player reused, not duplicated)');
END;
/

PROMPT === 2. HP_GET_STATS (one player, unknown player, all players) ===
DECLARE
    v_total NUMBER; v_success NUMBER; v_best NUMBER; v_avg NUMBER;
BEGIN
    hp_get_stats('SQLPLUS_TEST', v_total, v_success, v_best, v_avg);
    DBMS_OUTPUT.PUT_LINE('SQLPLUS_TEST: runs ' || v_total || ', successful ' || v_success
                         || ', best ' || v_best || ', average ' || v_avg
                         || '   (expected 2, 1, 810, 810)');
    hp_get_stats('NOBODY_AT_ALL', v_total, v_success, v_best, v_avg);
    DBMS_OUTPUT.PUT_LINE('Unknown player: runs ' || v_total || ', successful ' || v_success
                         || ', best ' || v_best || ', average ' || v_avg
                         || '   (expected all 0)');
    hp_get_stats(NULL, v_total, v_success, v_best, v_avg);
    DBMS_OUTPUT.PUT_LINE('All players: runs ' || v_total);
END;
/

PROMPT === 3. Invalid input is reported with RAISE_APPLICATION_ERROR ===
DECLARE
    v_run_id NUMBER;
BEGIN
    hp_save_run('SQLPLUS_TEST', 'gallery', 'SUCCESS', -5, 1, 1, 'None', 'N', v_run_id);
    DBMS_OUTPUT.PUT_LINE('FAIL - a negative score was accepted');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('OK  - negative score rejected: ' || SQLERRM);
END;
/
DECLARE
    v_run_id NUMBER;
BEGIN
    hp_save_run('SQLPLUS_TEST', 'moonbase', 'SUCCESS', 100, 1, 1, 'None', 'N', v_run_id);
    DBMS_OUTPUT.PUT_LINE('FAIL - an unknown mission was accepted');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('OK  - unknown mission rejected: ' || SQLERRM);
END;
/

PROMPT === 4. HP_RANK_TITLE (expected Phantom, Specialist, Operative, Rookie) ===
SELECT hp_rank_title(810) AS r810, hp_rank_title(700) AS r700,
       hp_rank_title(500) AS r500, hp_rank_title(100) AS r100
  FROM dual;

PROMPT === 5. Audit trigger copied the new runs ===
SELECT a.audit_id, a.run_id, a.score, a.db_user
  FROM hp_run_audit a
  JOIN hp_mission_runs r ON r.run_id = a.run_id
  JOIN hp_players p ON p.player_id = r.player_id
 WHERE p.player_name = 'SQLPLUS_TEST'
 ORDER BY a.audit_id;

PROMPT === 6. HP_PRINT_RECENT_RUNS (explicit cursor report) ===
EXEC hp_print_recent_runs(5)

PROMPT === 7. Remove the test rows ===
ROLLBACK;
PROMPT Test rows rolled back. Manual test finished.
