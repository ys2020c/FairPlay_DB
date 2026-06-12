-- Phase B - Queries for the Fair Play chess security system
-- The queries are written for PostgreSQL.

-- =========================================================
-- SELECT 1A: Monthly report volume by year and month
-- Screen: Admin dashboard
-- =========================================================
SELECT
  EXTRACT(YEAR FROM r.Report_Date) AS report_year,
  EXTRACT(MONTH FROM r.Report_Date) AS report_month,
  COUNT(*) AS total_reports,
  COUNT(i.Investigation_ID) AS opened_investigations,
  ROUND(COUNT(i.Investigation_ID)::NUMERIC / NULLIF(COUNT(*), 0), 2) AS investigations_per_report
FROM REPORTS r
LEFT JOIN INVESTIGATIONS i ON i.Report_ID = r.Report_ID
GROUP BY EXTRACT(YEAR FROM r.Report_Date), EXTRACT(MONTH FROM r.Report_Date)
ORDER BY report_year, report_month;

-- SELECT 1B: Same result using a CTE before grouping
WITH report_base AS (
  SELECT
    r.Report_ID,
    r.Report_Date,
    i.Investigation_ID
  FROM REPORTS r
  LEFT JOIN INVESTIGATIONS i ON i.Report_ID = r.Report_ID
)
SELECT
  EXTRACT(YEAR FROM Report_Date) AS report_year,
  EXTRACT(MONTH FROM Report_Date) AS report_month,
  COUNT(*) AS total_reports,
  COUNT(Investigation_ID) AS opened_investigations,
  ROUND(COUNT(Investigation_ID)::NUMERIC / NULLIF(COUNT(*), 0), 2) AS investigations_per_report
FROM report_base
GROUP BY EXTRACT(YEAR FROM Report_Date), EXTRACT(MONTH FROM Report_Date)
ORDER BY report_year, report_month;

-- =========================================================
-- SELECT 2A: Moderators with the heaviest open workload
-- Screen: Admin dashboard
-- =========================================================
SELECT
  m.Moderator_ID,
  m.Mname,
  m.Role,
  COUNT(i.Investigation_ID) AS open_investigations,
  MIN(i.Opened_Date) AS oldest_open_case
FROM MODERATORS m
JOIN INVESTIGATIONS i ON i.Moderator_ID = m.Moderator_ID
WHERE i.Status = 'In Progress'
GROUP BY m.Moderator_ID, m.Mname, m.Role
HAVING COUNT(i.Investigation_ID) >= 5
ORDER BY open_investigations DESC, oldest_open_case ASC
LIMIT 10;

-- SELECT 2B: Same result using a subquery that first counts workload
SELECT
  m.Moderator_ID,
  m.Mname,
  m.Role,
  workload.open_investigations,
  workload.oldest_open_case
FROM MODERATORS m
JOIN (
  SELECT
    Moderator_ID,
    COUNT(*) AS open_investigations,
    MIN(Opened_Date) AS oldest_open_case
  FROM INVESTIGATIONS
  WHERE Status = 'In Progress'
  GROUP BY Moderator_ID
  HAVING COUNT(*) >= 5
) workload ON workload.Moderator_ID = m.Moderator_ID
ORDER BY workload.open_investigations DESC, workload.oldest_open_case ASC
LIMIT 10;

-- =========================================================
-- SELECT 3A: Ban reasons that generate many appeals
-- Screen: Appeals management
-- =========================================================
SELECT
  br.Reason_ID,
  br.BR_Description,
  COUNT(b.Ban_ID) AS total_bans,
  COUNT(a.Appeal_ID) AS total_appeals,
  ROUND(COUNT(a.Appeal_ID)::NUMERIC / NULLIF(COUNT(b.Ban_ID), 0), 2) AS appeal_rate
FROM BAN_REASONS br
JOIN BANS b ON b.Reason_ID = br.Reason_ID
LEFT JOIN APPEALS a ON a.Ban_ID = b.Ban_ID
GROUP BY br.Reason_ID, br.BR_Description
HAVING COUNT(a.Appeal_ID) > 0
ORDER BY appeal_rate DESC, total_appeals DESC
LIMIT 10;

-- SELECT 3B: Same result using correlated subqueries
SELECT
  br.Reason_ID,
  br.BR_Description,
  (
    SELECT COUNT(*)
    FROM BANS b
    WHERE b.Reason_ID = br.Reason_ID
  ) AS total_bans,
  (
    SELECT COUNT(*)
    FROM BANS b
    JOIN APPEALS a ON a.Ban_ID = b.Ban_ID
    WHERE b.Reason_ID = br.Reason_ID
  ) AS total_appeals,
  ROUND((
    SELECT COUNT(*)::NUMERIC
    FROM BANS b
    JOIN APPEALS a ON a.Ban_ID = b.Ban_ID
    WHERE b.Reason_ID = br.Reason_ID
  ) / NULLIF((
    SELECT COUNT(*)
    FROM BANS b
    WHERE b.Reason_ID = br.Reason_ID
  ), 0), 2) AS appeal_rate
FROM BAN_REASONS br
WHERE EXISTS (
  SELECT 1
  FROM BANS b
  JOIN APPEALS a ON a.Ban_ID = b.Ban_ID
  WHERE b.Reason_ID = br.Reason_ID
)
ORDER BY appeal_rate DESC, total_appeals DESC
LIMIT 10;

-- =========================================================
-- SELECT 4A: Cases with evidence but no ban
-- Screen: Investigation room
-- =========================================================
SELECT
  i.Investigation_ID,
  r.Report_ID,
  r.Suspect_name,
  i.Status,
  COUNT(e.Evidence_ID) AS evidence_count,
  MAX(e.Evidence_Type) AS sample_evidence_type
FROM INVESTIGATIONS i
JOIN REPORTS r ON r.Report_ID = i.Report_ID
JOIN EVIDENCE e ON e.Investigation_ID = i.Investigation_ID
LEFT JOIN BANS b ON b.Investigation_ID = i.Investigation_ID
WHERE b.Ban_ID IS NULL
GROUP BY i.Investigation_ID, r.Report_ID, r.Suspect_name, i.Status
ORDER BY evidence_count DESC, i.Investigation_ID
LIMIT 20;

-- SELECT 4B: Same result using NOT EXISTS
SELECT
  i.Investigation_ID,
  r.Report_ID,
  r.Suspect_name,
  i.Status,
  COUNT(e.Evidence_ID) AS evidence_count,
  MAX(e.Evidence_Type) AS sample_evidence_type
FROM INVESTIGATIONS i
JOIN REPORTS r ON r.Report_ID = i.Report_ID
JOIN EVIDENCE e ON e.Investigation_ID = i.Investigation_ID
WHERE NOT EXISTS (
  SELECT 1
  FROM BANS b
  WHERE b.Investigation_ID = i.Investigation_ID
)
GROUP BY i.Investigation_ID, r.Report_ID, r.Suspect_name, i.Status
ORDER BY evidence_count DESC, i.Investigation_ID
LIMIT 20;

-- =========================================================
-- SELECT 5: Player file - full security history for a player
-- Screen: Player file
-- =========================================================
SELECT
  r.Suspect_name AS player_name,
  COUNT(DISTINCT r.Report_ID) AS total_reports,
  COUNT(DISTINCT i.Investigation_ID) AS total_investigations,
  COUNT(DISTINCT b.Ban_ID) AS total_bans,
  COUNT(DISTINCT a.Appeal_ID) AS total_appeals,
  MAX(r.Report_Date) AS latest_report_date
FROM REPORTS r
LEFT JOIN INVESTIGATIONS i ON i.Report_ID = r.Report_ID
LEFT JOIN BANS b ON b.Investigation_ID = i.Investigation_ID
LEFT JOIN APPEALS a ON a.Ban_ID = b.Ban_ID
GROUP BY r.Suspect_name
HAVING COUNT(DISTINCT r.Report_ID) >= 2
ORDER BY total_reports DESC, latest_report_date DESC
LIMIT 20;

-- =========================================================
-- SELECT 6: Average investigation duration by moderator role
-- Screen: Admin dashboard
-- =========================================================
SELECT
  m.Role,
  COUNT(i.Investigation_ID) AS closed_cases,
  ROUND(AVG(i.Closed_Date - i.Opened_Date), 2) AS avg_days_to_close,
  MIN(i.Closed_Date - i.Opened_Date) AS fastest_case_days,
  MAX(i.Closed_Date - i.Opened_Date) AS slowest_case_days
FROM MODERATORS m
JOIN INVESTIGATIONS i ON i.Moderator_ID = m.Moderator_ID
WHERE i.Status = 'Closed'
  AND i.Closed_Date IS NOT NULL
GROUP BY m.Role
ORDER BY avg_days_to_close DESC;

-- =========================================================
-- SELECT 7: Evidence type distribution by month
-- Screen: Investigation room
-- =========================================================
SELECT
  EXTRACT(YEAR FROM i.Opened_Date) AS opened_year,
  EXTRACT(MONTH FROM i.Opened_Date) AS opened_month,
  e.Evidence_Type,
  COUNT(*) AS evidence_items,
  COUNT(DISTINCT i.Investigation_ID) AS related_investigations
FROM EVIDENCE e
JOIN INVESTIGATIONS i ON i.Investigation_ID = e.Investigation_ID
GROUP BY EXTRACT(YEAR FROM i.Opened_Date), EXTRACT(MONTH FROM i.Opened_Date), e.Evidence_Type
ORDER BY opened_year, opened_month, evidence_items DESC;

-- =========================================================
-- SELECT 8: Recent bans with appeal status and reason
-- Screen: Appeals management
-- =========================================================
SELECT
  b.Ban_ID,
  b.Banned_Player,
  b.Start_Date,
  b.End_Date,
  br.BR_Description AS ban_reason,
  COALESCE(a.Decision, 'No appeal') AS appeal_status,
  m.Mname AS appeal_moderator
FROM BANS b
JOIN BAN_REASONS br ON br.Reason_ID = b.Reason_ID
LEFT JOIN APPEALS a ON a.Ban_ID = b.Ban_ID
LEFT JOIN MODERATORS m ON m.Moderator_ID = a.Moderator_ID
WHERE b.Start_Date >= DATE '2023-01-01'
ORDER BY b.Start_Date DESC, b.Ban_ID DESC
LIMIT 20;

-- =========================================================
-- UPDATE 1: Assign old open investigations to a senior moderator
-- =========================================================
UPDATE INVESTIGATIONS
SET Moderator_ID = (
  SELECT Moderator_ID
  FROM MODERATORS
  WHERE Role = 'Senior moderator'
  ORDER BY Hire_Date ASC
  LIMIT 1
)
WHERE Status = 'In Progress'
  AND Opened_Date < DATE '2023-06-01';

-- UPDATE 2: Mark old pending appeals as denied for demo data cleanup
UPDATE APPEALS
SET Decision = 'Denied'
WHERE Decision = 'Pending'
  AND Submission_Date < DATE '2023-06-01';

-- UPDATE 3: Extend bans connected to system-log evidence
UPDATE BANS b
SET End_Date = End_Date + 7
WHERE EXISTS (
  SELECT 1
  FROM EVIDENCE e
  WHERE e.Investigation_ID = b.Investigation_ID
    AND e.Evidence_Type = 'System Log'
);

-- =========================================================
-- DELETE 1: Delete appeals that point to short demo bans
-- =========================================================
DELETE FROM APPEALS a
WHERE EXISTS (
  SELECT 1
  FROM BANS b
  WHERE b.Ban_ID = a.Ban_ID
    AND b.End_Date - b.Start_Date <= 1
);

-- DELETE 2: Delete evidence rows that use non-http demo links
DELETE FROM EVIDENCE
WHERE URL_Link NOT LIKE 'http%';

-- DELETE 3: Delete orphan investigations that are not linked to a report
DELETE FROM INVESTIGATIONS
WHERE Report_ID IS NULL
  AND NOT EXISTS (
    SELECT 1
    FROM EVIDENCE e
    WHERE e.Investigation_ID = INVESTIGATIONS.Investigation_ID
  )
  AND NOT EXISTS (
    SELECT 1
    FROM BANS b
    WHERE b.Investigation_ID = INVESTIGATIONS.Investigation_ID
  );
