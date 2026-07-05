import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class FairPlayMainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("FairPlay Chess Security - לוח בקרה ראשי")
        self.root.geometry("950x650")
        
        # כותרת ראשית של המערכת
        title_lbl = tk.Label(self.root, text="מערכת אבטחה ואכיפה - FairPlay Chess", font=('Arial', 20, 'bold'), pady=15)
        title_lbl.pack()
        
        subtitle_lbl = tk.Label(self.root, text="לוח בקרה מרכזי לניהול הפלטפורמה", font=('Arial', 12, 'italic'), fg="gray")
        subtitle_lbl.pack(pady=(0, 20))

        # מיכל ראשי שמחזיק את כל הקטגוריות
        main_container = tk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # ---------------------------------------------------------
        # קטגוריה 1: ניהול משתמשים ואכיפה
        # ---------------------------------------------------------
        frame_users = tk.LabelFrame(main_container, text=" ניהול משתמשים, חסימות וערעורים ", font=('Arial', 11, 'bold'), padx=15, pady=15)
        frame_users.pack(fill="x", pady=10)
        
        self.create_dash_btn(frame_users, "ניהול שחקנים (player)", "player_gui.py").pack(side="left", padx=10, expand=True, fill="x")
        self.create_dash_btn(frame_users, "ניהול פקחים (moderators)", "moderators_gui.py").pack(side="left", padx=10, expand=True, fill="x")
        self.create_dash_btn(frame_users, "ניהול חסימות (bans)", "bans_gui.py").pack(side="left", padx=10, expand=True, fill="x")
        self.create_dash_btn(frame_users, "ערעורי שחקנים (appeals)", "appeals_gui.py").pack(side="left", padx=10, expand=True, fill="x")
        self.create_dash_btn(frame_users, "קטלוג סיבות חסימה", "ban_reasons_gui.py").pack(side="left", padx=10, expand=True, fill="x")

        # ---------------------------------------------------------
        # קטגוריה 2: חקירות, דיווחים וראיות
        # ---------------------------------------------------------
        frame_investigations = tk.LabelFrame(main_container, text=" חדר חקירות ודיווחים ", font=('Arial', 11, 'bold'), padx=15, pady=15)
        frame_investigations.pack(fill="x", pady=10)
        
        self.create_dash_btn(frame_investigations, "דיווחים על תקריות (reports)", "reports_gui.py").pack(side="left", padx=10, expand=True, fill="x")
        self.create_dash_btn(frame_investigations, "תיקי חקירה (investigations)", "investigations_gui.py").pack(side="left", padx=10, expand=True, fill="x")
        self.create_dash_btn(frame_investigations, "ניהול ראיות פורנזיות (evidence)", "evidence_gui.py").pack(side="left", padx=10, expand=True, fill="x")

        # ---------------------------------------------------------
        # קטגוריה 3: טורנירים, מועדונים ומשחקים
        # ---------------------------------------------------------
        frame_games = tk.LabelFrame(main_container, text=" ניהול ארגוני (משחקים, טורנירים ומועדונים) ", font=('Arial', 11, 'bold'), padx=15, pady=15)
        frame_games.pack(fill="x", pady=10)
        
        self.create_dash_btn(frame_games, "ניהול משחקים (game)", "game_gui.py").pack(side="left", padx=5, expand=True, fill="x")
        self.create_dash_btn(frame_games, "ניהול טורנירים (tournament)", "tournament_gui.py").pack(side="left", padx=5, expand=True, fill="x")
        self.create_dash_btn(frame_games, "הרשמות לטורניר", "registration_gui.py").pack(side="left", padx=5, expand=True, fill="x")
        self.create_dash_btn(frame_games, "מועדונים (club)", "club_gui.py").pack(side="left", padx=5, expand=True, fill="x")
        self.create_dash_btn(frame_games, "בקרות זמן (timecontrol)", "timecontrol_gui.py").pack(side="left", padx=5, expand=True, fill="x")
        self.create_dash_btn(frame_games, "סוגי משחק (gamevariant)", "gamevariant_gui.py").pack(side="left", padx=5, expand=True, fill="x")
        self.create_dash_btn(frame_games, "סיבובי טורניר (round)", "round_gui.py").pack(side="left", padx=5, expand=True, fill="x")

        # ---------------------------------------------------------
        # קטגוריה 4: אנליטיקה ולוגיקה מתקדמת (שלבים ב' ו-ד')
        # ---------------------------------------------------------
        frame_logic = tk.LabelFrame(main_container, text=" בינה עסקית, שאילתות ופונקציות (שלב ב' + ד') ", font=('Arial', 11, 'bold'), padx=15, pady=15)
        frame_logic.pack(fill="x", pady=10)
        
        btn_advanced = tk.Button(frame_logic, text="📊 פתח מסך שאילתות אנליטיות ופונקציות מורכבות 📊", 
                                  command=lambda: self.open_script("logic_queries_gui.py"), 
                                  font=('Arial', 11, 'bold'), bg="gold", fg="black", height=2)
        btn_advanced.pack(fill="x", padx=10)

        # שורת סטטוס תחתית
        status_lbl = tk.Label(self.root, text="כל הזכויות שמורות לפרויקט FairPlay_DB © 2026", font=('Arial', 9), fg="gray", pady=10)
        status_lbl.pack(side="bottom")

    def create_dash_btn(self, parent, text, script_name):
        """פונקציית עזר ליצירת כפתור מעוצב באופן אחיד במערכת"""
        btn = tk.Button(parent, text=text, 
                        command=lambda: self.open_script(script_name),
                        font=('Arial', 9, 'bold'), bg="#f0f0f0", height=2, wraplength=120)
        return btn

    def open_script(self, script_name):
        """מנגנון ריצה עצמאי לפתיחת תתי-המסכים ללא קריסת הממשק הראשי"""
        script_path = os.path.join(os.path.dirname(__file__), script_name)
        
        if not os.path.exists(script_path):
            messagebox.showerror("שגיאת קובץ", f"הקובץ {script_name} לא נמצא בתיקיית הריצה הנוכחית.")
            return
            
        try:
            # הפעלה כתהליך ברקע (עצמאי ובטוח)
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("שגיאת מערכת", f"לא ניתן לפתוח את המסך:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FairPlayMainMenu(root)
    root.mainloop()