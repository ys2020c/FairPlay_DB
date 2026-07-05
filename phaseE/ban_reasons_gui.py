import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class BanReasonsCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול סיבות חסימה (Ban Reasons) - FairPlay DB")
        self.root.geometry("700x450")
        
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
        form_frame = tk.LabelFrame(self.root, text="פרטי סיבת חסימה", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # ID
        tk.Label(form_frame, text="מספר סיבה (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5)

        # Description
        tk.Label(form_frame, text="תיאור (Description):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.desc_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.desc_var, width=50).grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף סיבה", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן סיבה", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק סיבה", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "description")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=80)
        self.tree.heading("description", text="תיאור סיבת החסימה")
        self.tree.column("description", width=550)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT reason_id, br_description FROM ban_reasons ORDER BY reason_id;")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
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
            cur.execute("SELECT br_description FROM ban_reasons WHERE reason_id = %s;", (r_id,))
            row = cur.fetchone()
            if row:
                self.desc_var.set(row[0])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "סיבת חסימה לא קיימת.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_inputs(self, r_id, desc):
        """בדיקת תקינות הקלט בהתאם לאילוצי ה-DB"""
        if not r_id or not desc:
            messagebox.showerror("שגיאה", "אנא מלא את כל השדות.")
            return False
            
        try:
            r_id_int = int(r_id)
            if r_id_int <= 0:
                messagebox.showerror("שגיאה לוגית", "מזהה סיבת החסימה (ID) חייב להיות מספר חיובי גדול מ-0.")
                return False
            return True
        except ValueError:
            messagebox.showerror("שגיאת קלט", "ה-ID חייב להיות מספר שלם.")
            return False

    def insert_record(self):
        r_id = self.id_var.get()
        desc = self.desc_var.get()
        
        if not self.validate_inputs(r_id, desc): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO ban_reasons (reason_id, br_description) VALUES (%s, %s);"
            cur.execute(query, (r_id, desc))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "סיבת החסימה נוספה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        r_id = self.id_var.get()
        desc = self.desc_var.get()
        
        if not self.validate_inputs(r_id, desc): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE ban_reasons SET br_description=%s WHERE reason_id=%s;"
            cur.execute(query, (desc, r_id))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "סיבת החסימה עודכנה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק סיבה זו? (לא ניתן למחוק אם קיימות חסימות המקושרות אליה)"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM ban_reasons WHERE reason_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "סיבת החסימה נמחקה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"מחיקה נכשלה:\n{e}")
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        vals = self.tree.item(selected, 'values')
        
        self.id_var.set(vals[0])
        self.desc_var.set(vals[1])

    def clear_form(self):
        self.id_var.set("")
        self.desc_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = BanReasonsCRUD(root)
    root.mainloop()