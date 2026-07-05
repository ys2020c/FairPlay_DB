import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class LogicQueriesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FairPlay DB - מסך שאילתות ופונקציות (שלבים ב' ו-ד')")
        self.root.geometry("1100x700")
        
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        self.create_widgets()
        self.load_combo_data()

    def get_db_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר למסד הנתונים:\n{e}")
            return None

    def load_combo_data(self):
        """טעינת שמות פקחים ושחקנים כדי שהמשתמש לא יצטרך לנחש מספרי ID"""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            
            # טעינת פקחים (עבור פונקציית הבונוס)
            cur.execute("SELECT moderator_id, mname FROM moderators;")
            self.mod_map = {f"{name} (ID: {m_id})": m_id for m_id, name in cur.fetchall()}
            self.mod_combo['values'] = list(self.mod_map.keys())
            
            # טעינת שחקנים (עבור פונקציית רמת סיכון)
            cur.execute("SELECT username FROM player ORDER BY username;")
            self.player_combo['values'] = [row[0] for row in cur.fetchall()]
            
            cur.close()
        except Exception as e:
            print(f"Error loading combos: {e}")
        finally:
            conn.close()

    def create_widgets(self):
        # ==========================================
        # אזור עליון: הפעלת פונקציות (שלב ד')
        # ==========================================
        func_frame = tk.LabelFrame(self.root, text="פונקציות מסד נתונים (שלב ד')", padx=10, pady=10)
        func_frame.pack(fill="x", padx=10, pady=10)

        # פונקציה 1: חישוב בונוס
        tk.Label(func_frame, text="1. חישוב בונוס לפקח:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="e", pady=5)
        self.mod_combo = ttk.Combobox(func_frame, width=20, state="readonly")
        self.mod_combo.grid(row=0, column=1, padx=5)
        self.mod_combo.set("בחר פקח...")
        
        tk.Label(func_frame, text="שנה:").grid(row=0, column=2)
        self.year_var = tk.StringVar(value="2026") # ברירת מחדל
        tk.Entry(func_frame, textvariable=self.year_var, width=8).grid(row=0, column=3, padx=5)
        
        tk.Label(func_frame, text="חודש:").grid(row=0, column=4)
        self.month_var = tk.StringVar(value="6")
        tk.Entry(func_frame, textvariable=self.month_var, width=5).grid(row=0, column=5, padx=5)
        
        tk.Button(func_frame, text="חשב בונוס", command=self.run_bonus_func, bg="lightblue").grid(row=0, column=6, padx=10)

        # פונקציה 2: האם שחקן בסיכון?
        tk.Label(func_frame, text="2. בדיקת שחקן בסיכון:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="e", pady=15)
        self.player_combo = ttk.Combobox(func_frame, width=20, state="readonly")
        self.player_combo.grid(row=1, column=1, padx=5)
        self.player_combo.set("בחר שחקן...")
        
        tk.Button(func_frame, text="בדוק סטטוס", command=self.run_risk_func, bg="lightcoral").grid(row=1, column=2, columnspan=2, sticky="w", padx=10)

        # אזור תצוגת תוצאות של הפונקציות
        self.func_result_lbl = tk.Label(func_frame, text="התוצאה תופיע כאן", font=('Arial', 12, 'bold'), fg="blue")
        self.func_result_lbl.grid(row=2, column=0, columnspan=7, pady=10)

        # ==========================================
        # אזור אמצעי: הפעלת שאילתות מורכבות (שלב ב')
        # ==========================================
        queries_frame = tk.LabelFrame(self.root, text="שאילתות אנליטיות מורכבות (שלב ב')", padx=10, pady=10)
        queries_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(queries_frame, text="הצג: עומס פקחים (שאילתה 2A)", command=self.run_query_2a, height=2, bg="lightgreen").pack(side="left", padx=10, expand=True, fill="x")
        tk.Button(queries_frame, text="הצג: חקירות עם ראיות ללא חסימה (שאילתה 4A)", command=self.run_query_4a, height=2, bg="lightgreen").pack(side="left", padx=10, expand=True, fill="x")

        # ==========================================
        # אזור תחתון: טבלה (Treeview) לתצוגת התוצאות של השאילתות
        # ==========================================
        self.tree = ttk.Treeview(self.root, show="headings")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------------- הפעלת פונקציות שלב ד' ----------------

    def run_bonus_func(self):
        mod_key = self.mod_combo.get()
        if "ID:" not in mod_key:
            messagebox.showerror("שגיאה", "אנא בחר פקח מהרשימה")
            return
            
        mod_id = self.mod_map[mod_key]
        year = self.year_var.get()
        month = self.month_var.get()

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            # קריאה לפונקציית הפוסטגרס
            cur.execute("SELECT public.calculate_moderator_bonus(%s, %s, %s);", (mod_id, year, month))
            result = cur.fetchone()[0]
            
            # אם אין בונוס, הפונקציה עשויה להחזיר None או 0
            if result is None: result = 0.0
            
            self.func_result_lbl.config(text=f"הבונוס המחושב לפקח לחודש זה הוא: ₪{result}", fg="darkgreen")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאת פונקציה", str(e))
        finally:
            conn.close()

    def run_risk_func(self):
        player = self.player_combo.get()
        if player == "בחר שחקן...":
            messagebox.showerror("שגיאה", "אנא בחר שחקן")
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("SELECT public.is_high_risk_player(%s);", (player,))
            is_risk = cur.fetchone()[0]
            
            if is_risk:
                self.func_result_lbl.config(text=f"⚠️ אזהרה: השחקן '{player}' מוגדר בסיכון גבוה!", fg="red")
            else:
                self.func_result_lbl.config(text=f"✅ תקין: השחקן '{player}' אינו בסיכון גבוה.", fg="green")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאת פונקציה", str(e))
        finally:
            conn.close()

    # ---------------- הפעלת שאילתות שלב ב' ----------------

    def display_query_results(self, columns, rows):
        """פונקציית עזר לניקוי הטבלה והצגת תוצאות חדשות"""
        # מחיקת נתונים קודמים
        self.tree.delete(*self.tree.get_children())
        
        # הגדרת עמודות חדשות
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
            
        # הכנסת השורות
        for row in rows:
            self.tree.insert("", "end", values=row)

    def run_query_2a(self):
        query = """
        SELECT
          m.Moderator_ID AS "ID פקח",
          m.Mname AS "שם פקח",
          m.Role AS "תפקיד",
          COUNT(i.Investigation_ID) AS "חקירות פתוחות",
          MIN(i.Opened_Date) AS "התיק הישן ביותר"
        FROM MODERATORS m
        JOIN INVESTIGATIONS i ON i.Moderator_ID = m.Moderator_ID
        WHERE i.Status = 'In Progress'
        GROUP BY m.Moderator_ID, m.Mname, m.Role
        ORDER BY "חקירות פתוחות" DESC, "התיק הישן ביותר" ASC
        LIMIT 10;
        """
        self._execute_and_display(query, ["ID פקח", "שם פקח", "תפקיד", "חקירות פתוחות", "התיק הישן ביותר"])

    def run_query_4a(self):
        query = """
        SELECT
          i.Investigation_ID AS "ID חקירה",
          r.Suspect_name AS "שם החשוד",
          i.Status AS "סטטוס תיק",
          COUNT(e.Evidence_ID) AS "כמות ראיות",
          MAX(e.Evidence_Type) AS "סוג ראיה (דוגמה)"
        FROM INVESTIGATIONS i
        JOIN REPORTS r ON r.Report_ID = i.Report_ID
        JOIN EVIDENCE e ON e.Investigation_ID = i.Investigation_ID
        LEFT JOIN BANS b ON b.Investigation_ID = i.Investigation_ID
        WHERE b.Ban_ID IS NULL
        GROUP BY i.Investigation_ID, r.Report_ID, r.Suspect_name, i.Status
        ORDER BY "כמות ראיות" DESC, i.Investigation_ID
        LIMIT 20;
        """
        self._execute_and_display(query, ["ID חקירה", "שם החשוד", "סטטוס תיק", "כמות ראיות", "סוג ראיה (דוגמה)"])

    def _execute_and_display(self, query, columns):
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            self.display_query_results(columns, rows)
            
            if not rows:
                messagebox.showinfo("תוצאות", "השאילתה רצה בהצלחה אך לא נמצאו נתונים תואמים.")
                
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאת שאילתה", str(e))
        finally:
            conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = LogicQueriesGUI(root)
    root.mainloop()