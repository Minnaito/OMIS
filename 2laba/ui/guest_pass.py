import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import re
from services import AdminService


class GuestPassFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#FFFFFF')
        self.app = app
        self.card_map = {}
        self.host_map = {}
        self.level_map = {}

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        self.tab_issue = tk.Frame(self.notebook, bg='#FFFFFF')
        self.tab_return = tk.Frame(self.notebook, bg='#FFFFFF')

        self.notebook.add(self.tab_issue, text="Выдача пропуска")
        self.notebook.add(self.tab_return, text="Возврат карт")

        self._build_issue_tab()
        self._build_return_tab()
        self._update_data()

    def _build_issue_tab(self):
        header = tk.Frame(self.tab_issue, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text="Новый гостевой пропуск", bg='#FAD2E1', fg='#333333', font=("Arial", 11, "bold")).pack(
            side='left', padx=15)

        main_frame = tk.Frame(self.tab_issue, padx=20, pady=15, bg='#FFFFFF')
        main_frame.pack(fill='both', expand=True)

        cols_frame = tk.Frame(main_frame, bg='#FFFFFF')
        cols_frame.pack(fill='x')

        left_col = tk.Frame(cols_frame, bg='#FFFFFF')
        left_col.pack(side='left', fill='x', expand=True, padx=(0, 20))

        self.fio_var = tk.StringVar()
        self.doc_var = tk.StringVar()
        self.purpose_var = tk.StringVar()
        self.host_var = tk.StringVar()

        self._add_field(left_col, "ФИО посетителя", self.fio_var)
        self._add_field(left_col, "Документ", self.doc_var)
        self._add_field(left_col, "Цель визита", self.purpose_var)

        tk.Label(left_col, text="Принимающий сотрудник", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w',
                                                                                                          pady=(5, 0))
        self.host_combo = ttk.Combobox(left_col, textvariable=self.host_var, state='readonly')
        self.host_combo.pack(fill='x', pady=(0, 5))

        right_col = tk.Frame(cols_frame, bg='#FFFFFF')
        right_col.pack(side='left', fill='x', expand=True)

        tk.Label(right_col, text="Свободная гостевая карта", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(
            anchor='w', pady=(5, 0))
        self.card_var = tk.StringVar()
        self.card_combo = ttk.Combobox(right_col, textvariable=self.card_var, state='readonly')
        self.card_combo.pack(fill='x', pady=(0, 10))

        tk.Label(right_col, text="Уровень доступа", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w',
                                                                                                     pady=(5, 0))
        self.level_var = tk.StringVar()
        self.level_combo = ttk.Combobox(right_col, textvariable=self.level_var, state='readonly')
        self.level_combo.pack(fill='x', pady=(0, 10))

        tk.Label(right_col, text="Срок действия", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w',
                                                                                                   pady=(5, 0))
        date_frame = tk.Frame(right_col, bg='#FFFFFF')
        date_frame.pack(fill='x', pady=(0, 10))

        self.date_var = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        tk.Entry(date_frame, textvariable=self.date_var, width=15, relief='solid', bd=1).pack(side='left')
        tk.Label(date_frame, text="до", bg='#FFFFFF').pack(side='left', padx=5)
        self.time_var = tk.StringVar(value="18:00")
        tk.Entry(date_frame, textvariable=self.time_var, width=10, relief='solid', bd=1).pack(side='left')

        card_frame = tk.Frame(right_col, bd=1, relief='solid', bg='#FFF9FB', pady=15)
        card_frame.pack(fill='x', pady=(15, 0))
        tk.Label(card_frame, text="Приложите карту", bg='#FFF9FB', fg='#555', font=("Arial", 10, "bold")).pack()
        tk.Label(card_frame, text="к настольному считывателю", bg='#FFF9FB', fg='#888', font=("Arial", 8)).pack()

        bottom_frame = tk.Frame(main_frame, pady=20, bg='#FFFFFF')
        bottom_frame.pack(fill='x', side='bottom')

        self.info_frame = tk.Frame(bottom_frame, bd=1, relief='solid', bg='#FFF9FB', padx=15, pady=10)
        self.info_frame.pack(fill='x', pady=(0, 15))

        self.lbl_warning = tk.Label(self.info_frame, text="", bg='#FFF9FB', font=("Arial", 9, "bold"))
        self.lbl_warning.pack(anchor='w')
        tk.Label(self.info_frame, text="Верните карты посетителей, покинувших территорию", bg='#FFF9FB', fg='#666',
                 font=("Arial", 8)).pack(anchor='w')

        btn_frame = tk.Frame(bottom_frame, bg='#FFFFFF')
        btn_frame.pack(anchor='w')

        tk.Button(btn_frame, text="Выдать пропуск", command=self.issue, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left', padx=(0, 10))
        tk.Button(btn_frame, text="Отмена", command=self.clear_form, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left')

    def _build_return_tab(self):
        header = tk.Frame(self.tab_return, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text="Возврат гостевых карт", bg='#FAD2E1', fg='#333333', font=("Arial", 11, "bold")).pack(
            side='left', padx=15)

        main_frame = tk.Frame(self.tab_return, padx=20, pady=15, bg='#FFFFFF')
        main_frame.pack(fill='both', expand=True)

        tk.Label(main_frame, text="Гости, находящиеся на территории:", bg='#FFFFFF', fg='#333333',
                 font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 10))

        cols = ("card", "fio", "doc", "purpose", "host", "valid")
        self.return_tree = ttk.Treeview(main_frame, columns=cols, show='headings', height=10)
        self.return_tree.heading("card", text="Карта")
        self.return_tree.heading("fio", text="ФИО посетителя")
        self.return_tree.heading("doc", text="Документ")
        self.return_tree.heading("purpose", text="Цель визита")
        self.return_tree.heading("host", text="Принимающий")
        self.return_tree.heading("valid", text="Действителен до")

        self.return_tree.column("card", width=60, anchor='center')
        self.return_tree.column("fio", width=180)
        self.return_tree.column("doc", width=130)
        self.return_tree.column("purpose", width=150)
        self.return_tree.column("host", width=150)
        self.return_tree.column("valid", width=140)

        self.return_tree.pack(fill='both', expand=True, pady=(0, 15))

        tk.Button(main_frame, text="Вернуть выбранную карту", command=self._return_card, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(anchor='w')

    def _add_field(self, parent, label_text, var):
        tk.Label(parent, text=label_text, bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w', pady=(5, 0))
        ent = tk.Entry(parent, textvariable=var, relief='solid', bd=1, font=("Arial", 10), bg='#FFFFFF')
        ent.pack(fill='x', pady=(0, 5))

    def _update_data(self):
        cards = AdminService.get_free_guest_cards()
        self.card_map = {}
        display_values = []

        def extract_num(card_obj):
            try:
                return int(card_obj['card_number'].split('-')[-1])
            except:
                return 0

        cards.sort(key=extract_num)

        for c in cards:
            num = c['card_number'].split('-')[-1]
            display = str(num)
            self.card_map[display] = c['card_number']
            display_values.append(display)

        self.card_combo['values'] = display_values
        if display_values: self.card_combo.current(0)

        if display_values:
            self.lbl_warning.config(text=f"Внимание: свободных гостевых карт осталось {len(display_values)}",
                                    fg='#333333')
        else:
            self.card_combo.set("")
            self.lbl_warning.config(text="Внимание: свободных гостевых карт нет!", fg='red')

        employees = AdminService.get_employees()
        self.host_map = {f"{e['full_name']} ({e['department_name']})": e['full_name'] for e in employees}
        self.host_combo['values'] = list(self.host_map.keys())
        if self.host_combo['values']: self.host_combo.current(0)

        levels = AdminService.get_access_levels()
        self.level_map = {l['name']: l['id'] for l in levels}
        guest_levels = [name for name in self.level_map.keys() if "Гостевой" in name]
        self.level_combo['values'] = guest_levels
        if guest_levels:
            self.level_var.set(guest_levels[0])

        self.return_tree.delete(*self.return_tree.get_children())
        for p in AdminService.get_active_guest_passes():
            card_num = p['card_number'].split('-')[-1]
            self.return_tree.insert('', 'end', iid=p['card_number'], values=(
                card_num, p['full_name'], p['document'] or '—',
                p['purpose'] or '—', p['host_employee'] or '—', p['valid_to'] or '—'
            ))

    def clear_form(self):
        self.fio_var.set("")
        self.doc_var.set("")
        self.purpose_var.set("")

    def issue(self):
        fio = self.fio_var.get().strip()
        doc = self.doc_var.get().strip()
        purpose = self.purpose_var.get().strip()
        host = self.host_map.get(self.host_var.get(), self.host_var.get())
        card = self.card_map.get(self.card_var.get())
        level_id = self.level_map.get(self.level_var.get())

        if not fio:
            messagebox.showerror("Ошибка", "Введите ФИО посетителя!")
            return
        if len(fio.split()) < 2 or not re.match(r'^[А-Яа-яЁё\s-]+$', fio):
            messagebox.showerror("Ошибка",
                                 "ФИО должно состоять минимум из двух слов (Фамилия Имя) и содержать только буквы!")
            return

        if len(doc) < 5:
            messagebox.showerror("Ошибка",
                                 "Документ слишком короткий. Введите серию и номер (например: паспорт MP 123456).")
            return

        if len(purpose) < 5:
            messagebox.showerror("Ошибка", "Укажите цель визита подробнее (минимум 5 символов).")
            return

        if not card or not level_id:
            messagebox.showerror("Ошибка", "Выберите карту и уровень доступа!")
            return

        try:
            d, m, y = self.date_var.get().split('.')
            valid_date = datetime.strptime(f"{y}-{m}-{d}", "%Y-%m-%d").date()
            if valid_date < date.today():
                messagebox.showerror("Ошибка", "Дата окончания не может быть в прошлом!")
                return
            valid_to = f"{y}-{m}-{d} {self.time_var.get()}"
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ДД.ММ.ГГГГ")
            return

        AdminService.issue_guest_pass(fio, doc, purpose, host, card, level_id, valid_to)
        messagebox.showinfo("Готово", f"Пропуск № {self.card_var.get()} успешно выдан!\nПосетитель: {fio}")

        self.clear_form()
        self._update_data()

    def _return_card(self):
        sel = self.return_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите гостя из списка")
            return

        card_number = sel[0]
        fio = self.return_tree.item(sel[0], 'values')[1]

        if messagebox.askyesno("Подтверждение", f"Подтверждаете возврат карты от гостя {fio}?"):
            AdminService.return_guest_card(card_number)
            messagebox.showinfo("Готово", "Карта возвращена в фонд свободных карт.")
            self._update_data()