import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class GameVariantCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול סוגי משחק (Game Variants) - FairPlay DB")
        self.root.geometry("600x450")
        
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
        form_frame = tk.LabelFrame(self.root, text="פרטי סוג משחק", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # ID
        tk.Label(form_frame, text="מספר (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5)

        # Name
        tk.Label(form_frame, text="שם (למשל Standard, Chess960):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.name_var, width=30).grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף סוג", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן סוג", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק סוג", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "name")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=100)
        self.tree.heading("name", text="סוג משחק")
        self.tree.column("name", width=400)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT variant_id, name FROM gamevariant ORDER BY variant_id;")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        v_id = self.id_var.get()
        if not v_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM gamevariant WHERE variant_id = %s;", (v_id,))
            row = cur.fetchone()
            if row:
                self.name_var.set(row[0])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "סוג משחק לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def insert_record(self):
        if not self.id_var.get() or not self.name_var.get():
            messagebox.showerror("שגיאה", "אנא מלא את כל השדות.")
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO gamevariant (variant_id, name) VALUES (%s, %s);", (self.id_var.get(), self.name_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "סוג המשחק נוסף בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        if not self.id_var.get() or not self.name_var.get():
            messagebox.showerror("שגיאה", "אנא מלא את כל השדות.")
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("UPDATE gamevariant SET name=%s WHERE variant_id=%s;", (self.name_var.get(), self.id_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "סוג המשחק עודכן בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק סוג זה? (לא ניתן למחוק אם מקושרים אליו משחקים בטבלת game)"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM gamevariant WHERE variant_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "סוג המשחק נמחק בהצלחה!")
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
        self.name_var.set(vals[1])

    def clear_form(self):
        self.id_var.set("")
        self.name_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameVariantCRUD(root)
    root.mainloop()