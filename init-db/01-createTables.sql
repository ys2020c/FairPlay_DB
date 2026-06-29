CREATE TABLE MODERATORS
(
  Moderator_ID INT NOT NULL,
  Mname VARCHAR(50) NOT NULL,
  Hire_Date DATE NULL,
  Role VARCHAR(50) NOT NULL,
  PRIMARY KEY (Moderator_ID),
  CHECK (Moderator_ID > 0),
  CHECK (Role IN ('Admin', 'Senior moderator', 'Moderator', 'Trial moderator'))
);

CREATE TABLE REPORTS
(
  Report_ID INT NOT NULL,
  Reporter_name VARCHAR(50) NOT NULL,
  Suspect_name VARCHAR(50) NOT NULL,
  Game_ID INT NOT NULL,
  Report_Date DATE NOT NULL,
  Description VARCHAR(500) NOT NULL,
  PRIMARY KEY (Report_ID),
  CHECK (Report_ID > 0),
  CHECK (Game_ID > 0)
);

CREATE TABLE INVESTIGATIONS
(
  Investigation_ID INT NOT NULL,
  Opened_Date DATE NOT NULL,
  Closed_Date DATE,
  Status VARCHAR(50) NOT NULL,
  Moderator_ID INT NOT NULL,
  Report_ID INT,
  PRIMARY KEY (Investigation_ID),
  CHECK (Investigation_ID > 0),
  CHECK (Status IN ('Closed', 'In Progress')),
  CHECK (Closed_Date IS NULL OR Closed_Date >= Opened_Date),
  FOREIGN KEY (Moderator_ID) REFERENCES MODERATORS(Moderator_ID),
  FOREIGN KEY (Report_ID) REFERENCES REPORTS(Report_ID)
);

CREATE TABLE EVIDENCE
(
  Evidence_ID INT NOT NULL,
  Evidence_Type VARCHAR(50) NOT NULL,
  URL_Link VARCHAR(2000) NOT NULL,
  Investigation_ID INT NOT NULL,
  PRIMARY KEY (Evidence_ID, Investigation_ID),
  CHECK (Evidence_ID > 0),
  CHECK (Evidence_Type IN ('Screenshot', 'Video', 'Chat Log', 'System Log')),
  FOREIGN KEY (Investigation_ID) REFERENCES INVESTIGATIONS(Investigation_ID)
);

CREATE TABLE BAN_REASONS
(
  Reason_ID INT NOT NULL,
  BR_Description VARCHAR(255) NOT NULL,
  PRIMARY KEY (Reason_ID),
  CHECK (Reason_ID > 0)
);

CREATE TABLE BANS
(
  Ban_ID INT NOT NULL,
  Banned_Player VARCHAR(50) NOT NULL,
  Start_Date DATE NOT NULL,
  End_Date DATE NOT NULL,
  Investigation_ID INT NOT NULL,
  Reason_ID INT NOT NULL,
  PRIMARY KEY (Ban_ID),
  CHECK (Ban_ID > 0),
  CHECK (End_Date >= Start_Date),
  FOREIGN KEY (Investigation_ID) REFERENCES INVESTIGATIONS(Investigation_ID),
  FOREIGN KEY (Reason_ID) REFERENCES BAN_REASONS(Reason_ID)
);

CREATE TABLE APPEALS
(
  Appeal_ID INT NOT NULL,
  Appeal_Text VARCHAR(1000) NOT NULL,
  Submission_Date DATE NOT NULL,
  Decision VARCHAR(50),
  Moderator_ID INT,
  Ban_ID INT NOT NULL,
  PRIMARY KEY (Appeal_ID),
  CHECK (Appeal_ID > 0),
  CHECK (Decision IS NULL OR Decision IN ('Accepted', 'Denied', 'Pending')),
  FOREIGN KEY (Moderator_ID) REFERENCES MODERATORS(Moderator_ID),
  FOREIGN KEY (Ban_ID) REFERENCES BANS(Ban_ID)
);
