import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class RoundCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול סיבובים בטורנירים - FairPlay DB")
        self.root.geometry("850x500")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילוני תרגום לטורנירים ולוגיקת תאריכים
        self.tourney_map, self.tourney_reverse_map = {}, {}
        self.tourney_dates = {} # שמירת תאריכי ההתחלה והסיום של הטורניר!

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
        """טעינת הטורנירים ותאריכיהם ליצירת תפריט נפתח קריא והגנות לוגיות"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT tournament_id, name, start_date, end_date FROM tournament;")
            for t_id, name, s_date, e_date in cur.fetchall():
                self.tourney_map[name] = t_id
                self.tourney_reverse_map[t_id] = name
                # שומרים את תאריכי הטורניר לצורך Validation
                self.tourney_dates[t_id] = {"start": s_date, "end": e_date}
                
            cur.close()
            
            # אכלוס התפריט (כולל אפשרות ריקה כי העמודה מאפשרת NULL)
            tourney_list = [''] + list(self.tourney_map.keys())
            self.tourney_combo['values'] = tourney_list

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת טורנירים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי סיבוב", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: ID וטורניר
        tk.Label(form_frame, text="מספר סיבוב (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="טורניר מקושר:").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.tourney_var = tk.StringVar()
        self.tourney_combo = ttk.Combobox(form_frame, textvariable=self.tourney_var, width=35, state="readonly")
        self.tourney_combo.grid(row=0, column=4, sticky="w")

        # שורה 1: מספר הסיבוב ותאריך
        tk.Label(form_frame, text="מס' סיבוב (Round Number):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.num_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.num_var, width=15).grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="תאריך מתוכנן (YYYY-MM-DD):").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.date_var, width=15).grid(row=1, column=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף סיבוב", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן סיבוב", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק סיבוב", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "tourney", "round_num", "date")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID סיבוב")
        self.tree.column("id", width=80)
        self.tree.heading("tourney", text="טורניר מקושר")
        self.tree.column("tourney", width=300)
        self.tree.heading("round_num", text="מספר הסיבוב (בפועל)")
        self.tree.column("round_num", width=150)
        self.tree.heading("date", text="תאריך מתוכנן")
        self.tree.column("date", width=150)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT round_id, tournament_id, round_number, scheduled_date FROM round ORDER BY round_id;")
            for row in cur.fetchall():
                r_id, t_id, r_num, s_date = row
                tourney_disp = self.tourney_reverse_map.get(t_id, "") if t_id else ""
                self.tree.insert("", "end", values=(r_id, tourney_disp, r_num, s_date))
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
            cur.execute("SELECT tournament_id, round_number, scheduled_date FROM round WHERE round_id = %s;", (r_id,))
            row = cur.fetchone()
            if row:
                self.tourney_var.set(self.tourney_reverse_map.get(row[0], "") if row[0] else "")
                self.num_var.set(row[1])
                self.date_var.set(row[2])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "סיבוב לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_logic(self, t_id, r_num, date_str):
        """הגנות לוגיות לבדיקת תקינות הקלט והתאריכים"""
        if not r_num:
            messagebox.showerror("שגיאה", "חובה להזין את מספר הסיבוב.")
            return False
        try:
            int(r_num)
        except ValueError:
            messagebox.showerror("שגיאת קלט", "מספר הסיבוב חייב להיות מספר שלם.")
            return False

        try:
            sch_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # בדיקה האם התאריך נופל בתוך חלון הזמן של הטורניר
            if t_id and t_id in self.tourney_dates:
                t_start = self.tourney_dates[t_id]["start"]
                t_end = self.tourney_dates[t_id]["end"]
                
                if sch_date < t_start or sch_date > t_end:
                    messagebox.showerror("שגיאה לוגית", f"תאריך הסיבוב אינו תקין!\nהטורניר פעיל בין התאריכים {t_start} עד {t_end}.")
                    return False
                    
            return True
        except ValueError:
            messagebox.showerror("שגיאת תאריך", "פורמט תאריך לא תקין. יש להזין YYYY-MM-DD")
            return False

    def insert_record(self):
        t_id = self.tourney_map.get(self.tourney_var.get()) if self.tourney_var.get() != '' else None
        r_num = self.num_var.get()
        date_str = self.date_var.get()
        
        if not self.validate_logic(t_id, r_num, date_str): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO round (round_id, tournament_id, round_number, scheduled_date) VALUES (%s, %s, %s, %s);"
            cur.execute(query, (self.id_var.get(), t_id, r_num, date_str))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הסיבוב נוסף בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        t_id = self.tourney_map.get(self.tourney_var.get()) if self.tourney_var.get() != '' else None
        r_num = self.num_var.get()
        date_str = self.date_var.get()
        
        if not self.validate_logic(t_id, r_num, date_str): return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "UPDATE round SET tournament_id=%s, round_number=%s, scheduled_date=%s WHERE round_id=%s;"
            cur.execute(query, (t_id, r_num, date_str, self.id_var.get()))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הסיבוב עודכן בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק סיבוב זה? (לא ניתן למחוק אם מקושרים אליו משחקים)"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM round WHERE round_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הסיבוב נמחק בהצלחה!")
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
        self.tourney_var.set(vals[1] if vals[1] != 'None' else '')
        self.num_var.set(vals[2])
        self.date_var.set(vals[3])

    def clear_form(self):
        self.id_var.set("")
        self.tourney_var.set("")
        self.num_var.set("")
        self.date_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = RoundCRUD(root)
    root.mainloop()