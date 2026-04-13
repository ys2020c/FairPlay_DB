import random
from datetime import datetime, timedelta

# הגדרות בסיסיות לסקריפט
NUM_RECORDS = 20000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 1, 1)

# פונקציית עזר להגרלת תאריך אקראי
def random_date(start, end):
    delta = end - start
    random_days = random.randrange(delta.days)
    return start + timedelta(days=random_days)

print("Starting to generate data, please wait...")

# יצירת הקובץ ופתיחתו לכתיבה
with open("insert_20k.sql", "w", encoding="utf-8") as file:
    file.write("-- קובץ יצירת 20,000 רשומות לטבלאות דיווחים וחקירות\n\n")
    
    # מילון לשמירת תאריכי הדיווח, כדי שנוכל לסנכרן אותם עם החקירות
    report_dates = {}

    # ---------------------------------------------------------
    # שלב 1: יצירת נתונים לטבלת הדיווחים (REPORTS)
    # ---------------------------------------------------------
    file.write("-- תחילת הכנסת נתונים: REPORTS\n")
    for i in range(1, NUM_RECORDS + 1):
        report_id = i
        reporter = f"Player_{random.randint(1, 10000)}"
        suspect = f"Player_{random.randint(10001, 20000)}"
        game_id = random.randint(100, 999)
        
        # הגרלת תאריך ושמירתו במילון
        rep_date = random_date(START_DATE, END_DATE)
        report_dates[report_id] = rep_date 
        rep_date_str = rep_date.strftime('%Y-%m-%d')
        
        # סיבות דיווח אקראיות
        desc = random.choice(["Aim bot suspected", "Verbal abuse in chat", "Wall hack", "Griefing team", "Spamming", "Exploiting map glitch"])
        
        file.write(f"INSERT INTO REPORTS (Report_ID, Reporter_name, Suspect_name, Game_ID, Report_Date, Description) VALUES ({report_id}, '{reporter}', '{suspect}', {game_id}, '{rep_date_str}', '{desc}');\n")

    # ---------------------------------------------------------
    # שלב 2: יצירת נתונים לטבלת החקירות (INVESTIGATIONS)
    # ---------------------------------------------------------
    file.write("\n-- תחילת הכנסת נתונים: INVESTIGATIONS\n")
    for i in range(1, NUM_RECORDS + 1):
        inv_id = i
        report_id = i 
        mod_id = random.randint(1, 500) # מניחים שקיימים 500 אנשי צוות שאת ה-ID שלהם נייצר בשלב הבא
        
        # לוגיקת תאריכים: החקירה נפתחת בין 0 ל-5 ימים אחרי הדיווח
        rep_date = report_dates[report_id]
        opened_date = rep_date + timedelta(days=random.randint(0, 5))
        opened_date_str = opened_date.strftime('%Y-%m-%d')
        
        # סטטוס חקירה (רוב הסיכויים שהיא כבר נסגרה)
        status = random.choice(["Closed", "Closed", "Closed", "In Progress"])
        
        if status == "Closed":
            closed_date = opened_date + timedelta(days=random.randint(1, 14))
            closed_date_str = f"'{closed_date.strftime('%Y-%m-%d')}'"
        else:
            closed_date_str = "NULL" # אין גרשיים סביב NULL ב-SQL
            
        file.write(f"INSERT INTO INVESTIGATIONS (Investigation_ID, Opened_Date, Closed_Date, Status, Moderator_ID, Report_ID) VALUES ({inv_id}, '{opened_date_str}', {closed_date_str}, '{status}', {mod_id}, {report_id});\n")

print("The process is complete! A file named 'insert_20k.sql' has been successfully created in the folder.")