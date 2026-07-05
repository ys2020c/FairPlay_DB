import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class InvestigationsCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול תיקי חקירה - FairPlay DB")
        self.root.geometry("1100x650")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילוני תרגום למפתחות זרים
        self.mod_map, self.mod_reverse_map = {}, {}
        self.report_map, self.report_reverse_map = {}, {}

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
        """טעינת פקחים ודיווחים לתפריטים נפתחים"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            
            # 1. טעינת פקחים
            cur.execute("SELECT moderator_id, mname FROM moderators;")
            for m_id, name in cur.fetchall():
                self.mod_map[name] = m_id
                self.mod_reverse_map[m_id] = name
                
            # 2. טעינת דיווחים
            cur.execute("SELECT report_id, reporter_name, suspect_name FROM reports;")
            for r_id, reporter, suspect in cur.fetchall():
                display_str = f"דיווח #{r_id}: {reporter} התלונן על {suspect}"
                self.report_map[display_str] = r_id
                self.report_reverse_map[r_id] = display_str
                
            cur.close()
            
            self.mod_combo['values'] = list(self.mod_map.keys())
            reports_list = [''] + list(self.report_map.keys())
            self.report_combo['values'] = reports_list

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מפתחות זרים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי תיק חקירה", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID וסטטוס
        tk.Label(form_frame, text="מספר חקירה (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="סטטוס חקירה:").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(form_frame, textvariable=self.status_var, width=20, state="readonly")
        self.status_combo['values'] = ['In Progress', 'Closed']
        self.status_combo.grid(row=0, column=4, sticky="w")

        # שורה 1: פקח ודיווח מקושר
        tk.Label(form_frame, text="פקח חוקר:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.mod_var = tk.StringVar()
        self.mod_combo = ttk.Combobox(form_frame, textvariable=self.mod_var, width=25, state="readonly")
        self.mod_combo.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="דיווח מקושר (אופציונלי):").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.report_var = tk.StringVar()
        self.report_combo = ttk.Combobox(form_frame, textvariable=self.report_var, width=40, state="readonly")
        self.report_combo.grid(row=1, column=4, sticky="w")

        # שורה 2: תאריכים
        tk.Label(form_frame, text="תאריך פתיחה (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.open_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.open_var, width=15).grid(row=2, column=1, sticky="w")

        tk.Label(form_frame, text="תאריך סגירה (YYYY-MM-DD):").grid(row=2, column=3, padx=5, pady=5, sticky="e")
        self.close_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.close_var, width=15).grid(row=2, column=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף חקירה", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן חקירה", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק חקירה", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "status", "opened", "closed", "moderator", "report")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50)
        self.tree.heading("status", text="סטטוס")
        self.tree.column("status", width=100)
        self.tree.heading("opened", text="נפתחה ב-")
        self.tree.column("opened", width=100)
        self.tree.heading("closed", text="נסגרה ב-")
        self.tree.column("closed", width=100)
        self.tree.heading("moderator", text="פקח")
        self.tree.column("moderator", width=150)
        self.tree.heading("report", text="דיווח מקושר")
        self.tree.column("report", width=350)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT investigation_id, status, opened_date, closed_date, moderator_id, report_id FROM investigations ORDER BY investigation_id;")
            for row in cur.fetchall():
                i_id, status, o_date, c_date, m_id, r_id = row
                mod_disp = self.mod_reverse_map.get(m_id, "")
                report_disp = self.report_reverse_map.get(r_id, "חקירה יזומה (ללא דיווח)") if r_id else "חקירה יזומה (ללא דיווח)"
                self.tree.insert("", "end", values=(i_id, status, o_date, c_date if c_date else "", mod_disp, report_disp))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        i_id = self.id_var.get()
        if not i_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT status, opened_date, closed_date, moderator_id, report_id FROM investigations WHERE investigation_id = %s;", (i_id,))
            row = cur.fetchone()
            if row:
                self.status_var.set(row[0])
                self.open_var.set(row[1])
                self.close_var.set(row[2] if row[2] else "")
                self.mod_var.set(self.mod_reverse_map.get(row[3], ""))
                self.report_var.set(self.report_reverse_map.get(row[4], "") if row[4] else "")
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "תיק חקירה לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_logic(self, open_str, close_str, m_id, status):
        """פונקציית הגנה חכמה שמונעת מצבים לא חוקיים"""
        if not m_id:
            messagebox.showerror("שגיאה", "חובה לשייך פקח לתיק החקירה.")
            return False
        if not status:
            messagebox.showerror("שגיאה", "חובה לבחור סטטוס חקירה.")
            return False
            
        # --- התוספת החדשה: חסימת סטטוס ותאריך מנוגדים ---
        if status == 'Closed' and not close_str:
            messagebox.showerror("שגיאה לוגית", "תיק חקירה 'סגור' חייב להכיל תאריך סגירה!")
            return False
            
        if status == 'In Progress' and close_str:
            messagebox.showerror("שגיאה לוגית", "תיק חקירה 'בתהליך' אינו יכול להכיל תאריך סגירה. השאר את השדה ריק או שנה סטטוס.")
            return False
        # --------------------------------------------------

        try:
            open_date = datetime.strptime(open_str, "%Y-%m-%d").date()
            if close_str:
                close_date = datetime.strptime(close_str, "%Y-%m-%d").date()
                if close_date < open_date:
                    messagebox.showerror("שגיאה לוגית", "תאריך סגירת התיק לא יכול להיות לפני תאריך הפתיחה!")
                    return False
            return True
        except ValueError:
            messagebox.showerror("שגיאת תאריך", "פורמט תאריך לא תקין. יש להזין YYYY-MM-DD")
            return False

    def insert_record(self):
        open_str = self.open_var.get()
        close_str = self.close_var.get()
        status = self.status_var.get()
        m_id = self.mod_map.get(self.mod_var.get())
        
        if not self.validate_logic(open_str, close_str, m_id, status): return

        r_id = self.report_map.get(self.report_var.get()) if self.report_var.get() != '' else None
        c_date = close_str if close_str.strip() != '' else None

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO investigations (investigation_id, opened_date, closed_date, status, moderator_id, report_id) VALUES (%s, %s, %s, %s, %s, %s);"
            values = (self.id_var.get(), open_str, c_date, status, m_id, r_id)
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "חקירה חדשה נפתחה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        open_str = self.open_var.get()
        close_str = self.close_var.get()
        status = self.status_var.get()
        m_id = self.mod_map.get(self.mod_var.get())
        
        if not self.validate_logic(open_str, close_str, m_id, status): return

        r_id = self.report_map.get(self.report_var.get()) if self.report_var.get() != '' else None
        c_date = close_str if close_str.strip() != '' else None

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE investigations SET opened_date=%s, closed_date=%s, status=%s, moderator_id=%s, report_id=%s WHERE investigation_id=%s;"
            values = (open_str, c_date, status, m_id, r_id, self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "חקירה עודכנה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק חקירה זו? ייתכן ויש ראיות או חסימות שמקושרות אליה ויימנעו את המחיקה."): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM investigations WHERE investigation_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "החקירה נמחקה בהצלחה!")
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
        self.status_var.set(vals[1])
        self.open_var.set(vals[2])
        self.close_var.set(vals[3] if vals[3] != 'None' else '')
        self.mod_var.set(vals[4])
        self.report_var.set(vals[5] if vals[5] != 'חקירה יזומה (ללא דיווח)' else '')

    def clear_form(self):
        self.id_var.set("")
        self.status_var.set("")
        self.open_var.set("")
        self.close_var.set("")
        self.mod_var.set("")
        self.report_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = InvestigationsCRUD(root)
    root.mainloop()