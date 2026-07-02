# דוח הפרויקט - שלב ד' (תכנות ב-PL/pgSQL)

בשלב זה הוספנו לוגיקה תכנותית מתקדמת למסד הנתונים באמצעות שפת PL/pgSQL, בהתאם לדרישות הפרויקט. הוספנו 2 פונקציות, 2 פרוצדורות (שאחת מהן משתמשת ב-Exception), שני טריגרים (שאחד מהם פועל בזמן UPDATE) ושתי תוכניות ראשיות.

**עמידה בדרישות ושימוש באלמנטים תכנותיים (לציון מירבי):**
בכדי להעשיר את הפרויקט, שילבנו את האלמנטים הבאים בקוד שלנו:
* **Cursor (Explicit):** הוגדר בתוך פונקציית `calculate_moderator_bonus` (`CURSOR FOR`).
* **Cursor (Implicit):** שימוש נרחב בפקודות `SELECT INTO` בכל התוכניות.
* **פקודות DML:** שימוש מסיבי בפקודות `UPDATE` ו-`INSERT` בפרוצדורות ובטריגרים שלנו.
* **הסתעפויות (IF/ELSE):** שולבו בכל הפונקציות, הפרוצדורות והטריגרים לבדיקת תנאים שונים.
* **לולאות (LOOP):** שולבה לולאת `LOOP` שעוברת על תוצאות הסמן בפונקציה הראשונה.
* **Exception:** מימשנו בלוק `EXCEPTION` מותאם אישית שזורק שגיאה בפרוצדורה הראשונה וכן בטריגר של ה-UPDATE, ובלוק שתופס אותה (`WHEN OTHERS`) בתוכנית הראשית 2.
* **רשומות (Records):** שימוש במשתנה מטיפוס `RECORD` כדי לשמור את נתוני שורות הסמן (בפונקציה הראשונה).

*(הערה: לא ביצענו שינויים במבנה הטבלאות ולכן לא מצורף קובץ `AlterTable.sql`, מכיוון שהסכמה המורחבת שיצרנו בשלב ג' תמכה מראש בכל צרכי התכנות שלנו).*

---

פירוט התוכניות שנכתבו ותוצאות הריצה:

## 1. פונקציה 1 - `calculate_moderator_bonus`

**תיאור:** 
מחשבת את הבונוס הכספי של מודרטור בחודש מסוים. הפונקציה משתמשת בסמן מפורש (Explicit Cursor) שעובר בלולאה על כל החסימות (Bans) שהמודרטור הפיק בחודש זה. היא מכניסה כל שורה למשתנה מטיפוס `RECORD` ומחשבת את חומרת החסימה כנגזרת לבונוס הכספי.

**הקוד:**
```sql
CREATE OR REPLACE FUNCTION calculate_moderator_bonus(p_moderator_id INT, p_year INT, p_month INT)
RETURNS NUMERIC AS $$
DECLARE
    total_bonus NUMERIC := 0.0;
    ban_record RECORD;
    cur_bans CURSOR FOR 
        SELECT (b.End_Date - b.Start_Date) AS Ban_Duration
        FROM INVESTIGATIONS i
        JOIN BANS b ON i.Investigation_ID = b.Investigation_ID
        WHERE i.Moderator_ID = p_moderator_id
          AND i.Status = 'Closed'
          AND EXTRACT(YEAR FROM i.Closed_Date) = p_year
          AND EXTRACT(MONTH FROM i.Closed_Date) = p_month;
BEGIN
    OPEN cur_bans;
    LOOP
        FETCH cur_bans INTO ban_record;
        EXIT WHEN NOT FOUND;
        total_bonus := total_bonus + (ban_record.Ban_Duration * 10);
    END LOOP;
    CLOSE cur_bans;
    RETURN total_bonus;
END;
$$ LANGUAGE plpgsql;
```

**תוצאת ריצה:**
(תוצאת הריצה של פונקציה זו מוצגת במסגרת התוכנית הראשית 1 מטה)
![תוצאת ריצה - תוכנית ראשית 1](./main1_bonus.png)

---

## 2. פונקציה 2 - `is_high_risk_player`

**תיאור:** 
פונקציה בוליאנית הבודקת האם שחקן מסוים מוגדר כ"שחקן בסיכון גבוה". היא משתמשת בסמנים מרומזים (`SELECT INTO`) ובודקת (באמצעות הסתעפויות `IF`) האם יש לו היסטוריה של 2 חסימות ומעלה, או האם תלויים נגדו כעת 3 דיווחים פתוחים או יותר.

**הקוד:**
```sql
CREATE OR REPLACE FUNCTION is_high_risk_player(p_player_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    past_bans_count INT;
    active_reports_count INT;
BEGIN
    SELECT COUNT(*) INTO past_bans_count FROM BANS WHERE Banned_Player = p_player_name;
    
    SELECT COUNT(*) INTO active_reports_count
    FROM REPORTS r JOIN INVESTIGATIONS i ON r.Report_ID = i.Report_ID
    WHERE r.Suspect_name = p_player_name AND i.Status IN ('In Progress', 'Pending');
      
    IF past_bans_count >= 2 OR active_reports_count >= 3 THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

**תוצאת ריצה:**
*(קריאה לשחקן בסיכון גבוה שמחזירה TRUE, וקריאה לשחקן רגיל שמחזירה FALSE)*
![שחקן בסיכון גבוה](./is_high_risk_player.png)

---

## 3. פרוצדורה 1 - `extend_ban_for_repeat_offenders`

**תיאור:** 
הפרוצדורה מאריכה תוקף של חסימה (Ban) קיימת במספר ימים. היא עושה שימוש נרחב בהסתעפויות וזורקת חריגה (Exception) מסודרת אם החסימה לא קיימת או אם מספר הימים שלילי. במידה והכל תקין, מתבצעת פקודת DML (`UPDATE`). היא כוללת גם בלוק `EXCEPTION` פנימי לתפיסת שגיאות לא צפויות (WHEN OTHERS).

**הקוד:**
```sql
CREATE OR REPLACE PROCEDURE extend_ban_for_repeat_offenders(p_ban_id INT, p_extra_days INT)
LANGUAGE plpgsql AS $$
DECLARE
    v_ban_exists BOOLEAN;
BEGIN
    IF p_extra_days <= 0 THEN
        RAISE EXCEPTION 'Extra days for extension must be greater than zero. Received: %', p_extra_days;
    END IF;

    SELECT EXISTS (SELECT 1 FROM BANS WHERE Ban_ID = p_ban_id) INTO v_ban_exists;
    IF NOT v_ban_exists THEN
        RAISE EXCEPTION 'Ban ID % does not exist in the system!', p_ban_id;
    END IF;

    UPDATE BANS SET End_Date = End_Date + p_extra_days WHERE Ban_ID = p_ban_id;
    RAISE NOTICE 'Ban ID % was successfully extended by % days.', p_ban_id, p_extra_days;
EXCEPTION
    WHEN RAISE_EXCEPTION THEN
        RAISE NOTICE 'Error extending ban: %', SQLERRM;
    WHEN OTHERS THEN
        RAISE NOTICE 'An unexpected error occurred: %', SQLERRM;
END;
$$;
```

**תוצאת ריצה:**
(תוצאת זריקת השגיאה וקליטת ה-Exception מוצגת במסגרת התוכנית הראשית 2 מטה)
![תוצאת ריצה - תוכנית ראשית 2](./main2_exception.png)

---

## 4. פרוצדורה 2 - `close_investigation_and_notify`

**תיאור:** 
פרוצדורה שסוגרת חקירה קיימת בצורה מסודרת על ידי פקודות DML. היא בודקת אם החקירה לא קיימת או כבר סגורה, מעדכנת את תאריך הסיום והסטטוס ל-'Closed', ומוציאה פלט (Log) למסך שהחקירה נסגרה.

**הקוד:**
```sql
CREATE OR REPLACE PROCEDURE close_investigation_and_notify(p_investigation_id INT)
LANGUAGE plpgsql AS $$
DECLARE
    v_current_status VARCHAR;
BEGIN
    SELECT Status INTO v_current_status FROM INVESTIGATIONS WHERE Investigation_ID = p_investigation_id;

    IF v_current_status IS NULL THEN
        RAISE NOTICE 'Investigation ID % was not found.', p_investigation_id;
        RETURN;
    END IF;

    IF v_current_status = 'Closed' THEN
        RAISE NOTICE 'Investigation ID % is already closed!', p_investigation_id;
        RETURN;
    END IF;

    UPDATE INVESTIGATIONS SET Status = 'Closed', Closed_Date = CURRENT_DATE WHERE Investigation_ID = p_investigation_id;
    RAISE NOTICE '*** FairPlay System: Investigation ID % was successfully closed on % ***', p_investigation_id, CURRENT_DATE;
END;
$$;
```

**תוצאת ריצה:**
![סגירת חקירה](./close_investigation.png)

---

## 5. טריגר 1 (פעולת UPDATE) - `trg_prevent_ban_reduction`

**תיאור:** 
טריגר שמופעל לפני עריכה (`BEFORE UPDATE`) בטבלת החסימות. מטרתו היא אכיפת מדיניות: מניעה מאדמינים או מודרטורים לקצר במכוון עונשים ("צלילת תאריכים"). במידה ותאריך הסיום החדש (NEW) קטן מתאריך הסיום הישן (OLD), הטריגר מונע את פקודת העדכון וזורק `EXCEPTION`.

**הקוד:**
```sql
CREATE OR REPLACE FUNCTION prevent_ban_reduction_func()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.End_Date < OLD.End_Date THEN
        RAISE EXCEPTION 'System policy does not allow reducing the end date of an active ban (Ban_ID: %). Original date: %, Requested date: %', 
            NEW.Ban_ID, OLD.End_Date, NEW.End_Date;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_ban_reduction
BEFORE UPDATE ON BANS
FOR EACH ROW
EXECUTE FUNCTION prevent_ban_reduction_func();
```

**תוצאת ריצה:**
*(ניסיון לשנות תאריך סיום חסימה לאחור והשגיאה שנזרקה כתוצאה מכך)*
![מניעת קיצור עונש](./trigger1_prevent_reduction.png)

---

## 6. טריגר 2 (פעולת INSERT) - `trg_auto_assign_investigation`

**תיאור:** 
טריגר אוטומציה לניהול משימות המופעל אחרי הכנסת נתונים (`AFTER INSERT`) לטבלת הדיווחים (`REPORTS`). ברגע שמתקבל דיווח חדש ממשחק שחמט, הטריגר מחשב מיהו המודרטור הפנוי ביותר כרגע, פותח רשומת חקירה חדשה, ומקצה אותה אליו באופן אוטומטי (Load Balancing). 

**הקוד:**
```sql
CREATE OR REPLACE FUNCTION auto_assign_investigation_func()
RETURNS TRIGGER AS $$
DECLARE
    v_selected_moderator INT;
    v_new_investigation_id INT;
BEGIN
    SELECT m.Moderator_ID INTO v_selected_moderator FROM MODERATORS m
    LEFT JOIN INVESTIGATIONS i ON m.Moderator_ID = i.Moderator_ID AND i.Status = 'In Progress'
    GROUP BY m.Moderator_ID ORDER BY COUNT(i.Investigation_ID) ASC LIMIT 1;

    SELECT COALESCE(MAX(Investigation_ID), 0) + 1 INTO v_new_investigation_id FROM INVESTIGATIONS;

    INSERT INTO INVESTIGATIONS (Investigation_ID, Opened_Date, Closed_Date, Status, Moderator_ID, Report_ID)
    VALUES (v_new_investigation_id, CURRENT_DATE, NULL, 'In Progress', v_selected_moderator, NEW.Report_ID);

    RAISE NOTICE 'New report (%) received. A new investigation (%) was automatically opened and assigned to moderator %.', NEW.Report_ID, v_new_investigation_id, v_selected_moderator;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_assign_investigation
AFTER INSERT ON REPORTS
FOR EACH ROW
EXECUTE FUNCTION auto_assign_investigation_func();
```

**תוצאת ריצה:**
*(יצירת דיווח והודעת המערכת שחקירה נפתחה והוקצתה בהצלחה)*
![פתיחת חקירה אוטומטית](./trigger2_auto_assign.png)

---

## 7. תוכניות ראשיות (Main Programs)

שתי תוכניות `DO` המדגימות את הפעלת הפונקציות והפרוצדורות שנכתבו:

### תוכנית ראשית 1 - חישוב והדפסת בונוס למודרטור
**תיאור:** התוכנית מעבירה מזהה של מודרטור פעיל ואת החודש/שנה הרלוונטיים. קוראת לפונקציית `calculate_moderator_bonus`, שומרת את התוצאה במשתנה ומדפיסה (דרך הודעת NOTICE) את סכום הבונוס הכספי המגיע לאותו מודרטור.

**תוצאת ריצה:**
![בלוק ראשי 1](./main_program_1_bonus.png)

### תוכנית ראשית 2 - הדגמת אכיפה ותפיסת שגיאות מתקדמת
**תיאור:** התוכנית מנסה להפעיל את פרוצדורת `extend_ban_for_repeat_offenders` על מזהה חסימה פקטיבי כדי לדמות כשל מערכת. היא מדגימה כיצד בלוק ה-`EXCEPTION ... WHEN OTHERS` הפנימי תופס את שגיאת ה-`RAISE EXCEPTION` וממשיך את ריצת התוכנית באופן בטוח מבלי להקריס את ה-DB.

**תוצאת ריצה:**
![בלוק ראשי 2](./main_program_2_exception.png)
