-- ======================================================================================
-- Procedures.sql
-- שלב ד: יצירת שתי פרוצדורות (Stored Procedures) ב-PL/pgSQL
-- אחת הפרוצדורות משתמשת במנגנון EXCEPTION לטיפול בשגיאות.
-- ======================================================================================

-- --------------------------------------------------------------------------------------
-- פרוצדורה 1: extend_ban_for_repeat_offenders (כוללת EXCEPTION)
-- תיאור: מאריכה חסימה קיימת של שחקן (במספר ימים מסוים).
-- לוגיקה: בודקת אם החסימה קיימת. אם לא, זורקת שגיאה מתאימה. 
-- בודקת האם מספר הימים להארכה תקין (גדול מ-0). במידה ולא, זורקת שגיאה.
-- במקרה תקין, מעדכנת את תאריך הסיום של החסימה בטבלת BANS.
-- --------------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE extend_ban_for_repeat_offenders(p_ban_id INT, p_extra_days INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_ban_exists BOOLEAN;
BEGIN
    -- בדיקה 1: האם מספר הימים הגיוני (חיובי)
    IF p_extra_days <= 0 THEN
        RAISE EXCEPTION 'Extra days for extension must be greater than zero. Received: %', p_extra_days;
    END IF;

    -- בדיקה 2: האם החסימה בכלל קיימת במסד הנתונים
    SELECT EXISTS (SELECT 1 FROM BANS WHERE Ban_ID = p_ban_id) INTO v_ban_exists;
    IF NOT v_ban_exists THEN
        RAISE EXCEPTION 'Ban ID % does not exist in the system!', p_ban_id;
    END IF;

    -- אם הכל תקין, נבצע את ההארכה של תאריך הסיום
    UPDATE BANS
    SET End_Date = End_Date + p_extra_days
    WHERE Ban_ID = p_ban_id;
    
    RAISE NOTICE 'Ban ID % was successfully extended by % days.', p_ban_id, p_extra_days;

EXCEPTION
    -- תפיסת שגיאות והדפסת הודעה יפה למשתמש
    WHEN RAISE_EXCEPTION THEN
        RAISE NOTICE 'Error extending ban: %', SQLERRM;
    WHEN OTHERS THEN
        RAISE NOTICE 'An unexpected error occurred: %', SQLERRM;
END;
$$;

-- --------------------------------------------------------------------------------------
-- פרוצדורה 2: close_investigation_and_notify
-- תיאור: מבצעת סגירה מסודרת של חקירה פעילה.
-- לוגיקה: מעדכנת את הסטטוס ל-'Closed', מכניסה את התאריך של היום ל-Closed_Date,
-- ומדפיסה הודעה למערכת שהחקירה נסגרה.
-- --------------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE close_investigation_and_notify(p_investigation_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_status VARCHAR;
BEGIN
    -- קודם נוודא שהחקירה קיימת ושנמצאת במצב פתוח (In Progress)
    SELECT Status INTO v_current_status
    FROM INVESTIGATIONS
    WHERE Investigation_ID = p_investigation_id;

    IF v_current_status IS NULL THEN
        RAISE NOTICE 'Investigation ID % was not found.', p_investigation_id;
        RETURN;
    END IF;

    IF v_current_status = 'Closed' THEN
        RAISE NOTICE 'Investigation ID % is already closed!', p_investigation_id;
        RETURN;
    END IF;

    -- עדכון נתוני החקירה לסגירה
    UPDATE INVESTIGATIONS
    SET Status = 'Closed',
        Closed_Date = CURRENT_DATE
    WHERE Investigation_ID = p_investigation_id;

    -- הודעת מערכת (Log) שמסכמת את הפעולה
    RAISE NOTICE '*** FairPlay System: Investigation ID % was successfully closed on % ***', p_investigation_id, CURRENT_DATE;
END;
$$;
