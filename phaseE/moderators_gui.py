import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class ModeratorsCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול פקחים - FairPlay DB")
        self.root.geometry("800x500")
        
        
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
        """יצירת חיבור למסד הנתונים"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            messagebox.showerror("שגיאת התחברות", f"לא ניתן להתחבר למסד הנתונים:\n{e}")
            return None

    def create_widgets(self):
        """יצירת הממשק הגרפי"""
        # אזור טופס הזנת הנתונים
        form_frame = tk.LabelFrame(self.root, text="פרטי פקח", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Moderator ID
        tk.Label(form_frame, text="תעודת מזהה (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        self.id_entry = tk.Entry(form_frame, textvariable=self.id_var)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Fetch Button (יישום דרישת שלב ה': שליפת הנתונים לפי מפתח)
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5)

        # Name
        tk.Label(form_frame, text="שם הפקח:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.name_var).grid(row=1, column=1, padx=5, pady=5)

        # Hire Date
        tk.Label(form_frame, text="תאריך גיוס (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.date_var).grid(row=2, column=1, padx=5, pady=5)

        # Role (Dropdown based on table constraints)
        tk.Label(form_frame, text="תפקיד:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(form_frame, textvariable=self.role_var, state="readonly")
        self.role_combo['values'] = ('Admin', 'Senior moderator', 'Moderator', 'Trial moderator')
        self.role_combo.grid(row=3, column=1, padx=5, pady=5)

        # אזור כפתורי הפעולות
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(buttons_frame, text="הוסף חדש", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="עדכן פקח", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="מחק פקח", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # אזור הטבלה לתצוגת הנתונים (Treeview)
        columns = ("id", "name", "hire_date", "role")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="שם")
        self.tree.heading("hire_date", text="תאריך גיוס")
        self.tree.heading("role", text="תפקיד")
        
        # אירוע לחיצה על שורה בטבלה כדי למלא את הטופס אוטומטית
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    # --- פונקציות מסד נתונים (CRUD) ---

    def fetch_data(self):
        """שליפת כל הנתונים והצגתם בטבלה"""
        conn = self.get_db_connection()
        if not conn: return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT moderator_id, mname, hire_date, role FROM moderators ORDER BY moderator_id;")
            rows = cur.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בשליפת נתונים:\n{e}")
        finally:
            conn.close()

    def fetch_by_id(self):
        """יישום הדרישה: מילוי שאר השדות על בסיס מפתח שהוזן"""
        mod_id = self.id_var.get()
        if not mod_id:
            messagebox.showwarning("אזהרה", "אנא הזן ID לחיפוש")
            return
            
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT mname, hire_date, role FROM moderators WHERE moderator_id = %s;", (mod_id,))
            row = cur.fetchone()
            if row:
                self.name_var.set(row[0])
                self.date_var.set(row[1])
                self.role_var.set(row[2])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה, ניתן לעדכן אותם כעת.")
            else:
                messagebox.showinfo("לא נמצא", "לא נמצא פקח עם ID זה.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בחיפוש:\n{e}")
        finally:
            conn.close()

    def insert_record(self):
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            query = "INSERT INTO moderators (moderator_id, mname, hire_date, role) VALUES (%s, %s, %s, %s);"
            values = (self.id_var.get(), self.name_var.get(), self.date_var.get(), self.role_var.get())
            cur.execute(query, values)
            conn.commit()
            messagebox.showinfo("הצלחה", "הפקח נוסף בהצלחה!")
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"שגיאה בהוספה:\n{e}")
        finally:
            conn.close()

    def update_record(self):
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            query = "UPDATE moderators SET mname=%s, hire_date=%s, role=%s WHERE moderator_id=%s;"
            values = (self.name_var.get(), self.date_var.get(), self.role_var.get(), self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            messagebox.showinfo("הצלחה", "פרטי הפקח עודכנו בהצלחה!")
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"שגיאה בעדכון:\n{e}")
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור מחיקה", "האם אתה בטוח שברצונך למחוק פקח זה?"):
            return
            
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            query = "DELETE FROM moderators WHERE moderator_id=%s;"
            cur.execute(query, (self.id_var.get(),))
            conn.commit()
            messagebox.showinfo("הצלחה", "הפקח נמחק בהצלחה!")
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"שגיאה במחיקה (ייתכן ויש עליו מגבלות מפתח זר):\n{e}")
        finally:
            conn.close()

    # --- פונקציות עזר לממשק ---

    def on_tree_select(self, event):
        """מילוי הטופס בעת לחיצה על שורה בטבלה"""
        selected_item = self.tree.focus()
        if not selected_item:
            return
        values = self.tree.item(selected_item, 'values')
        
        self.id_var.set(values[0])
        self.name_var.set(values[1])
        self.date_var.set(values[2])
        self.role_var.set(values[3])

    def clear_form(self):
        self.id_var.set("")
        self.name_var.set("")
        self.date_var.set("")
        self.role_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModeratorsCRUD(root)
    root.mainloop()