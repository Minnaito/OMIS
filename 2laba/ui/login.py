import tkinter as tk
from tkinter import messagebox
from services import AuthService

class LoginFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#FFFFFF')
        self.app = app
        self.pack(fill='both', expand=True)

        outer = tk.Frame(self, bg='#FFFFFF')
        outer.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(outer, text="Система контроля доступа и безопасности", bg='#FFFFFF', fg='#333333', font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(outer, text="Вход в систему", bg='#FFFFFF', fg='#333333', font=("Arial", 12)).pack(pady=(0, 20))

        box = tk.LabelFrame(outer, text="Авторизация", padx=20, pady=20, bg='#FFFFFF', fg='#5A4A4D', relief='solid', bd=1)
        box.pack()

        tk.Label(box, text="Логин:", bg='#FFFFFF').grid(row=0, column=0, sticky='e', pady=10)
        self.login_var = tk.StringVar()
        tk.Entry(box, textvariable=self.login_var, width=25, relief='solid', bd=1, bg='#FFFFFF').grid(row=0, column=1, pady=10, ipady=3)

        tk.Label(box, text="Пароль:", bg='#FFFFFF').grid(row=1, column=0, sticky='e', pady=10)
        self.pwd_var = tk.StringVar()
        tk.Entry(box, textvariable=self.pwd_var, show='*', width=25, relief='solid', bd=1, bg='#FFFFFF').grid(row=1, column=1, pady=10, ipady=3)

        btn = tk.Button(box, text="Войти", command=self.do_login,
                        bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                        font=("Arial", 10), relief='solid', bd=1, padx=20, pady=3)
        btn.grid(row=2, column=0, columnspan=2, pady=20)

        tk.Label(outer,
                  text=("Тестовые учётные записи:\n"
                        "guard/guard — Дежурный охранник\n"
                        "hr/hr — Специалист отдела кадров\n"
                        "sysadmin/sysadmin — Системный администратор"),
                  bg='#FFFFFF', fg='#777777', justify="center").pack(pady=15)

    def do_login(self):
        op = AuthService.login(self.login_var.get().strip(), self.pwd_var.get().strip())
        if not op:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            return
        self.app.on_login(op)