-- Phase B - Constraints added with ALTER TABLE
-- These constraints are meant to improve data quality after the first schema.

-- 1. A player should not report themselves.
ALTER TABLE REPORTS
ADD CONSTRAINT chk_reports_reporter_not_suspect
CHECK (Reporter_name <> Suspect_name) NOT VALID;

-- Demo: this insert should fail because reporter and suspect are identical.
BEGIN;
INSERT INTO REPORTS (Report_ID, Reporter_name, Suspect_name, Game_ID, Report_Date, Description)
VALUES (900001, 'ChessPlayer_77', 'ChessPlayer_77', 10, DATE '2024-01-01', 'Self report demo');
ROLLBACK;

-- 2. Each report should be connected to at most one investigation.
ALTER TABLE INVESTIGATIONS
ADD CONSTRAINT uq_investigations_report
UNIQUE (Report_ID);

-- Demo: this insert should fail if report 1 already has an investigation.
BEGIN;
INSERT INTO INVESTIGATIONS (Investigation_ID, Opened_Date, Closed_Date, Status, Moderator_ID, Report_ID)
VALUES (900001, DATE '2024-01-02', NULL, 'In Progress', 1, 1);
ROLLBACK;

-- 3. Evidence links should look like URLs.
ALTER TABLE EVIDENCE
ADD CONSTRAINT chk_evidence_url_format
CHECK (URL_Link LIKE 'http%') NOT VALID;

-- Demo: this insert should fail because the link is not a URL.
BEGIN;
INSERT INTO EVIDENCE (Evidence_ID, Evidence_Type, URL_Link, Investigation_ID)
VALUES (900001, 'Screenshot', 'local-file-without-url', 1);
ROLLBACK;
