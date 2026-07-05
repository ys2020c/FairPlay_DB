import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class RegistrationCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול הרשמות לטורנירים - FairPlay DB")
        self.root.geometry("900x550")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234",
            "host": "localhost",
            "port": "5432"
        }

        # מילוני תרגום למפתחות זרים ולוגיקה חכמה
        self.tourney_map, self.tourney_reverse_map = {}, {}
        self.player_map, self.player_reverse_map = {}, {}
        self.tourney_dates = {} # שומר את תאריכי הטורניר כדי למנוע הרשמות לא הגיוניות

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
        """טעינת הטורנירים והשחקנים ליצירת תפריטים נפתחים קריאים"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            
            # טעינת טורנירים (כולל תאריכי פתיחת הרשמה וסיום הטורניר בשביל הלוגיקה!)
            cur.execute("SELECT tournament_id, name, registration_open_date, end_date FROM tournament;")
            for t_id, name, open_date, end_date in cur.fetchall():
                self.tourney_map[name] = t_id
                self.tourney_reverse_map[t_id] = name
                # שומרים את התאריכים במילון כדי לבדוק מולם מאוחר יותר
                self.tourney_dates[t_id] = {"open": open_date, "end": end_date}
                
            # טעינת שחקנים
            cur.execute("SELECT player_id, username FROM player;")
            for p_id, username in cur.fetchall():
                self.player_map[username] = p_id
                self.player_reverse_map[p_id] = username
                
            cur.close()
            
            # אכלוס התפריטים במסך
            self.tourney_combo['values'] = list(self.tourney_map.keys())
            self.player_combo['values'] = list(self.player_map.keys())

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מפתחות זרים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי הרשמה", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID וסטטוס
        tk.Label(form_frame, text="מספר הרשמה (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="סטטוס (Status):").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(form_frame, textvariable=self.status_var, width=20)
        self.status_combo['values'] = ['Confirmed', 'Pending', 'Cancelled', 'Waiting List']
        self.status_combo.grid(row=0, column=4, sticky="w")

        # שורה 1: טורניר ושחקן
        tk.Label(form_frame, text="טורניר:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.tourney_var = tk.StringVar()
        self.tourney_combo = ttk.Combobox(form_frame, textvariable=self.tourney_var, width=30, state="readonly")
        self.tourney_combo.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="שחקן נרשם:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.player_var = tk.StringVar()
        self.player_combo = ttk.Combobox(form_frame, textvariable=self.player_var, width=20, state="readonly")
        self.player_combo.grid(row=1, column=4, sticky="w")

        # שורה 2: תאריך הרשמה
        tk.Label(form_frame, text="תאריך רישום (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.date_var, width=15).grid(row=2, column=1, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף הרשמה", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן הרשמה", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק הרשמה", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "tourney", "player", "date", "status")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50)
        self.tree.heading("tourney", text="טורניר")
        self.tree.column("tourney", width=200)
        self.tree.heading("player", text="שחקן")
        self.tree.column("player", width=150)
        self.tree.heading("date", text="תאריך רישום")
        self.tree.heading("status", text="סטטוס")
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT reg_id, tournament_id, player_id, registered_date, status FROM registration ORDER BY reg_id;")
            for row in cur.fetchall():
                r_id, t_id, p_id, r_date, status = row
                
                # תרגום חכם לטקסט קריא
                tourney_disp = self.tourney_reverse_map.get(t_id, "חסר") if t_id else ""
                player_disp = self.player_reverse_map.get(p_id, "חסר") if p_id else ""
                
                self.tree.insert("", "end", values=(r_id, tourney_disp, player_disp, r_date, status if status else ""))
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
            cur.execute("SELECT tournament_id, player_id, registered_date, status FROM registration WHERE reg_id = %s;", (r_id,))
            row = cur.fetchone()
            if row:
                self.tourney_var.set(self.tourney_reverse_map.get(row[0], "") if row[0] else "")
                self.player_var.set(self.player_reverse_map.get(row[1], "") if row[1] else "")
                self.date_var.set(row[2])
                self.status_var.set(row[3] if row[3] else "")
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "הרשמה לא קיימת.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_logic(self, t_id, p_id, date_str):
        """פונקציה חכמה שבודקת את הלוגיקה העסקית מול הטורניר"""
        if not t_id or not p_id:
            messagebox.showerror("שגיאה", "חובה לבחור טורניר ושחקן.")
            return False
            
        try:
            # המרת המחרוזת לתאריך כדי שנוכל לבצע השוואות
            reg_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # שליפת תאריכי הטורניר הספציפי מהמילון שלנו
            t_dates = self.tourney_dates.get(t_id)
            if t_dates:
                open_date = t_dates['open']
                end_date = t_dates['end']
                
                # מניעת הרשמה מוקדמת מדי
                if reg_date < open_date:
                    messagebox.showerror("שגיאה לוגית", f"לא ניתן להירשם! ההרשמה לטורניר זה נפתחת רק ב-{open_date}")
                    return False
                    
                # מניעת הרשמה מאוחרת מדי
                if reg_date > end_date:
                    messagebox.showerror("שגיאה לוגית", f"הטורניר הסתיים ב-{end_date}. לא ניתן להירשם אליו יותר.")
                    return False
                    
            return True
        except ValueError:
            messagebox.showerror("שגיאת תאריך", "אנא ודא שהתאריך כתוב בפורמט תקין: YYYY-MM-DD")
            return False

    def insert_record(self):
        t_id = self.tourney_map.get(self.tourney_var.get())
        p_id = self.player_map.get(self.player_var.get())
        reg_date = self.date_var.get()
        status = self.status_var.get() or None
        
        if not self.validate_logic(t_id, p_id, reg_date): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO registration (reg_id, tournament_id, player_id, registered_date, status) VALUES (%s, %s, %s, %s, %s);"
            cur.execute(query, (self.id_var.get(), t_id, p_id, reg_date, status))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "ההרשמה נקלטה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        t_id = self.tourney_map.get(self.tourney_var.get())
        p_id = self.player_map.get(self.player_var.get())
        reg_date = self.date_var.get()
        status = self.status_var.get() or None
        
        if not self.validate_logic(t_id, p_id, reg_date): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE registration SET tournament_id=%s, player_id=%s, registered_date=%s, status=%s WHERE reg_id=%s;"
            cur.execute(query, (t_id, p_id, reg_date, status, self.id_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "ההרשמה עודכנה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק הרשמה זו?"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM registration WHERE reg_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "ההרשמה נמחקה בהצלחה!")
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
        self.tourney_var.set(vals[1])
        self.player_var.set(vals[2])
        self.date_var.set(vals[3])
        self.status_var.set(vals[4] if vals[4] != 'None' else '')

    def clear_form(self):
        self.id_var.set("")
        self.tourney_var.set("")
        self.player_var.set("")
        self.date_var.set("")
        self.status_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = RegistrationCRUD(root)
    root.mainloop()