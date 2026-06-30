# דוח פרויקט מסדי נתונים - שלב ב'
## Fair Play - מערכת אבטחה לאתר שחמט

בשלב ב' התמקדנו בתשאול מסד הנתונים ובהוספת שכבת בקרה נוספת למערכת. המערכת מתארת מחלקת אבטחה באתר שחמט: שחקנים מדווחים על חשד לרמאות או התנהגות לא תקינה, אנשי צוות פותחים חקירות, מצרפים ראיות, מטילים חסימות ומנהלים ערעורים.

---

## קבצי שלב ב'
| קובץ | תפקיד |
|---|---|
| `Queries.sql` | 8 שאילתות `SELECT`, מתוכן 4 כתובות בשתי דרכים, ועוד 3 שאילתות `UPDATE` ו-3 שאילתות `DELETE` |
| `Constraints.sql` | 3 אילוצים שנוספו בעזרת `ALTER TABLE` ודוגמאות להכנסה שגויה שאמורה להיכשל |
| `RollbackCommit.sql` | הדגמה של `ROLLBACK` והדגמה של `COMMIT` |
| `Index.sql` | 3 אינדקסים עם בדיקות `EXPLAIN ANALYZE` לפני ואחרי |
| `backup2_12_06_2026.backup` | קובץ גיבוי מעודכן לשלב ב' |

---

## שאילתות SELECT כפולות
**שאילתה 1 - כמות דיווחים לפי חודש**  
מוצגת בדשבורד המנהלים. השאילתה מפרקת את תאריך הדיווח לשנה וחודש, סופרת דיווחים וחקירות, ומציגה יחס בין חקירות לדיווחים. הגרסה הראשונה מבצעת join ו-group ישירות. הגרסה השנייה משתמשת ב-CTE שמכין את הנתונים לפני הסיכום. בדרך כלל הגרסה הישירה תהיה פשוטה יותר לאופטימיזציה, אבל ה-CTE נוח יותר לקריאה כאשר הלוגיקה גדלה.

**שאילתה 2 - עומס חקירות פתוחות לפי Moderator**  
מוצגת בדשבורד ניהול צוות. הגרסה הראשונה עושה join ואז group. הגרסה השנייה מסכמת קודם את טבלת החקירות ורק אחר כך מחברת את שמות אנשי הצוות. כאשר טבלת אנשי הצוות קטנה וטבלת החקירות גדולה, הגרסה השנייה יכולה להיות יעילה יותר כי היא מצמצמת נתונים לפני ה-join.

**שאילתה 3 - סיבות חסימה שמובילות להרבה ערעורים**  
מוצגת במסך ניהול ערעורים. הגרסה הראשונה משתמשת ב-joins וב-group by. הגרסה השנייה משתמשת בתתי שאילתות מקושרות. בדרך כלל גרסת ה-join עדיפה כי היא סורקת ומקבצת בצורה מרוכזת, בעוד שתתי שאילתות מקושרות עלולות לרוץ שוב עבור כל שורת סיבה.

**שאילתה 4 - חקירות עם ראיות אך ללא חסימה**  
מוצגת בחדר החקירות. הגרסה הראשונה משתמשת ב-`LEFT JOIN` עם בדיקת `IS NULL`. הגרסה השנייה משתמשת ב-`NOT EXISTS`. ב-PostgreSQL שתי הצורות יכולות לקבל תוכנית דומה, אבל `NOT EXISTS` מבטאת טוב יותר את הכוונה: למצוא חקירות שאין להן חסימה.

---

## שאילתות SELECT נוספות
**שאילתה 5 - תיק שחקן**  
מסכמת לשחקן חשוד את מספר הדיווחים, החקירות, החסימות והערעורים שלו. מתאימה למסך תיק שחקן.

**שאילתה 6 - משך חקירה ממוצע לפי תפקיד**  
מציגה כמה זמן בממוצע לוקח לסגור חקירה לפי סוג איש צוות. מתאימה לדשבורד מנהלים.

**שאילתה 7 - סוגי ראיות לפי חודש**  
מפרקת תאריכי פתיחת חקירות לשנה וחודש ומראה אילו סוגי ראיות נפוצים בכל תקופה. מתאימה למסך ניתוח חקירות.

**שאילתה 8 - חסימות אחרונות וסטטוס ערעור**  
מציגה חסימות, סיבה, תאריכים וסטטוס ערעור אם קיים. מתאימה למסך ניהול ערעורים.

---

## UPDATE ו-DELETE
שאילתות ה-`UPDATE` נועדו לתרחישים ניהוליים: שיוך מחדש של חקירות פתוחות ישנות, סגירת ערעורים ישנים והארכת חסימות כאשר קיימת ראיית מערכת. שאילתות ה-`DELETE` מנקות נתוני דמו: ערעורים על חסימות קצרות במיוחד, ראיות עם קישור לא תקין וחקירות יתומות שאינן מחוברות לדיווח, ראיה או חסימה.

לפני הרצה אמיתית של שאילתות שינוי, מומלץ להריץ אותן בתוך טרנזקציה ולבדוק את התוצאה לפני `COMMIT`.

---

## אילוצים
נוספו שלושה אילוצים:
- `chk_reports_reporter_not_suspect` - מונע מצב שבו שחקן מדווח על עצמו.
- `uq_investigations_report` - מוודא שלכל דיווח תהיה לכל היותר חקירה אחת.
- `chk_evidence_url_format` - מוודא שקישור לראיה נראה כמו URL.

בקובץ `Constraints.sql` יש לכל אילוץ גם ניסיון הכנסה שגוי שאמור להחזיר שגיאת הרצה. הדוגמאות עטופות ב-`BEGIN` ו-`ROLLBACK` כדי לא להשאיר נתוני בדיקה במסד.

---

## Rollback ו-Commit
בקובץ `RollbackCommit.sql` יש שתי הדגמות:
- עדכון החלטת ערעור, הצגת המצב אחרי העדכון, ואז `ROLLBACK` והצגה שהערך חזר לקדמותו.
- עדכון סטטוס חקירה, הצגת המצב אחרי העדכון, `COMMIT`, והצגה שהשינוי נשמר.

---

## אינדקסים
נוספו שלושה אינדקסים:
- `idx_reports_report_date` - משפר סינון דיווחים לפי תאריך.
- `idx_investigations_status_opened` - משפר איתור חקירות פתוחות לפי סטטוס ותאריך פתיחה.
- `idx_bans_reason_start` - משפר ניתוח חסימות לפי סיבה ותאריך התחלה.

בקובץ `Index.sql` מופיעות פקודות `EXPLAIN ANALYZE` לפני ואחרי יצירת כל אינדקס. במסד קטן ייתכן שהשיפור לא יהיה גדול, כי PostgreSQL לפעמים יעדיף סריקה מלאה. במסד גדול יותר, ובעיקר במסכים שמסננים לפי תאריכים וסטטוסים, האינדקסים צפויים לעזור יותר.

---

## צילומי מסך מהרצה בפועל

**שאילתות SELECT:**
![SELECT 1](./images/queries/Q1.png)
![SELECT 2](./images/queries/Q2.png)
![SELECT 3](./images/queries/Q3.png)
![SELECT 4](./images/queries/Q4.png)
![SELECT 5](./images/queries/Q5.png)
![SELECT 6](./images/queries/Q6.png)
![SELECT 7](./images/queries/Q7.png)
![SELECT 8](./images/queries/Q8.png)

**שאילתות UPDATE:**
![update 1 before](./images/update/beforeU1.png)
![update 1 after](./images/update/afterU1.png)
![update 2 before](./images/update/beforeU2.png)
![update 2 after](./images/update/afterU2.png)
![update 3 before](./images/update/beforeU3.png)
![update 3 after](./images/update/afterU3.png)

**שאילתות DELETE:**
![delete 1 before](./images/delete/beforeD1.png)
![delete 1 after](./images/delete/afterD1.png)
![delete 2 before](./images/delete/beforeD2.png)
![delete 2 after](./images/delete/afterD2.png)
![delete 3 before](./images/delete/beforeD3.png)
![delete 3 after](./images/delete/afterD3.png)

**אילוצים (Constraints):**
![constraint 1](./images/constraints/constraint1.png)
![constraint 2](./images/constraints/constraint2.png)
![constraint 3](./images/constraints/constraint3.png)

**Rollback ו-Commit:**
![rollback before](./images/RollbackAndCommit/beforeRollback.png)
![rollback during](./images/RollbackAndCommit/duringRollback.png)
![rollback after](./images/RollbackAndCommit/afterRollback.png)
![commit before](./images/RollbackAndCommit/beforeCommit.png)
![commit during](./images/RollbackAndCommit/duringCommit.png)
![commit after](./images/RollbackAndCommit/afterCommit.png)

**אינדקסים (Indexes):**
![index 1 before](./images/index/beforeIndex1.png)
![index 1 after](./images/index/afterIndex1.png)
![index 2 before](./images/index/beforeIndex2.png)
![index 2 after](./images/index/afterIndex2.png)
![index 3 before](./images/index/beforeIndex3.png)
![index 3 after](./images/index/afterIndex3.png)
