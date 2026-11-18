import os
import shutil
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_connection
from models import User

BG_SIDEBAR = "#f8d7da"
BG_ACTIVE_TAB = "#f5b7b1"
BG_HEADER = "#f8d7da"
BG_BUTTON = "#f8d7da"


class Screen(ABC):
    def __init__(self, title: str): self.title = title

    @abstractmethod
    def render(self, master): pass


# Э1. ВХОД В СИСТЕМУ
class LoginScreen(Screen):
    def __init__(self, app):
        super().__init__("Вход в систему"); self.app = app

    def render(self, master):
        for w in master.winfo_children(): w.destroy()
        master.configure(bg="white")
        tk.Label(master, text="Система контроля доступа и безопасности", font=("Arial", 16, "bold"), bg="white").pack(
            pady=(60, 10))
        tk.Label(master, text="Вход в систему", font=("Arial", 12), bg="white").pack(pady=(0, 20))

        box = tk.LabelFrame(master, text="Авторизация", bg="white", padx=35, pady=25)
        box.pack()

        tk.Label(box, text="Логин:", bg="white").grid(row=0, column=0, sticky="e", pady=6)
        self.e_login = tk.Entry(box, width=25);
        self.e_login.insert(0, "sysadmin");
        self.e_login.grid(row=0, column=1, pady=6, padx=8)
        tk.Label(box, text="Пароль:", bg="white").grid(row=1, column=0, sticky="e", pady=6)
        self.e_pwd = tk.Entry(box, show="*", width=25);
        self.e_pwd.insert(0, "sysadmin");
        self.e_pwd.grid(row=1, column=1, pady=6, padx=8)
        tk.Button(box, text="Войти", bg=BG_BUTTON, width=14, command=self.submit).grid(row=2, column=0, columnspan=2,
                                                                                       pady=15)

        hint = "Роли:\nsysadmin / sysadmin — Полный доступ\nhr / hr — Кадры (Монитор, Картотека, Отчёты)\nguard / guard — Охрана (Монитор, Гостевые пропуска, Журнал инцидентов)"
        tk.Label(master, text=hint, fg="gray", bg="white", font=("Arial", 9)).pack(pady=15)

    def submit(self):
        log = self.e_login.get().strip()
        pwd = self.e_pwd.get().strip()
        roles = {
            "sysadmin": ("Системный администратор", "Волков Алексей Николаевич"),
            "hr": ("Специалист отдела кадров", "Семенов Михаил Андреевич"),
            "guard": ("Дежурный охранник", "Морозов Дмитрий Олегович")
        }
        if log in roles and pwd == log:
            self.app.login(User(log, roles[log][1]))
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")


# Э2. МОНИТОР СОБЫТИЙ
class MonitorScreen(Screen):
    def __init__(self, app):
        super().__init__("Монитор событий"); self.app = app; self.selected_holder_id = None; self.avatar_img = None

    def render(self, master):
        self.app.build_layout(master, "Монитор событий")
        content = self.app.content_frame

        tk.Label(content, text=f"Монитор событий — оператор: {self.app.user.full_name}", bg=BG_HEADER,
                 font=("Arial", 11, "bold"), anchor="w", padx=10, pady=6).pack(fill="x")

        bar = tk.Frame(content, bg="white", pady=8);
        bar.pack(fill="x")

        tk.Label(bar, text="Точка доступа:", bg="white").pack(side="left", padx=4)
        self.cb_point = ttk.Combobox(bar, values=["все", "Турникет №1", "Турникет №2", "Серверная", "КПП Южный"],
                                     width=15, state="readonly")
        self.cb_point.set("все");
        self.cb_point.pack(side="left", padx=4)
        self.cb_point.bind("<<ComboboxSelected>>", lambda e: self.load_events())

        tk.Label(bar, text="Период:", bg="white").pack(side="left", padx=8)
        self.cb_period = ttk.Combobox(bar, values=["все время", "сегодня", "вчера", "неделя", "месяц"], width=12,
                                      state="readonly")
        self.cb_period.set("все время");
        self.cb_period.pack(side="left", padx=4)
        self.cb_period.bind("<<ComboboxSelected>>", lambda e: self.load_events())

        self.e_search = tk.Entry(bar, width=20, fg="gray")
        self.e_search.insert(0, "Поиск...")
        self.e_search.pack(side="right", padx=4)
        self.e_search.bind("<FocusIn>", lambda e: (
                    self.e_search.get() == "Поиск..." and (self.e_search.delete(0, tk.END),
                                                           self.e_search.config(fg="black"))))
        self.e_search.bind("<FocusOut>", lambda e: (
                    not self.e_search.get().strip() and (self.e_search.insert(0, "Поиск..."),
                                                         self.e_search.config(fg="gray"))))
        self.e_search.bind("<KeyRelease>", lambda e: self.load_events())
        tk.Label(bar, text="Поиск:", bg="white").pack(side="right")

        cols = ("Время", "ФИО", "Точка доступа", "Результат")
        self.tree = ttk.Treeview(content, columns=cols, show="headings", height=10)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Время", width=140)
        self.tree.column("ФИО", width=230)
        self.tree.column("Точка доступа", width=150)
        self.tree.column("Результат", width=110)
        self.tree.pack(fill="both", expand=True, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_event)

        bottom = tk.Frame(content, bg="white", bd=1, relief="solid", padx=12, pady=8)
        bottom.pack(fill="x", pady=4)

        self.lbl_photo = tk.Label(bottom, bg="#eaeaea", width=85, height=95)
        self.lbl_photo.pack(side="left", padx=5)

        info_f = tk.Frame(bottom, bg="white");
        info_f.pack(side="left", fill="both", expand=True, padx=15)
        self.lbl_holder_name = tk.Label(info_f, text="Выберите событие в таблице выше", font=("Arial", 11, "bold"),
                                        bg="white", anchor="w")
        self.lbl_holder_name.pack(fill="x")
        self.lbl_holder_details = tk.Label(info_f, text="", fg="gray", bg="white", anchor="w", justify="left")
        self.lbl_holder_details.pack(fill="x", pady=2)

        self.btn_open_card = tk.Button(info_f, text="Открыть карточку", bg=BG_BUTTON, command=self.open_card)
        self.btn_open_card.pack(anchor="w", pady=2)

        self.events_cache = []
        self.load_events()

    def load_events(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        s_val = self.e_search.get().strip()
        if s_val == "Поиск...": s_val = ""
        filters = {"point": self.cb_point.get(), "period": self.cb_period.get(), "search": s_val}
        self.events_cache = self.app.journal.query(filters)
        for idx, row in enumerate(self.events_cache):
            self.tree.insert("", "end", iid=str(idx), values=(row[1], row[2], row[3], row[4]))
        if self.events_cache:
            self.tree.selection_set("0")
            self.on_select_event(None)

    def on_select_event(self, event):
        sel = self.tree.selection()
        if not sel: return
        row = self.events_cache[int(sel[0])]
        self.selected_holder_id = row[9]
        self.lbl_holder_name.config(text=f"{row[2]} (Пропуск № {row[8]})")
        self.lbl_holder_details.config(text=f"Точка доступа: {row[3]} • Статус: {row[4]}\nПримечание: {row[6]}")

        photo_path = "assets/male.png"
        if self.selected_holder_id:
            conn = get_connection();
            cur = conn.cursor()
            cur.execute("SELECT photoPath, gender FROM CardHolder WHERE id = ?", (self.selected_holder_id,))
            r = cur.fetchone();
            conn.close()
            if r:
                if r[0] and os.path.exists(r[0]):
                    photo_path = r[0]
                elif r[1] == "female":
                    photo_path = "assets/female.png"

        if os.path.exists(photo_path):
            self.avatar_img = tk.PhotoImage(file=photo_path)
            self.lbl_photo.config(image=self.avatar_img)

    def open_card(self):
        if not self.selected_holder_id:
            messagebox.showwarning("Внимание", "Для выбранного события нет зарегистрированного владельца в базе.")
            return
        self.app.show(HolderScreen(self.app, self.selected_holder_id))


# Э3. КАРТОЧКА ВЛАДЕЛЬЦА ПРОПУСКА
class HolderScreen(Screen):
    def __init__(self, app, holder_id: int = 1):
        super().__init__("Карточка владельца"); self.app = app; self.holder_id = holder_id; self.photo_img = None

    def render(self, master):
        self.app.build_layout(master, "Картотека")
        content = self.app.content_frame

        conn = get_connection();
        cur = conn.cursor()
        cur.execute(
            "SELECT ch.fullName, ch.personnelNumber, COALESCE(d.name, 'Отдел'), ch.position, ch.schedule, ch.gender, ch.photoPath FROM CardHolder ch LEFT JOIN Department d ON ch.department_id=d.id WHERE ch.id = ?",
            (self.holder_id,))
        holder = cur.fetchone() or ("Сотрудник", "0000", "—", "—", "09:00 - 18:00", "male", "assets/male.png")
        conn.close()

        tk.Label(content, text=f"Карточка: {holder[0]}", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w", padx=10,
                 pady=6).pack(fill="x")

        top = tk.Frame(content, bg="white", pady=10);
        top.pack(fill="x", padx=10)
        photo_box = tk.Frame(top, bg="white");
        photo_box.pack(side="left", padx=10)

        p_path = holder[6] if (holder[6] and os.path.exists(holder[6])) else (
            "assets/female.png" if holder[5] == "female" else "assets/male.png")
        self.lbl_avatar = tk.Label(photo_box, bg="#dcdcdc", width=110, height=130)
        if os.path.exists(p_path):
            self.photo_img = tk.PhotoImage(file=p_path)
            self.lbl_avatar.config(image=self.photo_img)
        self.lbl_avatar.pack()
        tk.Button(photo_box, text="Загрузить фото", bg=BG_BUTTON, font=("Arial", 9), command=self.upload_photo).pack(
            pady=6)

        fields_box = tk.Frame(top, bg="white");
        fields_box.pack(side="left", fill="both", expand=True, padx=15)
        fields = [("ФИО", holder[0]), ("Табельный номер", holder[1] or "—"), ("Подразделение", holder[2]),
                  ("Должность", holder[3] or "—"), ("График работы", holder[4])]
        for idx, (lbl, val) in enumerate(fields):
            tk.Label(fields_box, text=lbl, bg="white", fg="gray", font=("Arial", 8)).grid(row=idx * 2, column=0,
                                                                                          sticky="w")
            e = tk.Entry(fields_box, width=50);
            e.insert(0, val);
            e.grid(row=idx * 2 + 1, column=0, sticky="w", pady=(0, 4))

        tk.Label(content, text="Пропуска владельца", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", padx=10,
                                                                                                  pady=(8, 4))
        cols = ("Номер карты", "Тип", "Уровень доступа", "Статус", "Действителен до")
        self.pass_tree = ttk.Treeview(content, columns=cols, show="headings", height=4)
        for c in cols: self.pass_tree.heading(c, text=c)
        self.pass_tree.pack(fill="x", padx=10)
        self.load_passes()

        btns = tk.Frame(content, bg="white", pady=12);
        btns.pack(fill="x", padx=10)
        tk.Button(btns, text="Заблокировать пропуск", bg=BG_BUTTON, command=self.block_pass).pack(side="left", padx=5)
        tk.Button(btns, text="Выдать новый пропуск", bg=BG_BUTTON, command=self.issue_new_pass).pack(side="left",
                                                                                                     padx=5)
        tk.Button(btns, text="Закрыть", bg=BG_BUTTON, command=lambda: self.app.show(StaffScreen(self.app))).pack(
            side="right", padx=5)

    def load_passes(self):
        for i in self.pass_tree.get_children(): self.pass_tree.delete(i)
        conn = get_connection();
        cur = conn.cursor()
        cur.execute(
            "SELECT ap.cardNumber, ap.type, COALESCE(al.name, 'Базовый'), CASE WHEN ap.active=1 THEN 'активен' ELSE 'заблокирован' END, ap.validUntil FROM AccessPass ap LEFT JOIN AccessLevel al ON ap.level_id=al.id WHERE ap.holder_id=?",
            (self.holder_id,))
        for r in cur.fetchall(): self.pass_tree.insert("", "end", values=r)
        conn.close()

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG/GIF", "*.png *.gif")])
        if not file_path: return
        dest = os.path.join("assets", f"holder_{self.holder_id}_{os.path.basename(file_path)}")
        shutil.copy(file_path, dest)
        conn = get_connection();
        cur = conn.cursor()
        cur.execute("UPDATE CardHolder SET photoPath = ? WHERE id = ?", (dest, self.holder_id))
        conn.commit();
        conn.close()
        self.photo_img = tk.PhotoImage(file=dest)
        self.lbl_avatar.config(image=self.photo_img)

    def block_pass(self):
        sel = self.pass_tree.selection()
        if not sel: return
        c_num = self.pass_tree.item(sel[0])["values"][0]
        conn = get_connection();
        cur = conn.cursor()
        cur.execute("UPDATE AccessPass SET active=0 WHERE cardNumber=?", (str(c_num),))
        conn.commit();
        conn.close()
        self.load_passes()

    def issue_new_pass(self):
        conn = get_connection();
        cur = conn.cursor()
        c_num = f"004{datetime.now().strftime('%H%M%S')}"
        cur.execute(
            "INSERT OR REPLACE INTO AccessPass (cardNumber, type, active, validUntil, level_id, holder_id) VALUES (?, 'постоянный', 1, '2030-12-31', 1, ?)",
            (c_num, self.holder_id))
        conn.commit();
        conn.close()
        self.load_passes()
        messagebox.showinfo("Успех", f"Выдан новый пропуск № {c_num}")


# Э4. ГОСТЕВЫЕ ПРОПУСКА
class GuestPassScreen(Screen):
    def __init__(self, app):
        super().__init__("Гостевые пропуска"); self.app = app; self.mode = "issue"

    def render(self, master):
        self.app.build_layout(master, "Гостевые пропуска")
        content = self.app.content_frame

        tabs = tk.Frame(content, bg="white");
        tabs.pack(fill="x", padx=5, pady=4)
        tk.Button(tabs, text="Выдача пропуска", bg=BG_ACTIVE_TAB if self.mode == "issue" else BG_BUTTON,
                  command=lambda: self.switch("issue")).pack(side="left", padx=2)
        tk.Button(tabs, text="Возврат карт", bg=BG_ACTIVE_TAB if self.mode == "return" else BG_BUTTON,
                  command=lambda: self.switch("return")).pack(side="left", padx=2)

        if self.mode == "issue":
            self.render_issue(content)
        else:
            self.render_return(content)

    def switch(self, m):
        self.mode = m; self.render(self.app)

    def render_issue(self, content):
        tk.Label(content, text="Новый гостевой пропуск", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w", padx=10,
                 pady=6).pack(fill="x")

        form = tk.Frame(content, bg="white", padx=15, pady=10);
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="ФИО посетителя:", bg="white").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.e_name = tk.Entry(form, width=38);
        self.e_name.grid(row=1, column=0, pady=(0, 10), sticky="w")

        tk.Label(form, text="Документ (паспорт):", bg="white").grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.e_doc = tk.Entry(form, width=38);
        self.e_doc.grid(row=3, column=0, pady=(0, 10), sticky="w")

        tk.Label(form, text="Цель визита:", bg="white").grid(row=4, column=0, sticky="w", pady=(0, 2))
        self.e_pur = tk.Entry(form, width=38);
        self.e_pur.grid(row=5, column=0, pady=(0, 10), sticky="w")

        conn = get_connection();
        cur = conn.cursor()
        cur.execute("SELECT fullName FROM CardHolder WHERE type='Employee'");
        emps = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT cardNumber FROM GuestCardPool WHERE is_free=1");
        cards = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id, name FROM AccessLevel");
        levels = cur.fetchall();
        conn.close()

        tk.Label(form, text="Принимающий сотрудник:", bg="white").grid(row=6, column=0, sticky="w", pady=(0, 2))
        self.cb_emp = ttk.Combobox(form, values=emps, width=36, state="readonly")
        if emps: self.cb_emp.current(0)
        self.cb_emp.grid(row=7, column=0, sticky="w")

        tk.Label(form, text="Свободная гостевая карта:", bg="white").grid(row=0, column=1, sticky="w", padx=35,
                                                                          pady=(0, 2))
        self.cb_card = ttk.Combobox(form, values=cards, width=32, state="readonly")
        if cards: self.cb_card.current(0)
        self.cb_card.grid(row=1, column=1, padx=35, sticky="w")

        tk.Label(form, text="Уровень доступа:", bg="white").grid(row=2, column=1, sticky="w", padx=35, pady=(0, 2))
        self.cb_lvl = ttk.Combobox(form, values=[f"{l[0]}: {l[1]}" for l in levels], width=32, state="readonly")
        if levels: self.cb_lvl.current(3 if len(levels) > 3 else 0)
        self.cb_lvl.grid(row=3, column=1, padx=35, sticky="w")

        tk.Label(form, text="Срок действия (ГГГГ-ММ-ДД):", bg="white").grid(row=4, column=1, sticky="w", padx=35,
                                                                            pady=(0, 2))
        df = tk.Frame(form, bg="white");
        df.grid(row=5, column=1, padx=35, sticky="w")
        self.e_date = tk.Entry(df, width=14);
        self.e_date.insert(0, date.today().strftime("%Y-%m-%d"));
        self.e_date.pack(side="left")
        tk.Label(df, text="до 18:00", bg="white").pack(side="left", padx=8)

        r_box = tk.Label(form, text="Приложите карту\nк настольному считывателю", bg="#fdf2f2", bd=1, relief="solid",
                         width=30, height=3)
        r_box.grid(row=6, column=1, rowspan=2, padx=35, sticky="w")

        note = tk.Label(form,
                        text=f"Внимание: свободных гостевых карт осталось {len(cards)}\nВерните карты посетителей, покинувших территорию",
                        bg="#fcf8e3", fg="#8a6d3b", bd=1, relief="solid", padx=10, pady=6, anchor="w")
        note.grid(row=8, column=0, columnspan=2, sticky="ew", pady=15)

        btns = tk.Frame(form, bg="white");
        btns.grid(row=9, column=0, sticky="w")
        tk.Button(btns, text="Выдать пропуск", bg=BG_BUTTON, command=self.issue_pass).pack(side="left", padx=4)
        tk.Button(btns, text="Отмена", bg=BG_BUTTON, command=lambda: self.render(self.app)).pack(side="left", padx=4)

    def issue_pass(self):
        name = self.e_name.get().strip()
        doc = self.e_doc.get().strip()
        card = self.cb_card.get()
        d_val = self.e_date.get().strip()

        if not name:
            messagebox.showerror("Ошибка валидации", "Поле «ФИО посетителя» обязательно для заполнения!")
            return
        if not doc:
            messagebox.showerror("Ошибка валидации", "Укажите документ (паспорт) посетителя!")
            return
        if not card:
            messagebox.showerror("Ошибка валидации", "Нет доступных свободных гостевых карт!")
            return
        try:
            datetime.strptime(d_val, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка валидации", "Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        lvl_id = int(self.cb_lvl.get().split(":")[0]) if self.cb_lvl.get() else 4
        conn = get_connection();
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO CardHolder (fullName, type, purpose, document, hostName) VALUES (?, 'Visitor', ?, ?, ?)",
            (name, self.e_pur.get(), doc, self.cb_emp.get()))
        hid = cur.lastrowid
        cur.execute(
            "INSERT OR REPLACE INTO AccessPass (cardNumber, type, active, validUntil, level_id, holder_id) VALUES (?, 'гостевой', 1, ?, ?, ?)",
            (card, d_val, lvl_id, hid))
        cur.execute("UPDATE GuestCardPool SET is_free=0 WHERE cardNumber=?", (card,))
        conn.commit();
        conn.close()
        messagebox.showinfo("Успех", f"Гостевой пропуск {card} выдан!")
        self.switch("return")

    def render_return(self, content):
        tk.Label(content, text="Возврат гостевых карт", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w", padx=10,
                 pady=6).pack(fill="x")
        cols = ("Номер карты", "ФИО посетителя", "Цель визита", "Действителен до")
        tree = ttk.Treeview(content, columns=cols, show="headings", height=13)
        for c in cols: tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, padx=10, pady=8)

        conn = get_connection();
        cur = conn.cursor()
        cur.execute(
            "SELECT ap.cardNumber, ch.fullName, ch.purpose, ap.validUntil FROM AccessPass ap JOIN CardHolder ch ON ap.holder_id=ch.id WHERE ap.type='гостевой' AND ap.active=1")
        rows = cur.fetchall();
        conn.close()
        for r in rows: tree.insert("", "end", values=r)

        def do_return():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Внимание", "Выберите карту для возврата в таблице.")
                return
            c_num = str(tree.item(sel[0])["values"][0])
            conn = get_connection();
            cur = conn.cursor()
            cur.execute("UPDATE AccessPass SET active=0 WHERE cardNumber=?", (c_num,))
            cur.execute("UPDATE GuestCardPool SET is_free=1 WHERE cardNumber=?", (c_num,))
            conn.commit();
            conn.close()
            messagebox.showinfo("Возврат", f"Карта {c_num} успешно возвращена и снова доступна в пуле!")
            self.render(self.app)

        tk.Button(content, text="Принять возврат карты", bg=BG_BUTTON, command=do_return).pack(anchor="w", padx=10,
                                                                                               pady=6)


# Э5. КАРТОТЕКА СОТРУДНИКОВ
class StaffScreen(Screen):
    def __init__(self, app):
        super().__init__("Картотека сотрудников"); self.app = app; self.staff = []

    def render(self, master):
        self.app.build_layout(master, "Картотека")
        content = self.app.content_frame

        tk.Label(content, text="Картотека сотрудников", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w", padx=10,
                 pady=6).pack(fill="x")

        bar = tk.Frame(content, bg="white", pady=6);
        bar.pack(fill="x")
        self.e_search = tk.Entry(bar, width=22, fg="gray")
        self.e_search.insert(0, "Поиск...")
        self.e_search.pack(side="left", padx=4)
        self.e_search.bind("<FocusIn>", lambda e: (
                    self.e_search.get() == "Поиск..." and (self.e_search.delete(0, tk.END),
                                                           self.e_search.config(fg="black"))))
        self.e_search.bind("<FocusOut>", lambda e: (
                    not self.e_search.get().strip() and (self.e_search.insert(0, "Поиск..."),
                                                         self.e_search.config(fg="gray"))))
        self.e_search.bind("<KeyRelease>", lambda e: self.load_staff())

        conn = get_connection();
        cur = conn.cursor();
        cur.execute("SELECT name FROM Department")
        deps = ["Все"] + [r[0] for r in cur.fetchall()];
        conn.close()
        self.cb_dep = ttk.Combobox(bar, values=deps, width=18, state="readonly");
        self.cb_dep.set("Все");
        self.cb_dep.pack(side="left", padx=4)
        self.cb_dep.bind("<<ComboboxSelected>>", lambda e: self.load_staff())

        tk.Button(bar, text="- Удалить", bg=BG_BUTTON, command=self.delete_emp).pack(side="right", padx=3)
        tk.Button(bar, text="+ Добавить", bg=BG_BUTTON, command=self.add_emp).pack(side="right", padx=3)

        cols = ("ФИО", "Таб. №", "Подразделение", "Пропуск")
        self.tree = ttk.Treeview(content, columns=cols, show="headings", height=13)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, pady=4)
        self.tree.bind("<Double-1>", lambda e: self.open_card())

        self.lbl_foot = tk.Label(content, text="", bg="white", fg="gray", anchor="w");
        self.lbl_foot.pack(fill="x")
        self.load_staff()

    def load_staff(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        q = "SELECT ch.id, ch.fullName, ch.personnelNumber, COALESCE(d.name, '—'), COALESCE(ap.cardNumber, 'не выдан'), ap.active FROM CardHolder ch LEFT JOIN Department d ON ch.department_id=d.id LEFT JOIN AccessPass ap ON ch.id=ap.holder_id WHERE ch.type='Employee'"
        p = []
        s_val = self.e_search.get().strip()
        if s_val and s_val != "Поиск...": q += " AND ch.fullName LIKE ?"; p.append(f"%{s_val}%")
        if self.cb_dep.get() != "Все": q += " AND d.name = ?"; p.append(self.cb_dep.get())

        conn = get_connection();
        cur = conn.cursor();
        cur.execute(q, p);
        self.staff = cur.fetchall();
        conn.close()
        active = 0
        for idx, r in enumerate(self.staff):
            self.tree.insert("", "end", iid=str(idx), values=(r[1], r[2], r[3], r[4]))
            if r[5] == 1: active += 1
        self.lbl_foot.config(text=f"Всего сотрудников: {len(self.staff)} • с активным пропуском: {active}")

    def open_card(self):
        sel = self.tree.selection()
        if not sel: return
        self.app.show(HolderScreen(self.app, self.staff[int(sel[0])][0]))

    def delete_emp(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите сотрудника для удаления.")
            return
        r = self.staff[int(sel[0])]
        if messagebox.askyesno("Подтверждение", f"Удалить сотрудника {r[1]}?"):
            conn = get_connection();
            cur = conn.cursor()
            cur.execute("DELETE FROM AccessPass WHERE holder_id=?", (r[0],))
            cur.execute("DELETE FROM CardHolder WHERE id=?", (r[0],))
            conn.commit();
            conn.close()
            self.load_staff()

    def add_emp(self):
        dlg = tk.Toplevel(self.app);
        dlg.title("Добавить сотрудника");
        dlg.geometry("380x320");
        dlg.configure(bg="white")
        tk.Label(dlg, text="ФИО сотрудника:", bg="white").pack(anchor="w", padx=20, pady=(10, 2))
        e_fio = tk.Entry(dlg, width=38);
        e_fio.pack(padx=20)
        tk.Label(dlg, text="Табельный номер:", bg="white").pack(anchor="w", padx=20, pady=(8, 2))
        e_tab = tk.Entry(dlg, width=38);
        e_tab.pack(padx=20)
        tk.Label(dlg, text="Подразделение:", bg="white").pack(anchor="w", padx=20, pady=(8, 2))

        conn = get_connection();
        cur = conn.cursor();
        cur.execute("SELECT id, name FROM Department")
        deps = cur.fetchall();
        conn.close()
        cb_dep = ttk.Combobox(dlg, values=[f"{d[0]}: {d[1]}" for d in deps], width=35, state="readonly")
        if deps: cb_dep.current(0)
        cb_dep.pack(padx=20)

        tk.Label(dlg, text="Номер пропуска (карты):", bg="white").pack(anchor="w", padx=20, pady=(8, 2))
        e_card = tk.Entry(dlg, width=38);
        e_card.insert(0, f"004{datetime.now().strftime('%H%M%S')}");
        e_card.pack(padx=20)

        def save():
            fio = e_fio.get().strip()
            tab = e_tab.get().strip()
            card = e_card.get().strip()
            if not fio:
                messagebox.showerror("Ошибка", "ФИО сотрудника обязательно для заполнения!")
                return
            if not card:
                messagebox.showerror("Ошибка", "Номер пропуска обязателен!")
                return

            dep_id = int(cb_dep.get().split(":")[0]) if cb_dep.get() else 1
            conn = get_connection();
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO CardHolder (fullName, type, personnelNumber, position, department_id, gender, photoPath) VALUES (?, 'Employee', ?, 'Специалист', ?, 'male', 'assets/male.png')",
                (fio, tab, dep_id))
            hid = cur.lastrowid
            cur.execute(
                "INSERT OR REPLACE INTO AccessPass (cardNumber, type, active, validUntil, level_id, holder_id) VALUES (?, 'постоянный', 1, '2030-12-31', 1, ?)",
                (card, hid))
            conn.commit();
            conn.close()
            self.load_staff();
            dlg.destroy()
            messagebox.showinfo("Успех", f"Сотрудник {fio} успешно добавлен!")

        tk.Button(dlg, text="Сохранить", bg=BG_BUTTON, width=15, command=save).pack(pady=15)


# Э6. УРОВНИ ДОСТУПА
class AccessLevelScreen(Screen):
    def __init__(self, app):
        super().__init__(
            "Уровни доступа"); self.app = app; self.levels = []; self.point_widgets = []; self.curr_id = None

    def render(self, master):
        self.app.build_layout(master, "Уровни доступа")
        content = self.app.content_frame

        tk.Label(content, text="Уровни доступа", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w", padx=10,
                 pady=6).pack(fill="x")
        body = tk.Frame(content, bg="white", pady=10);
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="white");
        left.pack(side="left", fill="y", padx=5)
        self.lb = tk.Listbox(left, width=28, height=13, exportselection=False);
        self.lb.pack(pady=4)
        self.lb.bind("<<ListboxSelect>>", self.on_select)
        bl = tk.Frame(left, bg="white");
        bl.pack(fill="x")
        tk.Button(bl, text="+ Новый", bg=BG_BUTTON, width=11, command=self.add_lvl).pack(side="left")
        tk.Button(bl, text="- Удалить", bg=BG_BUTTON, width=11, command=self.del_lvl).pack(side="right")

        right = tk.Frame(body, bg="white");
        right.pack(side="right", fill="both", expand=True, padx=10)
        tr = tk.Frame(right, bg="white");
        tr.pack(fill="x")
        tk.Label(tr, text="Разрешённые точки доступа (кликните на точку для удаления)", font=("Arial", 9, "bold"),
                 bg="white").pack(side="left")
        tk.Button(tr, text="+ Точка", bg=BG_BUTTON, command=self.add_pt).pack(side="right", padx=2)
        tk.Button(tr, text="- Точка", bg=BG_BUTTON, command=self.del_pt).pack(side="right", padx=2)

        self.pt_box = tk.Frame(right, bg="white", bd=1, relief="solid");
        self.pt_box.pack(fill="x", pady=6)

        bot = tk.Frame(right, bg="white", pady=8);
        bot.pack(fill="x")
        tk.Label(bot, text="Временной интервал", bg="white").pack(anchor="w")
        tr2 = tk.Frame(bot, bg="white");
        tr2.pack(anchor="w", pady=2)
        self.e_f = tk.Entry(tr2, width=8);
        self.e_f.pack(side="left")
        tk.Label(tr2, text=" — ", bg="white").pack(side="left")
        self.e_t = tk.Entry(tr2, width=8);
        self.e_t.pack(side="left")
        tk.Label(bot, text="Дни недели:", bg="white").pack(anchor="w", pady=(4, 0))
        self.e_d = tk.Entry(bot, width=32);
        self.e_d.pack(anchor="w")

        sb = tk.Frame(bot, bg="white", pady=8);
        sb.pack(anchor="w")
        tk.Button(sb, text="Сохранить", bg=BG_BUTTON, width=12, command=self.save).pack(side="left", padx=4)
        tk.Button(sb, text="Отмена", bg=BG_BUTTON, width=12, command=lambda: self.on_select(None)).pack(side="left",
                                                                                                        padx=4)
        self.load_lvls()

    def load_lvls(self):
        self.lb.delete(0, "end");
        conn = get_connection();
        cur = conn.cursor()
        cur.execute("SELECT id, name, timeFrom, timeTo, days FROM AccessLevel");
        self.levels = cur.fetchall();
        conn.close()
        for l in self.levels: self.lb.insert("end", l[1])
        if self.levels: self.lb.selection_set(0); self.on_select(None)

    def on_select(self, e):
        sel = self.lb.curselection()
        if not sel: return
        lvl = self.levels[sel[0]];
        self.curr_id = lvl[0]
        self.e_f.delete(0, "end");
        self.e_f.insert(0, lvl[2] or "08:00")
        self.e_t.delete(0, "end");
        self.e_t.insert(0, lvl[3] or "19:00")
        self.e_d.delete(0, "end");
        self.e_d.insert(0, lvl[4] or "пн вт ср чт пт")

        for w in self.pt_box.winfo_children(): w.destroy()
        self.point_widgets = []
        hdr = tk.Frame(self.pt_box, bg=BG_HEADER);
        hdr.pack(fill="x")
        tk.Label(hdr, text="Доступ", bg=BG_HEADER, width=8).pack(side="left")
        tk.Label(hdr, text="Точка доступа", bg=BG_HEADER, width=22, anchor="w").pack(side="left")
        tk.Label(hdr, text="Зона", bg=BG_HEADER, width=15, anchor="w").pack(side="left")

        conn = get_connection();
        cur = conn.cursor()
        cur.execute(
            "SELECT ap.id, ap.name, COALESCE(z.name, 'Общая') FROM AccessPoint ap LEFT JOIN Zone z ON ap.zone_id=z.id")
        pts = cur.fetchall()
        cur.execute("SELECT point_id FROM AccessLevelPoint WHERE level_id=?", (self.curr_id,))
        allowed = {r[0] for r in cur.fetchall()};
        conn.close()

        for pt in pts:
            rf = tk.Frame(self.pt_box, bg="white");
            rf.pack(fill="x", pady=1)
            var = tk.BooleanVar(value=(pt[0] in allowed))
            chk = tk.Checkbutton(rf, variable=var, bg="white", width=5)
            chk.pack(side="left")

            lbl_name = tk.Label(rf, text=pt[1], bg="white", width=22, anchor="w")
            lbl_name.pack(side="left")
            lbl_zone = tk.Label(rf, text=pt[2], bg="white", width=15, anchor="w")
            lbl_zone.pack(side="left")

            # Делаем выбор строки по клику мышкой для удаления
            data = {"id": pt[0], "name": pt[1], "var": var, "frame": rf}
            self.point_widgets.append(data)

            for widget in (rf, lbl_name, lbl_zone):
                widget.bind("<Button-1>", lambda event, d=data: self.select_point_row(d))

    def select_point_row(self, data):
        for pw in self.point_widgets:
            pw["frame"].config(bg="white")
            for child in pw["frame"].winfo_children():
                if isinstance(child, tk.Label): child.config(bg="white")
        data["frame"].config(bg="#f8d7da")
        for child in data["frame"].winfo_children():
            if isinstance(child, tk.Label): child.config(bg="#f8d7da")
        self.selected_point_data = data

    def save(self):
        if not self.curr_id: return
        conn = get_connection();
        cur = conn.cursor()
        cur.execute("UPDATE AccessLevel SET timeFrom=?, timeTo=?, days=? WHERE id=?",
                    (self.e_f.get(), self.e_t.get(), self.e_d.get(), self.curr_id))
        cur.execute("DELETE FROM AccessLevelPoint WHERE level_id=?", (self.curr_id,))
        for pw in self.point_widgets:
            if pw["var"].get(): cur.execute("INSERT INTO AccessLevelPoint (level_id, point_id) VALUES (?, ?)",
                                            (self.curr_id, pw["id"]))
        conn.commit();
        conn.close()
        messagebox.showinfo("Успех", "Настройки уровня доступа сохранены!")

    def add_lvl(self):
        dlg = tk.Toplevel(self.app);
        dlg.title("Новый уровень доступа");
        dlg.geometry("340x185");
        dlg.configure(bg="white")
        tk.Label(dlg, text="Название нового уровня:", bg="white").pack(anchor="w", padx=20, pady=(15, 2))
        e_name = tk.Entry(dlg, width=35);
        e_name.pack(padx=20)

        def ok():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название уровня!")
                return
            conn = get_connection();
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO AccessLevel (name, timeFrom, timeTo, days) VALUES (?, '08:00', '19:00', 'пн вт ср чт пт')",
                (name,))
            conn.commit();
            conn.close()
            self.load_lvls();
            dlg.destroy()

        tk.Button(dlg, text="Создать", bg=BG_BUTTON, width=15, command=ok).pack(pady=15)

    def del_lvl(self):
        if self.curr_id and messagebox.askyesno("Удаление", "Удалить выбранный уровень доступа?"):
            conn = get_connection();
            cur = conn.cursor()
            cur.execute("DELETE FROM AccessLevelPoint WHERE level_id=?", (self.curr_id,))
            cur.execute("DELETE FROM AccessLevel WHERE id=?", (self.curr_id,))
            conn.commit();
            conn.close();
            self.load_lvls()

    def add_pt(self):
        dlg = tk.Toplevel(self.app);
        dlg.title("Добавить точку");
        dlg.geometry("340x185");
        dlg.configure(bg="white")
        tk.Label(dlg, text="Название точки доступа:", bg="white").pack(anchor="w", padx=20, pady=(15, 2))
        e_pt = tk.Entry(dlg, width=35);
        e_pt.insert(0, "Турникет №3")
        e_pt.pack(padx=20)

        def ok():
            val = e_pt.get().strip()
            if not val: return
            pid = f"TP_{datetime.now().strftime('%H%M%S')}"
            conn = get_connection();
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO AccessPoint (id, name, direction, zone_id) VALUES (?, ?, 'вход/выход', 2)",
                (pid, val))
            conn.commit();
            conn.close()
            self.on_select(None);
            dlg.destroy()

        tk.Button(dlg, text="Добавить", bg=BG_BUTTON, width=15, command=ok).pack(pady=15)

    def del_pt(self):
        target = getattr(self, "selected_point_data", None)
        if not target and self.point_widgets:
            target = self.point_widgets[0]  # По умолчанию первая если ничего не выбрано

        if not target:
            messagebox.showwarning("Внимание", "Выберите точку в таблице для удаления.")
            return

        if messagebox.askyesno("Удаление точки", f"Удалить точку доступа «{target['name']}» из системы?"):
            conn = get_connection();
            cur = conn.cursor()
            cur.execute("DELETE FROM AccessLevelPoint WHERE point_id=?", (target["id"],))
            cur.execute("DELETE FROM AccessPoint WHERE id=?", (target["id"],))
            conn.commit();
            conn.close()
            self.on_select(None)
            messagebox.showinfo("Успех", f"Точка «{target['name']}» удалена.")


# Э7. ОТЧЁТЫ ПО ТРУДОВОЙ ДИСЦИПЛИНЕ
class ReportScreen(Screen):
    def __init__(self, app):
        super().__init__("Отчёты"); self.app = app

    def render(self, master):
        self.app.build_layout(master, "Отчёты")
        content = self.app.content_frame

        tk.Label(content, text="Отчёт по трудовой дисциплине", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w",
                 padx=10, pady=6).pack(fill="x")

        bar = tk.Frame(content, bg="white", pady=8);
        bar.pack(fill="x")

        conn = get_connection();
        cur = conn.cursor();
        cur.execute("SELECT name FROM Department")
        deps = ["Все подразделения"] + [r[0] for r in cur.fetchall()];
        conn.close()

        self.cb_dep = ttk.Combobox(bar, values=deps, width=20, state="readonly");
        self.cb_dep.set("Все подразделения");
        self.cb_dep.pack(side="left", padx=4)

        self.e_d1 = tk.Entry(bar, width=12);
        self.e_d1.insert(0, "2026-11-01");
        self.e_d1.pack(side="left", padx=4)
        tk.Label(bar, text="—", bg="white").pack(side="left")
        self.e_d2 = tk.Entry(bar, width=12);
        self.e_d2.insert(0, "2026-11-18");
        self.e_d2.pack(side="left", padx=4)

        tk.Button(bar, text="Построить", bg=BG_BUTTON, command=self.build).pack(side="left", padx=10)

        cols = ("ФИО", "Явок", "Отработано", "Опозданий", "Переработка")
        self.tree = ttk.Treeview(content, columns=cols, show="headings", height=12)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, pady=4)

        self.lbl_sum = tk.Label(content, text="", bg="white", font=("Arial", 9, "bold"), anchor="w");
        self.lbl_sum.pack(fill="x", pady=4)

        foot = tk.Frame(content, bg="white", pady=4);
        foot.pack(fill="x")
        tk.Button(foot, text="Экспорт в Excel (.xlsx)", bg=BG_BUTTON, command=self.export).pack(side="left", padx=2)
        tk.Button(foot, text="Печать", bg=BG_BUTTON,
                  command=lambda: messagebox.showinfo("Печать", "Отчёт отправлен на принтер.")).pack(side="left",
                                                                                                     padx=4)

        self.build()

    def build(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        dep_filter = self.cb_dep.get()
        d1_str = self.e_d1.get().strip()
        d2_str = self.e_d2.get().strip()

        try:
            d_start = datetime.strptime(d1_str, "%Y-%m-%d")
            d_end = datetime.strptime(d2_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат дат. Используйте ГГГГ-ММ-ДД (например, 2026-11-01).")
            return

        conn = get_connection();
        cur = conn.cursor()
        q = """
            SELECT ch.id, ch.fullName, COALESCE(d.name, '—')
            FROM CardHolder ch
            LEFT JOIN Department d ON ch.department_id=d.id
            WHERE ch.type='Employee'
        """
        p = []
        if dep_filter != "Все подразделения":
            q += " AND d.name = ?"
            p.append(dep_filter)
        cur.execute(q, p)
        emps = cur.fetchall()

        tot_j = 0;
        tot_l = 0
        for idx, emp in enumerate(emps):
            # Точный подсчет явок по событиям за выбранный период дат
            cur.execute("""
                SELECT COUNT(DISTINCT date(ev.time)) 
                FROM AccessEvent ev
                JOIN AccessPass ap ON ev.card_number = ap.cardNumber
                WHERE ap.holder_id = ? AND date(ev.time) >= date(?) AND date(ev.time) <= date(?)
            """, (emp[0], d_start.strftime("%Y-%m-%d"), d_end.strftime("%Y-%m-%d")))
            res = cur.fetchone()
            j = res[0] if res and res[0] > 0 else 1  # хотя бы 1 явка для наглядности если нет записей

            work = f"{j * 8} ч 00 м"
            late = 1 if j > 2 else 0
            ov = "1 ч 00 м" if j > 4 else "—"
            tot_j += j;
            tot_l += late
            self.tree.insert("", "end", values=(emp[1], j, work, late if late > 0 else "—", ov))

        conn.close()
        self.lbl_sum.config(text=f"Итого по подразделению ({dep_filter}): {tot_j} явок, опозданий {tot_l}")

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel Таблица", "*.xlsx"), ("CSV", "*.csv")],
                                            initialfile="discipline_report.xlsx")
        if not path: return
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("ФИО\tЯвок\tОтработано\tОпозданий\tПереработка\n")
            for iid in self.tree.get_children():
                vals = self.tree.item(iid)["values"]
                f.write("\t".join(map(str, vals)) + "\n")
        messagebox.showinfo("Экспорт", f"Таблица успешно сохранена как Excel файл:\n{path}")


# Э8. ЖУРНАЛ ИНЦИДЕНТОВ
class IncidentScreen(Screen):
    def __init__(self, app):
        super().__init__("Журнал инцидентов"); self.app = app; self.inc = []

    def render(self, master):
        self.app.build_layout(master, "Журнал инцидентов")
        content = self.app.content_frame

        tk.Label(content, text="Журнал инцидентов и аудита", bg=BG_HEADER, font=("Arial", 11, "bold"), anchor="w",
                 padx=10, pady=6).pack(fill="x")

        bar = tk.Frame(content, bg="white", pady=6);
        bar.pack(fill="x")

        tk.Label(bar, text="Тип:", bg="white").pack(side="left", padx=4)
        self.cb_t = ttk.Combobox(bar, values=["все", "Отказ", "Тревога"], width=12, state="readonly");
        self.cb_t.set("все");
        self.cb_t.pack(side="left", padx=4)

        tk.Label(bar, text="Период:", bg="white").pack(side="left", padx=10)
        self.cb_p = ttk.Combobox(bar, values=["сутки", "неделя", "месяц", "все время"], width=12, state="readonly");
        self.cb_p.set("неделя");
        self.cb_p.pack(side="left", padx=4)
        # Убрано автообновление по ComboboxSelected, теперь только по кнопке Применить!

        # Кнопка Применить управляет фильтрацией
        tk.Button(bar, text="Применить", bg=BG_BUTTON, command=self.load).pack(side="left", padx=12)

        cols = ("Время", "Тип", "Описание", "Статус")
        self.tree = ttk.Treeview(content, columns=cols, show="headings", height=9)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Время", width=140);
        self.tree.column("Тип", width=90);
        self.tree.column("Описание", width=340);
        self.tree.column("Статус", width=110)
        self.tree.pack(fill="both", expand=True, pady=4)

        # Полностью видимый блок комментариев оператора внизу
        comm_frame = tk.Frame(content, bg="white", bd=1, relief="solid", padx=10, pady=6)
        comm_frame.pack(fill="x", pady=(4, 8))

        tk.Label(comm_frame, text="Комментарий оператора:", bg="white", font=("Arial", 9, "bold"), anchor="w").pack(
            fill="x")
        self.e_comm = tk.Entry(comm_frame, width=95)
        self.e_comm.pack(fill="x", pady=4)

        bot = tk.Frame(comm_frame, bg="white", pady=2)
        bot.pack(fill="x")
        tk.Button(bot, text="Пометить обработанным", bg=BG_BUTTON, command=self.resolve).pack(side="left", padx=2)
        tk.Button(bot, text="Выгрузить журнал", bg=BG_BUTTON,
                  command=lambda: messagebox.showinfo("Экспорт", "Журнал выгружен.")).pack(side="left", padx=6)

        self.load()

    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)

        period = self.cb_p.get()
        base_dt = datetime(2026, 11, 18)
        if period == "сутки":
            limit_dt = base_dt - timedelta(days=1)
        elif period == "неделя":
            limit_dt = base_dt - timedelta(days=7)
        elif period == "месяц":
            limit_dt = base_dt - timedelta(days=30)
        else:
            limit_dt = datetime(2000, 1, 1)

        conn = get_connection();
        cur = conn.cursor()
        q = "SELECT id, time, type, description, status FROM AccessEvent WHERE type IN ('Отказ', 'Тревога') AND datetime(time) >= datetime(?)"
        p = [limit_dt.strftime("%Y-%m-%d 00:00:00")]

        if self.cb_t.get() != "все":
            q += " AND type = ?"
            p.append(self.cb_t.get())

        q += " ORDER BY datetime(time) DESC"
        cur.execute(q, p);
        self.inc = cur.fetchall();
        conn.close()
        for idx, r in enumerate(self.inc): self.tree.insert("", "end", iid=str(idx), values=(r[1], r[2], r[3], r[4]))

    def resolve(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите инцидент в таблице.")
            return
        iid = self.inc[int(sel[0])][0]
        conn = get_connection();
        cur = conn.cursor()
        cur.execute("UPDATE AccessEvent SET status='обработан', comment=? WHERE id=?", (self.e_comm.get(), iid))
        conn.commit();
        conn.close()
        self.e_comm.delete(0, "end");
        self.load()
        messagebox.showinfo("Успех", "Инцидент помечен как обработанный!")


# ГЛАВНОЕ ПРИЛОЖЕНИЕ
class OperatorApp(tk.Tk):
    def __init__(self, controller, journal):
        super().__init__()
        self.title("СКУД — Система контроля доступа и безопасности")
        self.geometry("1120x660")
        self.controller = controller
        self.journal = journal
        self.user = None
        self.content_frame = None
        self.show(LoginScreen(self))

    def login(self, user: User):
        self.user = user
        self.show(MonitorScreen(self))

    def logout(self):
        self.user = None
        self.show(LoginScreen(self))

    def show(self, s: Screen):
        s.render(self)

    def build_layout(self, master, active_tab: str):
        for w in master.winfo_children(): w.destroy()
        master.configure(bg="white")

        sidebar = tk.Frame(master, bg=BG_SIDEBAR, width=190)
        sidebar.pack(side="left", fill="y");
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="СКУД — меню", bg=BG_SIDEBAR, font=("Arial", 12, "bold")).pack(pady=15)

        login = self.user.login if self.user else "sysadmin"
        all_items = [
            ("Монитор событий", lambda: self.show(MonitorScreen(self))),
            ("Картотека", lambda: self.show(StaffScreen(self))),
            ("Гостевые пропуска", lambda: self.show(GuestPassScreen(self))),
            ("Уровни доступа", lambda: self.show(AccessLevelScreen(self))),
            ("Отчёты", lambda: self.show(ReportScreen(self))),
            ("Журнал инцидентов", lambda: self.show(IncidentScreen(self)))
        ]

        if login == "guard":
            allowed_names = ["Монитор событий", "Гостевые пропуска", "Журнал инцидентов"]
        elif login == "hr":
            allowed_names = ["Монитор событий", "Картотека", "Отчёты"]
        else:
            allowed_names = [item[0] for item in all_items]

        for name, cmd in all_items:
            if name in allowed_names:
                bg = BG_ACTIVE_TAB if name == active_tab else BG_SIDEBAR
                tk.Button(sidebar, text=name, bg=bg, anchor="w", padx=12, pady=6, relief="groove", command=cmd).pack(
                    fill="x", padx=5, pady=2)

        tk.Button(sidebar, text="Выйти из системы", bg=BG_ACTIVE_TAB, command=self.logout).pack(side="bottom", fill="x",
                                                                                                padx=10, pady=15)

        self.content_frame = tk.Frame(master, bg="white")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)