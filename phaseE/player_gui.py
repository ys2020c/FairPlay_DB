import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class PlayerCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול שחקנים - FairPlay DB")
        self.root.geometry("600x400")
        

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
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר למסד הנתונים:\n{e}")
            return None

    def create_widgets(self):
        # אזור טופס הנתונים
        form_frame = tk.LabelFrame(self.root, text="פרטי שחקן", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Player ID
        tk.Label(form_frame, text="מספר שחקן (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        self.id_entry = tk.Entry(form_frame, textvariable=self.id_var)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5)

        # Username
        tk.Label(form_frame, text="שם משתמש:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.username_var).grid(row=1, column=1, padx=5, pady=5)

        # כפתורים
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(buttons_frame, text="הוסף שחקן", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="עדכן שחקן", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="מחק", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        columns = ("id", "username")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="שם משתמש")
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    # --- פונקציות מסד נתונים ---

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT player_id, username FROM player ORDER BY player_id;")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בשליפת שחקנים:\n{e}")
        finally:
            conn.close()

    def fetch_by_id(self):
        p_id = self.id_var.get()
        if not p_id: return
        
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT username FROM player WHERE player_id = %s;", (p_id,))
            row = cur.fetchone()
            if row:
                self.username_var.set(row[0])
                messagebox.showinfo("נמצא", "הנתונים נטענו, ניתן לעדכן.")
            else:
                messagebox.showinfo("לא נמצא", "מספר השחקן לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def insert_record(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO player (player_id, username) VALUES (%s, %s);"
            cur.execute(query, (self.id_var.get(), self.username_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה בהוספה", f"וודא שה-ID ושם המשתמש ייחודיים.\n{e}")
        finally:
            conn.close()

    def update_record(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE player SET username=%s WHERE player_id=%s;"
            cur.execute(query, (self.username_var.get(), self.id_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה בעדכון", str(e))
        finally:
            conn.close()

    def delete_record(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM player WHERE player_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה במחיקה", f"ייתכן ויש חסימות או משחקים מקושרים לשחקן זה:\n{e}")
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        values = self.tree.item(selected, 'values')
        self.id_var.set(values[0])
        self.username_var.set(values[1])

    def clear_form(self):
        self.id_var.set("")
        self.username_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = PlayerCRUD(root)
    root.mainloop()