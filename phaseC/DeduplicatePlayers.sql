-- תיקון נתונים פגומים משלב א' (כפילויות של שחקנים)
-- אנו נעדכן את כל הטבלאות שמפנות ל-Player להצביע תמיד על ה-ID הראשון של אותו שם משתמש,
-- ואז נמחוק את הכפילויות.

UPDATE Game 
SET white_player_id = (SELECT MIN(player_id) FROM Player p WHERE p.username = (SELECT username FROM Player WHERE player_id = Game.white_player_id));

UPDATE Game 
SET black_player_id = (SELECT MIN(player_id) FROM Player p WHERE p.username = (SELECT username FROM Player WHERE player_id = Game.black_player_id));

UPDATE Registration 
SET player_id = (SELECT MIN(player_id) FROM Player p WHERE p.username = (SELECT username FROM Player WHERE player_id = Registration.player_id));

-- עכשיו אפשר למחוק בבטחה את כל השחקנים הכפולים
DELETE FROM Player 
WHERE player_id NOT IN (SELECT MIN(player_id) FROM Player GROUP BY username);
