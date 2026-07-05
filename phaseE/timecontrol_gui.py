import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class TimeControlCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול בקרות זמן (Time Control) - FairPlay DB")
        self.root.geometry("800x500")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        self.create_widgets()
        self.fetch_data()

    def get_db_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר למסד הנתונים:\n{e}")
            return None

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי בקרת זמן", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID ושם סוג המשחק
        tk.Label(form_frame, text="מספר (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="שם (למשל Blitz, Rapid):").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.name_var, width=25).grid(row=0, column=4, sticky="w")

        # שורה 1: זמנים
        tk.Label(form_frame, text="זמן בסיס (בשניות):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.base_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.base_var, width=15).grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="תוספת זמן (Increment בשניות):").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.inc_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.inc_var, width=15).grid(row=1, column=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף בקרת זמן", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן בקרת זמן", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק בקרת זמן", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "name", "base", "inc")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=80)
        self.tree.heading("name", text="שם בקרת הזמן")
        self.tree.column("name", width=250)
        self.tree.heading("base", text="זמן בסיס (שניות)")
        self.tree.column("base", width=150)
        self.tree.heading("inc", text="תוספת זמן למהלך (שניות)")
        self.tree.column("inc", width=180)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT tc_id, name, base_seconds, increment_seconds FROM timecontrol ORDER BY tc_id;")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        tc_id = self.id_var.get()
        if not tc_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT name, base_seconds, increment_seconds FROM timecontrol WHERE tc_id = %s;", (tc_id,))
            row = cur.fetchone()
            if row:
                self.name_var.set(row[0])
                self.base_var.set(row[1])
                self.inc_var.set(row[2])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "בקרת זמן לא קיימת.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_inputs(self, base, inc):
        """פונקציית הגנה לוודא שהוזנו מספרים שלמים"""
        if not self.id_var.get() or not self.name_var.get() or not base or not inc:
            messagebox.showerror("שגיאה", "אנא מלא את כל השדות.")
            return False
        try:
            int(base)
            int(inc)
            return True
        except ValueError:
            messagebox.showerror("שגיאת קלט", "שדות זמן הבסיס ותוספת הזמן חייבים להכיל מספרים שלמים בלבד.")
            return False

    def insert_record(self):
        base = self.base_var.get()
        inc = self.inc_var.get()
        
        if not self.validate_inputs(base, inc): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO timecontrol (tc_id, name, base_seconds, increment_seconds) VALUES (%s, %s, %s, %s);"
            cur.execute(query, (self.id_var.get(), self.name_var.get(), base, inc))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "בקרת הזמן נוספה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        base = self.base_var.get()
        inc = self.inc_var.get()
        
        if not self.validate_inputs(base, inc): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE timecontrol SET name=%s, base_seconds=%s, increment_seconds=%s WHERE tc_id=%s;"
            cur.execute(query, (self.name_var.get(), base, inc, self.id_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "בקרת הזמן עודכנה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק בקרת זמן זו? (לא ניתן למחוק אם יש משחקים המקושרים אליה)"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM timecontrol WHERE tc_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "בקרת הזמן נמחקה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"מחיקה נכשלה (ייתכן שיש משחקים מקושרים):\n{e}")
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        vals = self.tree.item(selected, 'values')
        
        self.id_var.set(vals[0])
        self.name_var.set(vals[1])
        self.base_var.set(vals[2])
        self.inc_var.set(vals[3])

    def clear_form(self):
        self.id_var.set("")
        self.name_var.set("")
        self.base_var.set("")
        self.inc_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = TimeControlCRUD(root)
    root.mainloop()