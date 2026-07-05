import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class ReportsCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול דיווחים - FairPlay DB")
        self.root.geometry("1100x650")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234",
            "host": "localhost",
            "port": "5432"
        }

        # רשימות ומילונים למפתחות זרים
        self.players_list = []
        self.game_map = {}         # מתרגם טקסט -> game_id
        self.game_reverse_map = {} # מתרגם game_id -> טקסט קריא

        self.create_widgets()
        self.load_fk_data()
        self.fetch_data()

    def get_db_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר למסד הנתונים:\n{e}")
            return None

    def load_fk_data(self):
        """טעינת נתוני שחקנים ומשחקים ליצירת תפריטים ברורים"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            
            # 1. טעינת שמות שחקנים
            cur.execute("SELECT username FROM player ORDER BY username;")
            self.players_list = [row[0] for row in cur.fetchall()]
            
            # 2. טעינת משחקים עם שמות השחקנים בעזרת JOIN חכם
            query = """
                SELECT g.game_id, pw.username, pb.username 
                FROM game g
                LEFT JOIN player pw ON g.white_player_id = pw.player_id
                LEFT JOIN player pb ON g.black_player_id = pb.player_id
                ORDER BY g.game_id;
            """
            cur.execute(query)
            for g_id, w_name, b_name in cur.fetchall():
                w_disp = w_name if w_name else "לא ידוע"
                b_disp = b_name if b_name else "לא ידוע"
                display_str = f"משחק {g_id}: {w_disp} נגד {b_disp}"
                
                self.game_map[display_str] = g_id
                self.game_reverse_map[g_id] = display_str
                
            cur.close()
            
            # אכלוס התפריטים הנפתחים במסך
            self.reporter_combo['values'] = self.players_list
            self.suspect_combo['values'] = self.players_list
            self.game_combo['values'] = list(self.game_map.keys())

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מפתחות זרים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי דיווח", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID ותאריך
        tk.Label(form_frame, text="מספר דיווח (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="תאריך דיווח (YYYY-MM-DD):").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.date_var, width=20).grid(row=0, column=4, sticky="w")

        # שורה 1: מדווח וחשוד
        tk.Label(form_frame, text="שם המדווח:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.reporter_var = tk.StringVar()
        self.reporter_combo = ttk.Combobox(form_frame, textvariable=self.reporter_var, width=25, state="readonly")
        self.reporter_combo.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="שם החשוד:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.suspect_var = tk.StringVar()
        self.suspect_combo = ttk.Combobox(form_frame, textvariable=self.suspect_var, width=25, state="readonly")
        self.suspect_combo.grid(row=1, column=4, sticky="w")

        # שורה 2: משחק
        tk.Label(form_frame, text="משחק מקושר:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.game_var = tk.StringVar()
        self.game_combo = ttk.Combobox(form_frame, textvariable=self.game_var, width=45, state="readonly")
        self.game_combo.grid(row=2, column=1, columnspan=4, sticky="w")

        # שורה 3: תיאור
        tk.Label(form_frame, text="תיאור התקרית:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.desc_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.desc_var, width=70).grid(row=3, column=1, columnspan=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף דיווח", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן דיווח", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק דיווח", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה לתצוגת הנתונים
        cols = ("id", "date", "reporter", "suspect", "game", "desc")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50)
        self.tree.heading("date", text="תאריך")
        self.tree.column("date", width=100)
        self.tree.heading("reporter", text="מדווח")
        self.tree.column("reporter", width=120)
        self.tree.heading("suspect", text="חשוד")
        self.tree.column("suspect", width=120)
        self.tree.heading("game", text="משחק מקושר")
        self.tree.column("game", width=250)
        self.tree.heading("desc", text="תיאור")
        self.tree.column("desc", width=300)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT report_id, report_date, reporter_name, suspect_name, game_id, description FROM reports ORDER BY report_id;")
            for row in cur.fetchall():
                r_id, r_date, reporter, suspect, g_id, desc = row
                
                # תרגום ID של משחק לטקסט קריא
                game_disp = self.game_reverse_map.get(g_id, f"משחק #{g_id}")
                
                self.tree.insert("", "end", values=(r_id, r_date, reporter, suspect, game_disp, desc))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        r_id = self.id_var.get()
        if not r_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT report_date, reporter_name, suspect_name, game_id, description FROM reports WHERE report_id = %s;", (r_id,))
            row = cur.fetchone()
            if row:
                self.date_var.set(row[0])
                self.reporter_var.set(row[1])
                self.suspect_var.set(row[2])
                self.game_var.set(self.game_reverse_map.get(row[3], ""))
                self.desc_var.set(row[4])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "דיווח לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_logic(self, reporter, suspect, date_str):
        if not reporter or not suspect:
            messagebox.showerror("שגיאה", "חובה לבחור מדווח וחשוד.")
            return False
            
        if reporter == suspect:
            messagebox.showerror("שגיאה לוגית", "שחקן לא יכול לדווח על עצמו!")
            return False
            
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            messagebox.showerror("שגיאת תאריך", "פורמט תאריך לא תקין. יש להזין YYYY-MM-DD")
            return False

    def insert_record(self):
        reporter = self.reporter_var.get()
        suspect = self.suspect_var.get()
        date_str = self.date_var.get()
        
        if not self.validate_logic(reporter, suspect, date_str): return

        # חילוץ ה-ID של המשחק מתוך התפריט הנפתח
        g_id = self.game_map.get(self.game_var.get())
        if not g_id:
            messagebox.showerror("שגיאה", "חובה לבחור משחק מקושר חוקי.")
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO reports (report_id, reporter_name, suspect_name, game_id, report_date, description) VALUES (%s, %s, %s, %s, %s, %s);"
            values = (self.id_var.get(), reporter, suspect, g_id, date_str, self.desc_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הדיווח נוסף בהצלחה! הופעל טריגר אוטומטי לפתיחת חקירה.")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        reporter = self.reporter_var.get()
        suspect = self.suspect_var.get()
        date_str = self.date_var.get()
        
        if not self.validate_logic(reporter, suspect, date_str): return

        g_id = self.game_map.get(self.game_var.get())
        if not g_id:
            messagebox.showerror("שגיאה", "חובה לבחור משחק מקושר חוקי.")
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE reports SET reporter_name=%s, suspect_name=%s, game_id=%s, report_date=%s, description=%s WHERE report_id=%s;"
            values = (reporter, suspect, g_id, date_str, self.desc_var.get(), self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הדיווח עודכן בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק דיווח זה? (ייתכן ויש חקירות המקושרות אליו)"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM reports WHERE report_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הדיווח נמחק בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"לא ניתן למחוק את הדיווח:\n{e}")
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        vals = self.tree.item(selected, 'values')
        
        self.id_var.set(vals[0])
        self.date_var.set(vals[1])
        self.reporter_var.set(vals[2])
        self.suspect_var.set(vals[3])
        self.game_var.set(vals[4])
        self.desc_var.set(vals[5])

    def clear_form(self):
        self.id_var.set("")
        self.date_var.set("")
        self.reporter_var.set("")
        self.suspect_var.set("")
        self.game_var.set("")
        self.desc_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReportsCRUD(root)
    root.mainloop()