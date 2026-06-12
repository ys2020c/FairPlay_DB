-- Phase B - Rollback and Commit demonstrations

-- =========================================================
-- ROLLBACK demo
-- Goal: change one appeal decision, show the change, rollback, and show it was cancelled.
-- =========================================================
SELECT Appeal_ID, Decision, Submission_Date
FROM APPEALS
WHERE Appeal_ID = 1;

BEGIN;

UPDATE APPEALS
SET Decision = 'Accepted'
WHERE Appeal_ID = 1;

SELECT Appeal_ID, Decision, Submission_Date
FROM APPEALS
WHERE Appeal_ID = 1;

ROLLBACK;

SELECT Appeal_ID, Decision, Submission_Date
FROM APPEALS
WHERE Appeal_ID = 1;

-- =========================================================
-- COMMIT demo
-- Goal: update one investigation status, commit, and show the change remains.
-- =========================================================
SELECT Investigation_ID, Status, Opened_Date, Closed_Date
FROM INVESTIGATIONS
WHERE Investigation_ID = 2;

BEGIN;

UPDATE INVESTIGATIONS
SET Status = 'Closed',
    Closed_Date = COALESCE(Closed_Date, Opened_Date + 3)
WHERE Investigation_ID = 2;

SELECT Investigation_ID, Status, Opened_Date, Closed_Date
FROM INVESTIGATIONS
WHERE Investigation_ID = 2;

COMMIT;

SELECT Investigation_ID, Status, Opened_Date, Closed_Date
FROM INVESTIGATIONS
WHERE Investigation_ID = 2;
