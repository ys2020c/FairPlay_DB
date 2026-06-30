-- ======================================================================================
-- MainPrograms.sql
-- שלב ד: 2 תוכניות ראשיות (DO Blocks) לבדיקת הפונקציות והפרוצדורות שלנו
-- ======================================================================================

-- --------------------------------------------------------------------------------------
-- תוכנית ראשית 1: קריאה לפונקציית בונוסים של מודרטורים
-- תיאור: מריצה את פונקציית calculate_moderator_bonus ומדפיסה הודעה מסודרת עם התוצאה.
-- --------------------------------------------------------------------------------------
DO $$
DECLARE
    v_moderator_id INT := 2; -- מזהה של מודרטור לבדיקה
    v_year INT := 2023;
    v_month INT := 5;
    v_bonus_amount NUMERIC;
    v_mod_name VARCHAR;
BEGIN
    -- שליפת שם המודרטור כדי להדפיס הודעה יפה
    SELECT Mname INTO v_mod_name FROM MODERATORS WHERE Moderator_ID = v_moderator_id;

    -- קריאה לפונקציה ושמירת התוצאה למשתנה
    v_bonus_amount := calculate_moderator_bonus(v_moderator_id, v_year, v_month);
    
    -- הדפסת התוצאה למסך
    IF v_bonus_amount > 0 THEN
        RAISE NOTICE 'תוכנית 1: המודרטור % קיבל בונוס של % ש"ח עבור חודש %/%!', v_mod_name, v_bonus_amount, v_month, v_year;
    ELSE
        RAISE NOTICE 'תוכנית 1: למודרטור % אין בונוס בחודש %/% (לא סגר חקירות שהובילו לחסימות החודש).', v_mod_name, v_month, v_year;
    END IF;
END;
$$;


-- --------------------------------------------------------------------------------------
-- תוכנית ראשית 2: קריאה לפרוצדורה עם Exception Handling
-- תיאור: קוראת לפרוצדורה extend_ban_for_repeat_offenders ומדפיסה את התוצאה.
-- --------------------------------------------------------------------------------------
DO $$
DECLARE
    v_ban_id_to_extend INT := 999999; -- מספר חסימה שלא קיים בכוונה (כדי להדגים תפיסת שגיאות)
    v_extra_days INT := 14;
BEGIN
    RAISE NOTICE 'תוכנית 2: מנסים להאריך את תוקף החסימה מספר % ב-% ימים...', v_ban_id_to_extend, v_extra_days;
    
    -- קריאה לפרוצדורה (שתזרוק אקספשן כי ה-ID לא קיים)
    CALL extend_ban_for_repeat_offenders(v_ban_id_to_extend, v_extra_days);
    
    RAISE NOTICE 'הפעולה הסתיימה בהצלחה ללא שגיאות.';

EXCEPTION
    WHEN OTHERS THEN
        -- תפיסת האקספשן שנזרק מהפרוצדורה (או כל שגיאה אחרת)
        RAISE NOTICE 'תוכנית 2 תפסה שגיאה במהלך ההרצה: %', SQLERRM;
END;
$$;
