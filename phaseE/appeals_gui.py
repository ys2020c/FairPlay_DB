import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class AppealsCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול ערעורים - FairPlay DB")
        self.root.geometry("1100x650")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילוני תרגום למפתחות זרים ולוגיקה
        self.ban_map, self.ban_reverse_map = {}, {}
        self.mod_map, self.mod_reverse_map = {}, {}
        self.ban_dates = {} # מילון חדש לשמירת תאריכי תחילת החסימות!

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
        """טעינת נתוני חסימות ופקחים לתפריטים נפתחים"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            
            # 1. טעינת חסימות (שמירת תאריך ההתחלה לצורך ולידציה)
            cur.execute("SELECT ban_id, banned_player, start_date FROM bans;")
            for b_id, player, s_date in cur.fetchall():
                display_str = f"חסימה #{b_id}: {player} ({s_date})"
                self.ban_map[display_str] = b_id
                self.ban_reverse_map[b_id] = display_str
                # שמירת התאריך כדי למנוע ערעור מוקדם מדי
                self.ban_dates[b_id] = s_date
                
            # 2. טעינת פקחים
            cur.execute("SELECT moderator_id, mname FROM moderators;")
            for m_id, name in cur.fetchall():
                self.mod_map[name] = m_id
                self.mod_reverse_map[m_id] = name
                
            cur.close()
            
            # אכלוס התפריטים
            self.ban_combo['values'] = list(self.ban_map.keys())
            self.mod_combo['values'] = list(self.mod_map.keys())

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מפתחות זרים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי ערעור", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID והחלטה
        tk.Label(form_frame, text="מספר ערעור (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="החלטה (Decision):").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.decision_var = tk.StringVar()
        self.decision_combo = ttk.Combobox(form_frame, textvariable=self.decision_var, width=20, state="readonly")
        self.decision_combo['values'] = ['', 'Pending', 'Accepted', 'Denied']
        self.decision_combo.grid(row=0, column=4, sticky="w")

        # שורה 1: חסימה ופקח מטפל
        tk.Label(form_frame, text="חסימה מקושרת:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ban_var = tk.StringVar()
        self.ban_combo = ttk.Combobox(form_frame, textvariable=self.ban_var, width=40, state="readonly")
        self.ban_combo.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="פקח מטפל:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.mod_var = tk.StringVar()
        self.mod_combo = ttk.Combobox(form_frame, textvariable=self.mod_var, width=20, state="readonly")
        self.mod_combo.grid(row=1, column=4, sticky="w")

        # שורה 2: תאריך וטקסט
        tk.Label(form_frame, text="תאריך הגשה (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.date_var, width=15).grid(row=2, column=1, sticky="w")

        tk.Label(form_frame, text="תוכן הערעור:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.text_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.text_var, width=80).grid(row=3, column=1, columnspan=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף ערעור", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן ערעור", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק ערעור", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "ban", "date", "decision", "moderator", "text")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50)
        self.tree.heading("ban", text="חסימה מקושרת")
        self.tree.column("ban", width=250)
        self.tree.heading("date", text="תאריך")
        self.tree.column("date", width=100)
        self.tree.heading("decision", text="החלטה")
        self.tree.column("decision", width=100)
        self.tree.heading("moderator", text="פקח")
        self.tree.column("moderator", width=120)
        self.tree.heading("text", text="תוכן הערעור")
        self.tree.column("text", width=350)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT appeal_id, ban_id, submission_date, decision, moderator_id, appeal_text FROM appeals ORDER BY appeal_id;")
            for row in cur.fetchall():
                a_id, b_id, s_date, decision, m_id, a_text = row
                
                # תרגום חכם לטקסט קריא
                ban_disp = self.ban_reverse_map.get(b_id, f"חסימה #{b_id}")
                mod_disp = self.mod_reverse_map.get(m_id, "") if m_id else ""
                
                self.tree.insert("", "end", values=(a_id, ban_disp, s_date, decision if decision else "", mod_disp, a_text))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        a_id = self.id_var.get()
        if not a_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT ban_id, submission_date, decision, moderator_id, appeal_text FROM appeals WHERE appeal_id = %s;", (a_id,))
            row = cur.fetchone()
            if row:
                self.ban_var.set(self.ban_reverse_map.get(row[0], ""))
                self.date_var.set(row[1])
                self.decision_var.set(row[2] if row[2] else "")
                self.mod_var.set(self.mod_reverse_map.get(row[3], "") if row[3] else "")
                self.text_var.set(row[4])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "ערעור לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_logic(self, b_id, date_str, text):
        if not b_id:
            messagebox.showerror("שגיאה", "חובה לבחור חסימה אליה משויך הערעור.")
            return False
        if not text or len(text.strip()) == 0:
            messagebox.showerror("שגיאה", "חובה להזין תוכן לערעור.")
            return False
            
        try:
            sub_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # הלוגיקה החדשה: מניעת ערעור של נוסע בזמן!
            if b_id in self.ban_dates:
                ban_start_date = self.ban_dates[b_id]
                if sub_date < ban_start_date:
                    messagebox.showerror("שגיאה לוגית", f"אי אפשר לערער על חסימה שטרם התחילה!\nתאריך התחלת החסימה: {ban_start_date}")
                    return False
                    
            return True
        except ValueError:
            messagebox.showerror("שגיאת תאריך", "פורמט תאריך לא תקין. יש להזין YYYY-MM-DD")
            return False

    def insert_record(self):
        b_id = self.ban_map.get(self.ban_var.get())
        date_str = self.date_var.get()
        text = self.text_var.get()
        
        if not self.validate_logic(b_id, date_str, text): return

        decision = self.decision_var.get() if self.decision_var.get() != '' else None
        m_id = self.mod_map.get(self.mod_var.get()) if self.mod_var.get() != '' else None

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO appeals (appeal_id, appeal_text, submission_date, decision, moderator_id, ban_id) VALUES (%s, %s, %s, %s, %s, %s);"
            values = (self.id_var.get(), text, date_str, decision, m_id, b_id)
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הערעור נוסף בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        b_id = self.ban_map.get(self.ban_var.get())
        date_str = self.date_var.get()
        text = self.text_var.get()
        
        if not self.validate_logic(b_id, date_str, text): return

        decision = self.decision_var.get() if self.decision_var.get() != '' else None
        m_id = self.mod_map.get(self.mod_var.get()) if self.mod_var.get() != '' else None

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE appeals SET appeal_text=%s, submission_date=%s, decision=%s, moderator_id=%s, ban_id=%s WHERE appeal_id=%s;"
            values = (text, date_str, decision, m_id, b_id, self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הערעור עודכן בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק ערעור זה?"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM appeals WHERE appeal_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הערעור נמחק בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        vals = self.tree.item(selected, 'values')
        
        self.id_var.set(vals[0])
        self.ban_var.set(vals[1])
        self.date_var.set(vals[2])
        self.decision_var.set(vals[3] if vals[3] != 'None' else '')
        self.mod_var.set(vals[4] if vals[4] != 'None' else '')
        self.text_var.set(vals[5])

    def clear_form(self):
        self.id_var.set("")
        self.ban_var.set("")
        self.date_var.set("")
        self.decision_var.set("")
        self.mod_var.set("")
        self.text_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppealsCRUD(root)
    root.mainloop()