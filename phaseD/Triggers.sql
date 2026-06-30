-- ======================================================================================
-- Triggers.sql
-- שלב ד: יצירת שני טריגרים ב-PL/pgSQL
-- לפחות אחד מהטריגרים מופעל בעת עדכון (UPDATE)
-- ======================================================================================

-- --------------------------------------------------------------------------------------
-- טריגר 1: prevent_ban_reduction_func & trg_prevent_ban_reduction
-- סוג פעולה: UPDATE (לפני הפעולה - BEFORE)
-- תיאור: מונע ממשתמש במערכת או מודרטור לקצר עונש של שחקן על ידי שינוי End_Date לתאריך מוקדם יותר.
-- לוגיקה: בודק אם תאריך הסיום החדש קטן מתאריך הסיום הישן. אם כן, עוצר את העדכון וזורק שגיאה.
-- --------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION prevent_ban_reduction_func()
RETURNS TRIGGER AS $$
BEGIN
    -- בדיקה האם יש ניסיון לקצר את תאריך הסיום
    IF NEW.End_Date < OLD.End_Date THEN
        RAISE EXCEPTION 'מדיניות המערכת אינה מאפשרת קיצור של תאריך סיום חסימה פעילה (Ban_ID: %). התאריך המקורי: %, התאריך שהתבקש: %', 
            NEW.Ban_ID, OLD.End_Date, NEW.End_Date;
    END IF;
    
    -- אם הכל תקין, ממשיכים בפעולת העדכון
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_ban_reduction ON BANS;

CREATE TRIGGER trg_prevent_ban_reduction
BEFORE UPDATE ON BANS
FOR EACH ROW
EXECUTE FUNCTION prevent_ban_reduction_func();


-- --------------------------------------------------------------------------------------
-- טריגר 2: auto_assign_investigation_func & trg_auto_assign_investigation
-- סוג פעולה: INSERT (אחרי הפעולה - AFTER)
-- תיאור: ברגע שנפתח דיווח חדש (REPORT), הטריגר אוטומטית פותח חקירה חדשה בסטטוס 'In Progress'
-- ומקצה אותה למודרטור הכי פחות עמוס במערכת (זה שיש לו הכי פחות חקירות פעילות כרגע).
-- --------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auto_assign_investigation_func()
RETURNS TRIGGER AS $$
DECLARE
    v_selected_moderator INT;
    v_new_investigation_id INT;
BEGIN
    -- מציאת המודרטור הפנוי ביותר (למי יש הכי פחות חקירות בסטטוס In Progress)
    SELECT m.Moderator_ID INTO v_selected_moderator
    FROM MODERATORS m
    LEFT JOIN INVESTIGATIONS i ON m.Moderator_ID = i.Moderator_ID AND i.Status = 'In Progress'
    GROUP BY m.Moderator_ID
    ORDER BY COUNT(i.Investigation_ID) ASC
    LIMIT 1;

    -- יצירת מזהה חקירה חדש (נמצא את הערך המקסימלי ונוסיף 1)
    SELECT COALESCE(MAX(Investigation_ID), 0) + 1 INTO v_new_investigation_id FROM INVESTIGATIONS;

    -- יצירת החקירה החדשה והקצאתה למודרטור שנבחר
    INSERT INTO INVESTIGATIONS (Investigation_ID, Opened_Date, Closed_Date, Status, Moderator_ID, Report_ID)
    VALUES (
        v_new_investigation_id, 
        CURRENT_DATE, 
        NULL, 
        'In Progress', 
        v_selected_moderator, 
        NEW.Report_ID
    );

    RAISE NOTICE 'דיווח חדש (%) התקבל. חקירה חדשה (%) נפתחה אוטומטית והוקצתה למודרטור מספר %.', NEW.Report_ID, v_new_investigation_id, v_selected_moderator;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auto_assign_investigation ON REPORTS;

CREATE TRIGGER trg_auto_assign_investigation
AFTER INSERT ON REPORTS
FOR EACH ROW
EXECUTE FUNCTION auto_assign_investigation_func();
