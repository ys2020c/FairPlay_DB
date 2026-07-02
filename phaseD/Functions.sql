-- ======================================================================================
-- Functions.sql
-- שלב ד: יצירת שתי פונקציות ב-PL/pgSQL
-- אחת הפונקציות עושה שימוש מפורש ב-Cursor
-- ======================================================================================

-- --------------------------------------------------------------------------------------
-- פונקציה 1: calculate_moderator_bonus (כוללת שימוש ב-Cursor)
-- תיאור: מחשבת את הבונוס הכספי של מודרטור בחודש ושנה מסוימים.
-- לוגיקה: עוברת באמצעות סמן (Cursor) על כל החסימות (Bans) שהופקו כתוצאה מחקירות של אותו
-- מודרטור, שנסגרו בחודש המבוקש. הבונוס מחושב לפי חומרת העבירה (משך החסימה בדיפולט).
-- --------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_moderator_bonus(p_moderator_id INT, p_year INT, p_month INT)
RETURNS NUMERIC AS $$
DECLARE
    total_bonus NUMERIC := 0.0;
    ban_record RECORD;
    -- הגדרת הסמן (Cursor) לשליפת נתוני החסימות הרלוונטיות
    cur_bans CURSOR FOR 
        SELECT (b.End_Date - b.Start_Date) AS Ban_Duration
        FROM INVESTIGATIONS i
        JOIN BANS b ON i.Investigation_ID = b.Investigation_ID
        WHERE i.Moderator_ID = p_moderator_id
          AND i.Status = 'Closed'
          AND EXTRACT(YEAR FROM i.Closed_Date) = p_year
          AND EXTRACT(MONTH FROM i.Closed_Date) = p_month;
BEGIN
    -- פתיחת הסמן
    OPEN cur_bans;
    
    -- לולאה למעבר על כל שורה בתוצאת הסמן
    LOOP
        FETCH cur_bans INTO ban_record;
        EXIT WHEN NOT FOUND;
        
        -- חישוב הבונוס: 10 שקלים/דולרים על כל יום חסימה שהמודרטור חילק (משקף את חומרת העבירה שהוא איתר)
        total_bonus := total_bonus + (ban_record.Ban_Duration * 10);
    END LOOP;
    
    -- סגירת הסמן
    CLOSE cur_bans;
    
    RETURN total_bonus;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------------------------------------
-- פונקציה 2: is_high_risk_player
-- תיאור: בודקת אם שחקן מסוים מוגדר כ"שחקן בסיכון גבוה".
-- לוגיקה: שחקן מוגדר בסיכון גבוה אם יש לו היסטוריה של 2 חסימות ומעלה, 
-- או שיש נגדו כרגע 3 דיווחים או יותר שטרם נסגרו (נמצאים בחקירה פתוחה או ממתינים).
-- --------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION is_high_risk_player(p_player_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    past_bans_count INT;
    active_reports_count INT;
BEGIN
    -- בדיקת כמות החסימות בעבר
    SELECT COUNT(*) INTO past_bans_count
    FROM BANS
    WHERE Banned_Player = p_player_name;
    
    -- בדיקת כמות הדיווחים התלויים ועומדים נגדו
    SELECT COUNT(*) INTO active_reports_count
    FROM REPORTS r
    JOIN INVESTIGATIONS i ON r.Report_ID = i.Report_ID
    WHERE r.Suspect_name = p_player_name
      AND i.Status IN ('In Progress', 'Pending');
      
    -- אם יש יותר מ-1 חסימה או יותר מ-2 דיווחים פתוחים, הוא בסיכון גבוה
    IF past_bans_count >= 2 OR active_reports_count >= 3 THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
