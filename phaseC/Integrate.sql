-- ======================================================================================
-- Integrate.sql
-- שלב ג: מיזוג מסד הנתונים של פרויקט השחמט (שלב א') 
-- אל מסד הנתונים הקיים שלנו (FairPlay_DB - מערכת אכיפה).
-- ======================================================================================

-- 1. יצירת הטבלאות של המערכת השנייה (שחמט - שלב א')
-- ==========================================
-- טבלאות עזר (לצורך מפתחות זרים בלבד לשלב זה)
-- ==========================================
CREATE TABLE Player (
    player_id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL
);

CREATE TABLE Club (
    club_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- ==========================================
-- מחלקה 3: תחרויות ואירועים
-- ==========================================
CREATE TABLE Tournament (
    tournament_id INT PRIMARY KEY,
    club_id INT REFERENCES Club(club_id),
    name VARCHAR(100) NOT NULL,
    registration_open_date DATE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    -- אילוצים: סדר תאריכים הגיוני
    CONSTRAINT chk_tourney_reg CHECK (start_date >= registration_open_date),
    CONSTRAINT chk_tourney_dates CHECK (end_date >= start_date)
);

CREATE TABLE Registration (
    reg_id INT PRIMARY KEY,
    tournament_id INT REFERENCES Tournament(tournament_id),
    player_id INT REFERENCES Player(player_id),
    registered_date DATE NOT NULL,
    status VARCHAR(20)
);

CREATE TABLE Round (
    round_id INT PRIMARY KEY,
    tournament_id INT REFERENCES Tournament(tournament_id),
    round_number INT NOT NULL,
    scheduled_date DATE NOT NULL
);

-- ==========================================
-- מחלקה 2: משחקים
-- ==========================================
CREATE TABLE TimeControl (
    tc_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    base_seconds INT NOT NULL,
    increment_seconds INT NOT NULL
);

CREATE TABLE GameVariant (
    variant_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE Game (
    game_id INT PRIMARY KEY,
    white_player_id INT REFERENCES Player(player_id),
    black_player_id INT REFERENCES Player(player_id),
    tc_id INT REFERENCES TimeControl(tc_id),
    variant_id INT REFERENCES GameVariant(variant_id),
    round_id INT REFERENCES Round(round_id), -- הקשר לסבב בטורניר (אופציונלי למשחקי ידידות)
    result VARCHAR(10),
    start_date DATE NOT NULL,
    end_date DATE,
    -- אילוץ: תאריך סיום לא יכול להיות לפני תאריך התחלה
    CONSTRAINT chk_game_dates CHECK (end_date >= start_date)
);

-- ======================================================================================
-- 2. שילוב שתי המערכות (אינטגרציה) באמצעות ALTER TABLE על הנתונים הקיימים שלנו
-- ======================================================================================

-- עדכון הנתונים הקיימים כדי למנוע שגיאות Constraint בעת חיבור הדיווחים.
-- קודם נכניס נתוני דמו בסיסיים לטבלאות השחמט כדי שהחיבור יעבוד ויצוק נתונים למבטים:
INSERT INTO Player (player_id, username) VALUES (1, 'DemoWhite'), (2, 'DemoBlack') ON CONFLICT DO NOTHING;

INSERT INTO TimeControl (tc_id, name, base_seconds, increment_seconds) VALUES 
(1, 'Blitz', 180, 2), (2, 'Rapid', 600, 5), (3, 'Bullet', 60, 0), (4, 'Classical', 5400, 30) ON CONFLICT DO NOTHING;

INSERT INTO GameVariant (variant_id, name) VALUES 
(1, 'Standard'), (2, 'Chess960'), (3, 'Crazyhouse') ON CONFLICT DO NOTHING;

INSERT INTO Game (game_id, white_player_id, black_player_id, tc_id, variant_id, start_date, end_date, result) VALUES 
(1, 1, 2, 1, 1, DATE '2023-01-01', DATE '2023-01-01', '1-0'),
(2, 2, 1, 2, 1, DATE '2023-01-02', DATE '2023-01-02', '0-1'),
(3, 1, 2, 3, 2, DATE '2023-01-03', DATE '2023-01-03', '1/2-1/2'),
(4, 2, 1, 1, 1, DATE '2023-01-04', DATE '2023-01-04', '1-0'),
(5, 1, 2, 2, 3, DATE '2023-01-05', DATE '2023-01-05', '0-1')
ON CONFLICT (game_id) DO UPDATE SET tc_id=EXCLUDED.tc_id, variant_id=EXCLUDED.variant_id, result=EXCLUDED.result;

-- פיזור הדיווחים בין 5 המשחקים החדשים שיצרנו במקום שכולם ייפלו על משחק אחד
UPDATE REPORTS
SET Game_ID = (Report_ID % 5) + 1;

-- הוספת מפתח זר המקשר בין הדיווחים שלנו למשחקי השחמט
ALTER TABLE REPORTS
ADD CONSTRAINT FK_Report_Game 
FOREIGN KEY (Game_ID) REFERENCES Game(game_id);

-- ==========================================
-- הוספת מפתחות זרים לשחקנים (דיווחים וחסימות)
-- ==========================================

-- שלב א: אכלוס טבלת השחקנים (Player) מתוך השמות שכבר קיימים במערכת האכיפה 
-- כדי למנוע שגיאות של חוסר התאמה בזמן יצירת המפתחות הזרים.
INSERT INTO Player (player_id, username)
SELECT ROW_NUMBER() OVER (ORDER BY username) + 100, username
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
