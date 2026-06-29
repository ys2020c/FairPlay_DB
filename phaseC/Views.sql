-- Views.sql

-- ==========================================
-- View 1: Suspicious_Games_View
-- Perspective: הנהלת השחמט
-- Purpose: מציג משחקים שעליהם התקבלו דיווחים, כולל סוג המשחק וזמן המשחק
-- ==========================================
CREATE VIEW Suspicious_Games_View AS
SELECT 
    g.game_id,
    g.start_date,
    g.result,
    tc.name AS Time_Control,
    gv.name AS Variant,
    COUNT(r.Report_ID) AS Total_Reports
FROM 
    Game g
JOIN 
    REPORTS r ON g.game_id = r.Game_ID
LEFT JOIN 
    TimeControl tc ON g.tc_id = tc.tc_id
LEFT JOIN 
    GameVariant gv ON g.variant_id = gv.variant_id
GROUP BY 
    g.game_id, g.start_date, g.result, tc.name, gv.name;

-- Query 1.1: מציאת משחקים עם יותר מדיווח אחד
SELECT * FROM Suspicious_Games_View
WHERE Total_Reports > 1
ORDER BY Total_Reports DESC;

-- Query 1.2: מציאת משחקים חשודים מסוג בליץ
SELECT * FROM Suspicious_Games_View
WHERE Time_Control = 'Blitz'
ORDER BY start_date DESC;

-- ==========================================
-- View 2: Moderation_Queue_View
-- Perspective: מערכת האכיפה והמודרציה (FairPlay)
-- Purpose: מציג את החקירות הפעילות יחד עם פרטי הדיווח והמשחק ששוחק
-- ==========================================
CREATE VIEW Moderation_Queue_View AS
SELECT 
    i.Investigation_ID,
    i.Opened_Date,
    i.Status,
    m.Mname AS Moderator_Name,
    r.Report_ID,
    r.Description AS Report_Reason,
    g.game_id,
    g.start_date AS Game_Date
FROM 
    INVESTIGATIONS i
JOIN 
    MODERATORS m ON i.Moderator_ID = m.Moderator_ID
JOIN 
    REPORTS r ON i.Report_ID = r.Report_ID
JOIN 
    Game g ON r.Game_ID = g.game_id;

-- Query 2.1: הצגת כל החקירות הפתוחות כרגע עם פרטי המשחקים
SELECT * FROM Moderation_Queue_View
WHERE Status = 'In Progress'
ORDER BY Opened_Date;

-- Query 2.2: בדיקת עומס על כל מודרטור ותאריך המשחק הישן ביותר בטיפולו
SELECT 
    Moderator_Name,
    COUNT(Investigation_ID) as Active_Investigations,
    MIN(Game_Date) as Oldest_Game
FROM 
    Moderation_Queue_View
WHERE 
    Status = 'In Progress'
GROUP BY 
    Moderator_Name;
