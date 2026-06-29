$text = @"

-- Add reports without investigations to vary the ratio for Query 1
INSERT INTO REPORTS (Report_ID, Reporter_name, Suspect_name, Game_ID, Report_Date, Description)
SELECT Report_ID + 50000, Reporter_name, Suspect_name, Game_ID, Report_Date, Description
FROM REPORTS
WHERE MOD(Report_ID, 5) = 0;
"@
Add-Content -Path 'c:\Users\bshay\FairPlay_DB\FairPlay_DB\init-db\07-insertTables.sql' -Value $text
