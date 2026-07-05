import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

class EvidenceCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("ניהול ראיות (מפתח ראשי מורכב) - FairPlay DB")
        self.root.geometry("1000x600")
        
        # --- פרטי ההתחברות לדוקר ---
        self.db_config = {
            "dbname": "fairplay",
            "user": "postgres",
            "password": "1234", 
            "host": "localhost",
            "port": "5432"
        }

        # מילוני תרגום למפתח הזר
        self.inv_map, self.inv_reverse_map = {}, {}

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
        """טעינת חקירות לתפריט נפתח קריא"""
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            # נטען את מזהה החקירה ותאריך הפתיחה כדי שיהיה ברור למשתמש
            cur.execute("SELECT investigation_id, opened_date, status FROM investigations;")
            for i_id, o_date, status in cur.fetchall():
                display_str = f"חקירה #{i_id} ({status}) מ-{o_date}"
                self.inv_map[display_str] = i_id
                self.inv_reverse_map[i_id] = display_str
                
            cur.close()
            self.inv_combo['values'] = list(self.inv_map.keys())

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת חקירות:\n{e}")
        finally:
            conn.close()

    def create_widgets(self):
        form_frame = tk.LabelFrame(self.root, text="פרטי ראיה (שים לב: מפתח ראשי מורכב מ-ID ומחקירה)", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # שורה 0: מפתחות ראשיים מורכבים
        tk.Label(form_frame, text="מספר ראיה (ID):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.id_var, width=15).grid(row=0, column=1, sticky="w")

        tk.Label(form_frame, text="חקירה מקושרת:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.inv_var = tk.StringVar()
        self.inv_combo = ttk.Combobox(form_frame, textvariable=self.inv_var, width=35, state="readonly")
        self.inv_combo.grid(row=0, column=3, sticky="w")

        # כפתור חיפוש מיוחד הדורש את שני השדות
        tk.Button(form_frame, text="חפש לפי ID + חקירה", command=self.fetch_by_composite_key, bg="lightyellow").grid(row=0, column=4, padx=10)

        # שורה 1: סוג ראיה וקישור
        tk.Label(form_frame, text="סוג ראיה (Type):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, width=20, state="readonly")
        # אילוץ CHECK מהדאטה-בייס הומר לתפריט סגור
        self.type_combo['values'] = ['Screenshot', 'Video', 'Chat Log', 'System Log']
        self.type_combo.grid(row=1, column=1, sticky="w")

        tk.Label(form_frame, text="קישור (URL):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.url_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.url_var, width=50).grid(row=1, column=3, columnspan=2, sticky="w")

        # אזור כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="הוסף ראיה", command=self.insert_record, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכן ראיה", command=self.update_record, bg="lightblue").pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחק ראיה", command=self.delete_record, bg="salmon").pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה טופס", command=self.clear_form).pack(side="left", padx=5)

        # טבלה
        cols = ("id", "inv", "type", "url")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("id", text="ID ראיה")
        self.tree.column("id", width=80)
        self.tree.heading("inv", text="חקירה מקושרת")
        self.tree.column("inv", width=250)
        self.tree.heading("type", text="סוג ראיה")
        self.tree.column("type", width=120)
        self.tree.heading("url", text="קישור (URL)")
        self.tree.column("url", width=450)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def fetch_data(self):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cur = conn.cursor()
            cur.execute("SELECT evidence_id, investigation_id, evidence_type, url_link FROM evidence ORDER BY investigation_id, evidence_id;")
            for row in cur.fetchall():
                e_id, i_id, e_type, url = row
                inv_disp = self.inv_reverse_map.get(i_id, f"חקירה #{i_id}")
                self.tree.insert("", "end", values=(e_id, inv_disp, e_type, url))
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def fetch_by_composite_key(self):
        """חיפוש הדורש את המפתח הראשי המורכב (ID + חקירה)"""
        e_id = self.id_var.get()
        inv_str = self.inv_var.get()
        
        if not e_id or not inv_str:
            messagebox.showerror("שגיאה", "לצורך חיפוש, חובה להזין גם מספר ראיה (ID) וגם לבחור חקירה מקושרת.")
            return
            
        i_id = self.inv_map.get(inv_str)
        
        conn = self.get_db_connection()
        if not conn: return
        
        try:
            cur = conn.cursor()
            # חיפוש לפי שני מפתחות
            cur.execute("SELECT evidence_type, url_link FROM evidence WHERE evidence_id = %s AND investigation_id = %s;", (e_id, i_id))
            row = cur.fetchone()
            if row:
                self.type_var.set(row[0])
                self.url_var.set(row[1])
                messagebox.showinfo("נמצא", "הנתונים נטענו בהצלחה.")
            else:
                messagebox.showinfo("לא נמצא", "ראיה עם שילוב מפתחות זה לא קיימת.")
            cur.close()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))
        finally:
            conn.close()

    def validate_inputs(self, e_id, inv_str, e_type, url):
        if not e_id or not inv_str:
            messagebox.showerror("שגיאה", "חובה להזין מספר ראיה ולבחור חקירה (מפתח ראשי מורכב).")
            return False
        if not e_type:
            messagebox.showerror("שגיאה", "חובה לבחור סוג ראיה.")
            return False
        if not url:
            messagebox.showerror("שגיאה", "חובה להזין קישור לראיה.")
            return False
        return True

    def insert_record(self):
        e_id = self.id_var.get()
        inv_str = self.inv_var.get()
        e_type = self.type_var.get()
        url = self.url_var.get()
        
        if not self.validate_inputs(e_id, inv_str, e_type, url): return
        
        i_id = self.inv_map.get(inv_str)

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            query = "INSERT INTO evidence (evidence_id, investigation_id, evidence_type, url_link) VALUES (%s, %s, %s, %s);"
            cur.execute(query, (e_id, i_id, e_type, url))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הראיה נוספה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def update_record(self):
        e_id = self.id_var.get()
        inv_str = self.inv_var.get()
        e_type = self.type_var.get()
        url = self.url_var.get()
        
        if not self.validate_inputs(e_id, inv_str, e_type, url): return
        
        i_id = self.inv_map.get(inv_str)

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            # עדכון לפי מפתח כפול!
            query = "UPDATE evidence SET evidence_type=%s, url_link=%s WHERE evidence_id=%s AND investigation_id=%s;"
            cur.execute(query, (e_type, url, e_id, i_id))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הראיה עודכנה בהצלחה!")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("שגיאת מסד נתונים", str(e))
        finally:
            conn.close()

    def delete_record(self):
        e_id = self.id_var.get()
        inv_str = self.inv_var.get()
        
        if not e_id or not inv_str:
            messagebox.showerror("שגיאה", "בחר ראיה מהטבלה למחיקה (חובה מזהה וחקירה).")
            return
            
        i_id = self.inv_map.get(inv_str)

        if not messagebox.askyesno("אישור", "האם למחוק ראיה זו?"): return
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            # מחיקה לפי מפתח כפול
            cur.execute("DELETE FROM evidence WHERE evidence_id=%s AND investigation_id=%s;", (e_id, i_id))
            conn.commit()
            self.clear_form()
            self.fetch_data()
            messagebox.showinfo("הצלחה", "הראיה נמחקה בהצלחה!")
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
        self.inv_var.set(vals[1])
        self.type_var.set(vals[2])
        self.url_var.set(vals[3])

    def clear_form(self):
        self.id_var.set("")
        self.inv_var.set("")
        self.type_var.set("")
        self.url_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = EvidenceCRUD(root)
    root.mainloop()