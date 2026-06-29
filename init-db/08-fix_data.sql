BEGIN;

-- 1. Fix Reports per Investigation Ratio
-- Insert 5000 new reports without any investigations
INSERT INTO REPORTS (Report_ID, Reporter_name, Suspect_name, Game_ID, Report_Date, Description)
SELECT Report_ID + 100000, 
       Reporter_name, 
       Suspect_name, 
       Game_ID + 10000, 
       Report_Date, 
       'Suspected engine use during the middle game.'
FROM REPORTS
WHERE MOD(Report_ID, 4) = 0;

-- 2. Fix Appeals per Ban Ratio
-- Delete random appeals to lower the ratio from 1.00 to something varied
DELETE FROM APPEALS
WHERE MOD(Appeal_ID, 3) != 0;

-- 3. Fix Evidence per Investigation Ratio
-- Duplicate evidence for 60% of investigations so the ratio is varied
INSERT INTO EVIDENCE (Evidence_ID, Evidence_Type, URL_Link, Investigation_ID)
SELECT Evidence_ID + 100000, 
       'Video', 
       'https://fairplay-chess.com/evidence/video_' || (Evidence_ID + 100000) || '.mp4', 
       Investigation_ID
FROM EVIDENCE
WHERE MOD(Investigation_ID, 5) < 3;

-- 4. Fix realistic texts for APPEALS
UPDATE APPEALS
SET Appeal_Text = CASE MOD(Appeal_ID, 10)
    WHEN 0 THEN 'I was just playing good moves, I never cheated! Please check my history.'
    WHEN 1 THEN 'My little brother was playing on my account, I swear it wont happen again.'
    WHEN 2 THEN 'I studied this opening line for hours, that is why I played so fast.'
    WHEN 3 THEN 'You banned me for no reason. I stream my games, you can watch the VOD.'
    WHEN 4 THEN 'I accidentally left my chess engine open in another tab, but I didn''t use it.'
    WHEN 5 THEN 'This is unfair. The opponent blundered their queen, anyone would spot that.'
    WHEN 6 THEN 'I admit I used an opening book, but only for the first 5 moves!'
    WHEN 7 THEN 'Please unban me, I promise to follow the fair play rules from now on.'
    WHEN 8 THEN 'I had a lucky game. Banning someone for one good game is ridiculous.'
    ELSE 'I am a titled player on another site, my rating here is just lower because I am new.'
END;

-- 5. Fix realistic texts for REPORTS
UPDATE REPORTS
SET Description = CASE MOD(Report_ID, 10)
    WHEN 0 THEN 'Opponent played perfect engine moves with 1 second delay every time.'
    WHEN 1 THEN 'Suspicious activity: they paused for 2 minutes and then mated me perfectly.'
    WHEN 2 THEN 'Player rating is 800 but they played like a Grandmaster.'
    WHEN 3 THEN 'They were insulting me in the chat and using offensive language.'
    WHEN 4 THEN 'Stalling the game! They let the clock run out instead of resigning.'
    WHEN 5 THEN 'Clear cheating. 99% accuracy in a 60 move game.'
    WHEN 6 THEN 'Using an opening explorer during a live rapid game.'
    WHEN 7 THEN 'The moves make no human sense, definitely using Stockfish.'
    WHEN 8 THEN 'Abusive chat behavior and inappropriate profile picture.'
    ELSE 'Suspicious rating climb: won 50 games in a row today.'
END;

-- 6. Randomize Statuses and Decisions
UPDATE APPEALS
SET Decision = CASE MOD(Appeal_ID, 3)
    WHEN 0 THEN 'Accepted'
    WHEN 1 THEN 'Denied'
    ELSE 'Pending'
END;

UPDATE INVESTIGATIONS
SET Status = CASE MOD(Investigation_ID, 4)
    WHEN 0 THEN 'In Progress'
    ELSE 'Closed'
END;

UPDATE INVESTIGATIONS
SET Closed_Date = NULL
WHERE Status = 'In Progress';

COMMIT;
