import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime

class GameCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול משחקים - מפתחות זרים מרובים (כולל הגנות לוגיות)")
        self.root.geometry("1100x700")
        
        
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילוני תרגום לכל חמשת המפתחות הזרים
        self.players_map, self.players_reverse_map = {}, {}
        self.tc_map, self.tc_reverse_map = {}, {}
        self.variant_map, self.variant_reverse_map = {}, {}
        self.round_map, self.round_reverse_map = {}, {}

        self.create_widgets()
        self.load_fk_data()
        self.fetch_data()

    def get_db_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר:\n{e}")
            return None

    def load_fk_data(self):
        """טעינת כל נתוני טבלאות המעטפת ליצירת תפריטים נפתחים קריאים"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            
            # 1. שחקנים
            cur.execute("SELECT player_id, username FROM player;")
            for p_id, username in cur.fetchall():
                self.players_map[username] = p_id
                self.players_reverse_map[p_id] = username
                
            # 2. בקרת זמן (Time Control) - תצוגה משולבת
            cur.execute("SELECT tc_id, name, base_seconds, increment_seconds FROM timecontrol;")
            for tc_id, name, base, inc in cur.fetchall():
                display_str = f"{name} ({base}s + {inc}s)"
                self.tc_map[display_str] = tc_id
                self.tc_reverse_map[tc_id] = display_str
                
            # 3. סוג משחק (Game Variant)
            cur.execute("SELECT variant_id, name FROM gamevariant;")
            for var_id, name in cur.fetchall():
                self.variant_map[name] = var_id
                self.variant_reverse_map[var_id] = name
                
            # 4. סיבובים (Rounds)
            cur.execute("SELECT round_id, round_number, scheduled_date FROM round;")
            for r_id, r_num, s_date in cur.fetchall():
                display_str = f"סיבוב {r_num} ({s_date})"
                self.round_map[display_str] = r_id
                self.round_reverse_map[r_id] = display_str

            cur.close()
            
            # אכלוס התפריטים
            players_list = list(self.players_map.keys())
            self.white_combo['values'] = players_list
            self.black_combo['values'] = players_list
            self.tc_combo['values'] = list(self.tc_map.keys())
            self.variant_combo['values'] = list(self.variant_map.keys())
            self.round_combo['values'] = list(self.round_map.keys())

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מפתחות זרים:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי משחק", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=5)

        # שורה 0: ID ותוצאה
        tk.Label(form_frame, text="מספר משחק (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")
        tk.Button(form_frame, text="חפש לפי ID", command=self.fetch_by_id).grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(form_frame, text="תוצאה (Result):").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.result_var = tk.StringVar()
        ttk.Combobox(form_frame, textvariable=self.result_var, values=['1-0', '0-1', '1/2-1/2', 'Unknown']).grid(row=0, column=4, sticky="w")

        # שורה 1: שחקנים
        tk.Label(form_frame, text="שחקן לבן:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.white_var = tk.StringVar()
        self.white_combo = ttk.Combobox(form_frame, textvariable=self.white_var, width=25)
        self.white_combo.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="שחקן שחור:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.black_var = tk.StringVar()
        self.black_combo = ttk.Combobox(form_frame, textvariable=self.black_var, width=25)
        self.black_combo.grid(row=1, column=4, sticky="w")

        # שורה 2: בקרת זמן וסוג
        tk.Label(form_frame, text="בקרת זמן:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.tc_var = tk.StringVar()
        self.tc_combo = ttk.Combobox(form_frame, textvariable=self.tc_var, width=25, state="readonly")
        self.tc_combo.grid(row=2, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="סוג משחק:").grid(row=2, column=3, padx=5, pady=5, sticky="e")
        self.variant_var = tk.StringVar()
        self.variant_combo = ttk.Combobox(form_frame, textvariable=self.variant_var, width=25, state="readonly")
        self.variant_combo.grid(row=2, column=4, sticky="w")

        # שורה 3: סיבוב ותאריכים
        tk.Label(form_frame, text="סיבוב:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.round_var = tk.StringVar()
        self.round_combo = ttk.Combobox(form_frame, textvariable=self.round_var, width=25, state="readonly")
        self.round_combo.grid(row=3, column=1, columnspan=2, sticky="w")

        tk.Label(form_frame, text="התחלה (YYYY-MM-DD):").grid(row=3, column=3, padx=5, pady=5, sticky="e")
        self.start_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.start_date_var, width=15).grid(row=3, column=4, sticky="w")

        tk.Label(form_frame, text="סיום (YYYY-MM-DD):").grid(row=4, column=3, padx=5, pady=5, sticky="e")
        self.end_date_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.end_date_var, width=15).grid(row=4, column=4, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף משחק", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן משחק", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק משחק", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "white", "black", "tc", "variant", "round", "res", "start", "end")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50)
        self.tree.heading("white", text="לבן")
        self.tree.heading("black", text="שחור")
        self.tree.heading("tc", text="בקרת זמן")
        self.tree.heading("variant", text="סוג")
        self.tree.heading("round", text="סיבוב")
        self.tree.heading("res", text="תוצאה")
        self.tree.column("res", width=70)
        self.tree.heading("start", text="התחלה")
        self.tree.heading("end", text="סיום")
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def get_fk_values(self):
        """פונקציית עזר להמרת טקסט ל-IDs בבטחה, תומכת בשדות ריקים (NULL)"""
        w = self.players_map.get(self.white_var.get()) if self.white_var.get() else None
        b = self.players_map.get(self.black_var.get()) if self.black_var.get() else None
        tc = self.tc_map.get(self.tc_var.get()) if self.tc_var.get() else None
        v = self.variant_map.get(self.variant_var.get()) if self.variant_var.get() else None
        r = self.round_map.get(self.round_var.get()) if self.round_var.get() else None
        return w, b, tc, v, r

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT game_id, white_player_id, black_player_id, tc_id, variant_id, round_id, result, start_date, end_date FROM game ORDER BY game_id;")
            for row in cur.fetchall():
                g_id, w_id, b_id, tc_id, v_id, r_id, res, s_date, e_date = row
                
                # תרגום לתצוגה חכמה
                w_disp = self.players_reverse_map.get(w_id, "")
                b_disp = self.players_reverse_map.get(b_id, "")
                tc_disp = self.tc_reverse_map.get(tc_id, "")
                v_disp = self.variant_reverse_map.get(v_id, "")
                r_disp = self.round_reverse_map.get(r_id, "")
                
                self.tree.insert("", "end", values=(g_id, w_disp, b_disp, tc_disp, v_disp, r_disp, res, s_date, e_date))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_id(self):
        g_id = self.id_var.get()
        if not g_id: return
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT white_player_id, black_player_id, tc_id, variant_id, round_id, result, start_date, end_date FROM game WHERE game_id = %s;", (g_id,))
            row = cur.fetchone()
            if row:
                self.white_var.set(self.players_reverse_map.get(row[0], ""))
                self.black_var.set(self.players_reverse_map.get(row[1], ""))
                self.tc_var.set(self.tc_reverse_map.get(row[2], ""))
                self.variant_var.set(self.variant_reverse_map.get(row[3], ""))
                self.round_var.set(self.round_reverse_map.get(row[4], ""))
                self.result_var.set(row[5] if row[5] else "")
                self.start_date_var.set(row[6] if row[6] else "")
                self.end_date_var.set(row[7] if row[7] else "")
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "משחק לא קיים.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_game_logic(self, w_id, b_id, start_str, end_str):
        """פונקציית עזר שבודקת את תקינות הנתונים לפני הפנייה לדאטה-בייס"""
        # 1. מניעת משחק נגד עצמך (אם נבחרו שני שחקנים)
        if w_id is not None and b_id is not None and w_id == b_id:
            messagebox.showerror("שגיאת חוקיות", "שחקן לא יכול לשחק נגד עצמו. אנא בחר שחקנים שונים לכל צבע.")
            return False
            
        # 2. בדיקת תאריכים בעברית
        if start_str and end_str:
            try:
                s_date = datetime.strptime(start_str, "%Y-%m-%d")
                e_date = datetime.strptime(end_str, "%Y-%m-%d")
                
                if e_date < s_date:
                    messagebox.showerror("שגיאת זמנים", "תאריך סיום המשחק אינו יכול להיות מוקדם מתאריך ההתחלה!")
                    return False
                    
                # חסימת משחקים שארוכים מ-30 יום (אופציונלי למערכת מציאותית יותר)
                if (e_date - s_date).days > 30:
                    messagebox.showwarning("אזהרת מערכת", "שים לב: הזנת משחק שאורכו מעל 30 יום. בדוק שוב את התאריכים.")
                    
            except ValueError:
                messagebox.showerror("שגיאת פורמט", "אנא ודא שהתאריכים כתובים בפורמט התקין: YYYY-MM-DD")
                return False
                
        return True

    def insert_record(self):
        w_id, b_id, tc_id, v_id, r_id = self.get_fk_values()
        s_date = self.start_date_var.get()
        e_date = self.end_date_var.get() or None
        
        # הרצת בדיקת התקינות שלנו (Validation)
        if not self.validate_game_logic(w_id, b_id, s_date, e_date):
            return

        res = self.result_var.get() or None
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO game (game_id, white_player_id, black_player_id, tc_id, variant_id, round_id, result, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            values = (self.id_var.get(), w_id, b_id, tc_id, v_id, r_id, res, s_date, e_date)
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "המשחק נוסף בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        w_id, b_id, tc_id, v_id, r_id = self.get_fk_values()
        s_date = self.start_date_var.get()
        e_date = self.end_date_var.get() or None
        
        # הרצת בדיקת התקינות שלנו (Validation)
        if not self.validate_game_logic(w_id, b_id, s_date, e_date):
            return

        res = self.result_var.get() or None
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = """UPDATE game SET white_player_id=%s, black_player_id=%s, tc_id=%s, variant_id=%s, round_id=%s, result=%s, start_date=%s, end_date=%s WHERE game_id=%s;"""
            values = (w_id, b_id, tc_id, v_id, r_id, res, s_date, e_date, self.id_var.get())
            cur.execute(query, values)
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "המשחק עודכן בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        if not messagebox.askyesno("אישור", "האם למחוק משחק זה?"):
            return
            
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM game WHERE game_id=%s;", (self.id_var.get(),))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "המשחק נמחק בהצלחה!")
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
        self.white_var.set(vals[1] if vals[1] != 'None' else '')
        self.black_var.set(vals[2] if vals[2] != 'None' else '')
        self.tc_var.set(vals[3] if vals[3] != 'None' else '')
        self.variant_var.set(vals[4] if vals[4] != 'None' else '')
        self.round_var.set(vals[5] if vals[5] != 'None' else '')
        self.result_var.set(vals[6] if vals[6] != 'None' else '')
        self.start_date_var.set(vals[7] if vals[7] != 'None' else '')
        self.end_date_var.set(vals[8] if vals[8] != 'None' else '')

    def clear_form(self):
        self.id_var.set("")
        self.white_var.set("")
        self.black_var.set("")
        self.tc_var.set("")
        self.variant_var.set("")
        self.round_var.set("")
        self.result_var.set("")
        self.start_date_var.set("")
        self.end_date_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameCRUD(root)
    root.mainloop()