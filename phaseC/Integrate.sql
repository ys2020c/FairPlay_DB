-- ======================================================================================
-- Integrate.sql
-- שלב ג: מיזוג מסד הנתונים של פרויקט השחמט (שלב א') 
-- אל מסד הנתונים הקיים שלנו (FairPlay_DB - מערכת אכיפה).
-- הערה חשובה: יש להריץ קובץ זה **לאחר** הרצת קובץ יצירת הטבלאות וייבוא הנתונים (insertTables.sql).
-- מכיוון שיש שם עשרות אלפי רשומות, אנחנו קודם מריצים את הסקריפט משלב א' שלהם (create + insert)
-- ורק אז את הסקריפט שלנו שמחבר את המערכות.
-- ======================================================================================

-- עדכון הנתונים הקיימים כדי למנוע שגיאות Constraint בעת חיבור הדיווחים.
-- בשלב זה אנו מניחים שקובץ insertTables.sql שמכיל עשרות אלפי רשומות הורץ.
-- פיזור הדיווחים בין המשחקים החדשים האמיתיים שיצרנו. 
-- נשתמש במספר מודולו 100,000 (כי יש 100 אלף משחקים) ועוד 1 כדי שזה יפול על מזהה משחק קיים
UPDATE REPORTS
SET Game_ID = (Report_ID % (SELECT COUNT(*) FROM Game)) + 1;

-- הוספת מפתח זר המקשר בין הדיווחים שלנו למשחקי השחמט האמיתיים
ALTER TABLE REPORTS
ADD CONSTRAINT FK_Report_Game 
FOREIGN KEY (Game_ID) REFERENCES Game(game_id);

-- ==========================================
-- הוספת מפתחות זרים לשחקנים (דיווחים וחסימות)
-- ==========================================

-- שלב א: אכלוס טבלת השחקנים (Player) מתוך השמות שכבר קיימים במערכת האכיפה (שלא היו ב-100 אלף השחקנים משחמט)
-- כדי למנוע שגיאות של חוסר התאמה בזמן יצירת המפתחות הזרים. אנו נותנים להם ID החל מ-1,000,000.
INSERT INTO Player (player_id, username)
SELECT ROW_NUMBER() OVER (ORDER BY username) + 1000000, username
FROM (
  SELECT Reporter_name AS username FROM REPORTS
  UNION
  SELECT Suspect_name FROM REPORTS
  UNION
  SELECT Banned_Player FROM BANS
) AS existing_users
ON CONFLICT DO NOTHING;

-- שלב ב: הגדרת אילוץ יוניק על שם המשתמש בטבלת השחקנים (כדי שנוכל לקשר אליו מפתחות זרים טקסטואליים)
ALTER TABLE Player ADD CONSTRAINT UQ_Player_Username UNIQUE (username);

-- שלב ג: הוספת מפתחות זרים שמקשרים כל דיווח וכל חסימה לשחקן רשום
ALTER TABLE REPORTS ADD CONSTRAINT FK_Report_Reporter FOREIGN KEY (Reporter_name) REFERENCES Player(username);
ALTER TABLE REPORTS ADD CONSTRAINT FK_Report_Suspect FOREIGN KEY (Suspect_name) REFERENCES Player(username);
ALTER TABLE BANS ADD CONSTRAINT FK_Bans_Player FOREIGN KEY (Banned_Player) REFERENCES Player(username);
