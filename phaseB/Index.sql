-- Phase B - Indexes and runtime checks
-- Run each EXPLAIN ANALYZE before and after the matching CREATE INDEX.

-- =========================================================
-- Index 1: Reports by report date
-- Supports dashboard filtering by year/month/date range.
-- =========================================================
EXPLAIN ANALYZE
SELECT
  EXTRACT(YEAR FROM Report_Date) AS report_year,
  EXTRACT(MONTH FROM Report_Date) AS report_month,
  COUNT(*) AS total_reports
FROM REPORTS
WHERE Report_Date BETWEEN DATE '2023-01-01' AND DATE '2023-12-31'
GROUP BY EXTRACT(YEAR FROM Report_Date), EXTRACT(MONTH FROM Report_Date)
ORDER BY report_year, report_month;

CREATE INDEX idx_reports_report_date
ON REPORTS (Report_Date);

EXPLAIN ANALYZE
SELECT
  EXTRACT(YEAR FROM Report_Date) AS report_year,
  EXTRACT(MONTH FROM Report_Date) AS report_month,
  COUNT(*) AS total_reports
FROM REPORTS
WHERE Report_Date BETWEEN DATE '2023-01-01' AND DATE '2023-12-31'
GROUP BY EXTRACT(YEAR FROM Report_Date), EXTRACT(MONTH FROM Report_Date)
ORDER BY report_year, report_month;

-- =========================================================
-- Index 2: Investigation status and open date
-- Supports finding old open investigations quickly.
-- =========================================================
EXPLAIN ANALYZE
SELECT
  Investigation_ID,
  Opened_Date,
  Status,
  Moderator_ID
FROM INVESTIGATIONS
WHERE Status = 'In Progress'
  AND Opened_Date < DATE '2023-06-01'
ORDER BY Opened_Date ASC
LIMIT 20;

CREATE INDEX idx_investigations_status_opened
ON INVESTIGATIONS (Status, Opened_Date);

EXPLAIN ANALYZE
SELECT
  Investigation_ID,
  Opened_Date,
  Status,
  Moderator_ID
FROM INVESTIGATIONS
WHERE Status = 'In Progress'
  AND Opened_Date < DATE '2023-06-01'
ORDER BY Opened_Date ASC
LIMIT 20;

-- =========================================================
-- Index 3: Bans by reason and start date
-- Supports analytics for common ban reasons over time.
-- =========================================================
EXPLAIN ANALYZE
SELECT
  Reason_ID,
  COUNT(*) AS total_bans,
  MIN(Start_Date) AS first_ban,
  MAX(Start_Date) AS latest_ban
FROM BANS
WHERE Start_Date >= DATE '2023-01-01'
GROUP BY Reason_ID
ORDER BY total_bans DESC;

CREATE INDEX idx_bans_reason_start
ON BANS (Reason_ID, Start_Date);

EXPLAIN ANALYZE
SELECT
  Reason_ID,
  COUNT(*) AS total_bans,
  MIN(Start_Date) AS first_ban,
  MAX(Start_Date) AS latest_ban
FROM BANS
WHERE Start_Date >= DATE '2023-01-01'
GROUP BY Reason_ID
ORDER BY total_bans DESC;
