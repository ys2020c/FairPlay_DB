import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class BansCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול חסימות שחקנים - מסך מפתחות זרים")
        self.root.geometry("900x600")
        
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילונים לתרגום ID לטקסט קריא (בשביל המפתחות הזרים)
        self.reasons_map = {}         # מתרגם: טקסט -> ID
        self.reasons_reverse_map = {} # מתרגם: ID -> טקסט
        
        self.inv_map = {}             # מתרגם: טקסט -> ID
        self.inv_reverse_map = {}     # מתרגם: ID -> טקסט
        
        self.players_list = []

        self.create_widgets()
        
        # סדר הפעולות קריטי: קודם טוענים את המפתחות הזרים, ואז את נתוני הטבלה
        self.load_fk_data()
        self.fetch_data()

    def get_db_connection(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר למסד הנתונים:\n{e}")
            return None

    def load_fk_data(self):
        """טעינת המפתחות הזרים מהטבלאות המקושרות והמרתם לטקסט קריא"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            
            # 1. טעינת סיבות חסימה
            cur.execute("SELECT reason_id, br_description FROM ban_reasons;")
            for r_id, desc in cur.fetchall():
                self.reasons_map[desc] = r_id
                self.reasons_reverse_map[r_id] = desc
                
            # 2. טעינת חקירות (הצגת סטטוס ותאריך במקום ID)
            cur.execute("SELECT investigation_id, opened_date, status FROM investigations;")
            for i_id, o_date, status in cur.fetchall():
                display_str = f"חקירה #{i_id} ({status}) - נפתחה ב:{o_date}"
                self.inv_map[display_str] = i_id
                self.inv_reverse_map[i_id] = display_str

            # 3. טעינת שחקנים (username הוא כבר מחרוזת קריאה)
            cur.execute("SELECT username FROM player;")
            self.players_list = [row[0] for row in cur.fetchall()]
            
            cur.close()
            
            # עדכון התפריטים הנפתחים במסך עם המילים ולא המספרים
            self.reason_combo['values'] = list(self.reasons_map.keys())
            self.inv_combo['values'] = list(self.inv_map.keys())
            self.player_combo['values'] = self.players_list

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת המפתחות הזרים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        # אזור טופס הנתונים
        form_frame = tk.LabelFrame(self.root, text="פרטי חסימה (Ban)", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Ban ID (מפתח ראשי)
        tk.Label(form_frame, text="מספר חסימה (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        self.id_entry = tk.Entry(form_frame, textvariable=self.id_var)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(form_frame, text="חפש לפי ID (עדכון)", command=self.fetch_by_id).grid(row=0, column=2, padx=5)

        # Player Username (מפתח זר)
        tk.Label(form_frame, text="שחקן נחסם:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.player_var = tk.StringVar()
        self.player_combo = ttk.Combobox(form_frame, textvariable=self.player_var)
        self.player_combo.grid(row=1, column=1, padx=5, pady=5)

        # Start Date
        tk.Label(form_frame, text="תאריך התחלה:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.start_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.start_date_var).grid(row=2, column=1, padx=5, pady=5)

        # End Date
        tk.Label(form_frame, text="תאריך סיום:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.end_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.end_date_var).grid(row=3, column=1, padx=5, pady=5)

        # Investigation ID (מפתח זר - מוצג כטקסט)
        tk.Label(form_frame, text="תיק חקירה:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.inv_var = tk.StringVar()
        self.inv_combo = ttk.Combobox(form_frame, textvariable=self.inv_var, state="readonly", width=40)
        self.inv_combo.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # Reason ID (מפתח זר - מוצג כטקסט)
        tk.Label(form_frame, text="סיבת חסימה:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.reason_var = tk.StringVar()
        self.reason_combo = ttk.Combobox(form_frame, textvariable=self.reason_var, state="readonly", width=40)
        self.reason_combo.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # כפתורים
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(buttons_frame, text="הוסף חסימה חדשה", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="עדכן חסימה", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="מחק", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(buttons_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה (Treeview)
        columns = ("id", "player", "start", "end", "inv", "reason")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("player", text="שחקן")
        self.tree.heading("start", text="התחלה")
        self.tree.heading("end", text="סיום")
        self.tree.heading("inv", text="חקירה מקושרת")
        self.tree.heading("reason", text="סיבה")
        
        self.tree.column("inv", width=250)
        self.tree.column("reason", width=200)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    # --- פונקציות מסד נתונים ---

    def fetch_data(self):
        """שליפת הנתונים והצגת שמות במקום מספרים"""
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            # שליפה רגילה. את ההמרה לטקסט אנחנו עושים בעזרת המילונים שיצרנו!
            cur.execute("SELECT ban_id, banned_player, start_date, end_date, investigation_id, reason_id FROM bans ORDER BY ban_id;")
            for row in cur.fetchall():
                ban_id, player, s_date, e_date, inv_id, reason_id = row
                
                # תרגום ה-IDs לטקסט נעים לעין
                inv_display = self.inv_reverse_map.get(inv_id, f"Unknown ID: {inv_id}")
                reason_display = self.reasons_reverse_map.get(reason_id, f"Unknown ID: {reason_id}")
                
                self.tree.insert("", "end", values=(ban_id, player, s_date, e_date, inv_display, reason_display))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בשליפת חסימות:\n{e}")
        finally:
            conn.close()

    def fetch_by_id(self):
        ban_id = self.id_var.get()
        if not ban_id: return
        
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT banned_player, start_date, end_date, investigation_id, reason_id FROM bans WHERE ban_id = %s;", (ban_id,))
            row = cur.fetchone()
            if row:
                self.player_var.set(row[0])
                self.start_date_var.set(row[1])
                self.end_date_var.set(row[2])
                
                # תרגום חזרה לטקסט כדי שיופיע יפה בטופס
                self.inv_var.set(self.inv_reverse_map.get(row[3], ""))
                self.reason_var.set(self.reasons_reverse_map.get(row[4], ""))
                
                messagebox.showinfo("נמצא", "הנתונים נטענו, ניתן לעדכן.")
            else:
                messagebox.showinfo("לא נמצא", "מספר החסימה לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def insert_record(self):
        # המרה הפוכה: מטקסט קריא חזרה ל-ID בשביל הדוקר
        reason_id = self.reasons_map.get(self.reason_var.get())
        inv_id = self.inv_map.get(self.inv_var.get())
        
        if not reason_id or not inv_id:
            messagebox.showerror("שגיאה", "אנא בחר סיבה וחקירה חוקיים מהרשימה")
            return

        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            query = "INSERT INTO bans (ban_id, banned_player, start_date, end_date, investigation_id, reason_id) VALUES (%s, %s, %s, %s, %s, %s);"
            values = (self.id_var.get(), self.player_var.get(), self.start_date_var.get(), self.end_date_var.get(), inv_id, reason_id)
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", f"הפעולה נדחתה:\n{e}")
        finally:
            conn.close()

    def update_record(self):
        reason_id = self.reasons_map.get(self.reason_var.get())
        inv_id = self.inv_map.get(self.inv_var.get())
        
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            query = "UPDATE bans SET banned_player=%s, start_date=%s, end_date=%s, investigation_id=%s, reason_id=%s WHERE ban_id=%s;"
            values = (self.player_var.get(), self.start_date_var.get(), self.end_date_var.get(), inv_id, reason_id, self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            # הטריגר של שלב ד' יקפיץ את השגיאה לכאן אם ננסה לקצר חסימה!
            messagebox.showerror("עדכון נכשל", f"הודעת מערכת:\n{e}")
        finally:
            conn.close()

    def delete_record(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM bans WHERE ban_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        values = self.tree.item(selected, 'values')
        
        self.id_var.set(values[0])
        self.player_var.set(values[1])
        self.start_date_var.set(values[2])
        self.end_date_var.set(values[3])
        self.inv_var.set(values[4])
        self.reason_var.set(values[5])

    def clear_form(self):
        self.id_var.set("")
        self.player_var.set("")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.inv_var.set("")
        self.reason_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = BansCRUD(root)
    root.mainloop()