import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class TournamentCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול טורנירים - FairPlay DB")
        self.root.geometry("1000x600")
        

        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילון תרגום למועדונים
        self.club_map, self.club_reverse_map = {}, {}

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
        """טעינת המועדונים ליצירת תפריט נפתח קריא"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT club_id, name FROM club;")
            for c_id, name in cur.fetchall():
                self.club_map[name] = c_id
                self.club_reverse_map[c_id] = name
            cur.close()
            
            # אכלוס התפריט במסך
            self.club_combo['values'] = list(self.club_map.keys())

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מועדונים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי טורניר", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID ושם
        tk.Label(form_frame, text="מספר טורניר (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="שם הטורניר:").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.name_var, width=30).grid(row=0, column=4, sticky="w")

        # שורה 1: מועדון ותאריך הרשמה
        tk.Label(form_frame, text="מועדון מארח:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.club_var = tk.StringVar()
        self.club_combo = ttk.Combobox(form_frame, textvariable=self.club_var, width=28, state="readonly")
        self.club_combo.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="פתיחת הרשמה (YYYY-MM-DD):").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.reg_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.reg_date_var, width=15).grid(row=1, column=4, sticky="w")

        # שורה 2: תאריכי טורניר
        tk.Label(form_frame, text="תאריך התחלה:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.start_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.start_date_var, width=15).grid(row=2, column=1, sticky="w")

        tk.Label(form_frame, text="תאריך סיום:").grid(row=2, column=3, padx=5, pady=5, sticky="e")
        self.end_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.end_date_var, width=15).grid(row=2, column=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף טורניר", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן טורניר", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק טורניר", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "name", "club", "reg_open", "start", "end")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50)
        self.tree.heading("name", text="שם הטורניר")
        self.tree.column("name", width=200)
        self.tree.heading("club", text="מועדון")
        self.tree.column("club", width=150)
        self.tree.heading("reg_open", text="הרשמה נפתחת")
        self.tree.heading("start", text="התחלה")
        self.tree.heading("end", text="סיום")
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT tournament_id, name, club_id, registration_open_date, start_date, end_date FROM tournament ORDER BY tournament_id;")
            for row in cur.fetchall():
                t_id, name, c_id, reg_date, s_date, e_date = row
                
                # תרגום ה-ID לשם המועדון (או השארת ריק אם אין מועדון)
                club_disp = self.club_reverse_map.get(c_id, "") if c_id else "ללא מועדון"
                
                self.tree.insert("", "end", values=(t_id, name, club_disp, reg_date, s_date, e_date))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        t_id = self.id_var.get()
        if not t_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT name, club_id, registration_open_date, start_date, end_date FROM tournament WHERE tournament_id = %s;", (t_id,))
            row = cur.fetchone()
            if row:
                self.name_var.set(row[0])
                self.club_var.set(self.club_reverse_map.get(row[1], "") if row[1] else "")
                self.reg_date_var.set(row[2])
                self.start_date_var.set(row[3])
                self.end_date_var.set(row[4])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "טורניר לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_dates(self, reg_str, start_str, end_str):
        """פונקציית הגנה (Validation) לחוקיות התאריכים של הטורניר"""
        try:
            r_date = datetime.strptime(reg_str, "%Y-%m-%d")
            s_date = datetime.strptime(start_str, "%Y-%m-%d")
            e_date = datetime.strptime(end_str, "%Y-%m-%d")
            
            if s_date < r_date:
                messagebox.showerror("שגיאת תאריכים", "הטורניר אינו יכול להתחיל לפני שנפתחה ההרשמה אליו!")
                return False
                
            if e_date < s_date:
                messagebox.showerror("שגיאת תאריכים", "תאריך סיום הטורניר חייב להיות שווה או מאוחר לתאריך ההתחלה!")
                return False
                
            return True
        except ValueError:
            messagebox.showerror("שגיאת פורמט", "אנא ודא שכל התאריכים מלאים וכתובים בפורמט תקין: YYYY-MM-DD")
            return False

    def insert_record(self):
        reg = self.reg_date_var.get()
        start = self.start_date_var.get()
        end = self.end_date_var.get()
        
        if not self.validate_dates(reg, start, end):
            return

        c_id = self.club_map.get(self.club_var.get()) if self.club_var.get() else None
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO tournament (tournament_id, name, club_id, registration_open_date, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s);"
            values = (self.id_var.get(), self.name_var.get(), c_id, reg, start, end)
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הטורניר נוסף בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        reg = self.reg_date_var.get()
        start = self.start_date_var.get()
        end = self.end_date_var.get()
        
        if not self.validate_dates(reg, start, end):
            return

        c_id = self.club_map.get(self.club_var.get()) if self.club_var.get() else None
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE tournament SET name=%s, club_id=%s, registration_open_date=%s, start_date=%s, end_date=%s WHERE tournament_id=%s;"
            values = (self.name_var.get(), c_id, reg, start, end, self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הטורניר עודכן בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק טורניר זה?"):
            return
            
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM tournament WHERE tournament_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הטורניר נמחק בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", f"לא ניתן למחוק (ייתכן ויש הרשמות או משחקים מקושרים):\n{e}")
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        vals = self.tree.item(selected, 'values')
        
        self.id_var.set(vals[0])
        self.name_var.set(vals[1])
        # אם כתוב "ללא מועדון" נשאיר את השדה במסך ריק
        self.club_var.set(vals[2] if vals[2] != "ללא מועדון" else "")
        self.reg_date_var.set(vals[3])
        self.start_date_var.set(vals[4])
        self.end_date_var.set(vals[5])

    def clear_form(self):
        self.id_var.set("")
        self.name_var.set("")
        self.club_var.set("")
        self.reg_date_var.set("")
        self.start_date_var.set("")
        self.end_date_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = TournamentCRUD(root)
    root.mainloop()