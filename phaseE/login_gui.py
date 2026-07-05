import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("התחברות - FairPlay DB")
        self.root.geometry("400x350")
        self.root.configure(bg="#2c3e50") # רקע כהה ויוקרתי
        
        # מסגרת פנימית
        frame = tk.Frame(self.root, bg="#ecf0f1", padx=30, pady=30)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # כותרת
        tk.Label(frame, text="FairPlay Security", font=('Arial', 18, 'bold'), bg="#ecf0f1", fg="#2c3e50").pack(pady=(0, 20))
        tk.Label(frame, text="התחברות מנהל מערכת", font=('Arial', 12), bg="#ecf0f1", fg="#7f8c8d").pack(pady=(0, 20))
        
        # שם משתמש
        tk.Label(frame, text="שם משתמש:", font=('Arial', 10, 'bold'), bg="#ecf0f1").pack(anchor="e")
        self.user_entry = tk.Entry(frame, width=25, font=('Arial', 12), justify="right")
        self.user_entry.pack(pady=(0, 15))
        
        # סיסמה
        tk.Label(frame, text="סיסמה:", font=('Arial', 10, 'bold'), bg="#ecf0f1").pack(anchor="e")
        self.pass_entry = tk.Entry(frame, width=25, font=('Arial', 12), show="*", justify="right")
        self.pass_entry.pack(pady=(0, 20))
        
        # כפתור התחברות
        tk.Button(frame, text="הכנס למערכת", command=self.login, font=('Arial', 12, 'bold'), bg="#27ae60", fg="white", width=20, height=2).pack()

    def login(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        # נגדיר פרטי התחברות קשיחים (Hardcoded) לצורך הדגמה למרצים
        if username == "admin" and password == "1234":
            messagebox.showinfo("התחברות מוצלחת", "ברוך הבא למערכת FairPlay!")
            self.root.destroy() # סוגר את מסך ההתחברות
            self.open_main_dashboard()
        else:
            messagebox.showerror("שגיאה", "שם משתמש או סיסמה שגויים!\n(רמז: admin / 1234)")

    def open_main_dashboard(self):
        """פותח את לוח הבקרה הראשי לאחר התחברות מוצלחת"""
        script_path = os.path.join(os.path.dirname(__file__), "main.py")
        try:
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("שגיאת מערכת", f"לא ניתן לטעון את לוח הבקרה:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginScreen(root)
    root.mainloop()