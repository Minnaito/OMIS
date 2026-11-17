import tkinter as tk
from tkinter import ttk, messagebox
import re
from services import AdminService


class EmployeesFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#FFFFFF')
        self.app = app
        self.depts = [{"id": None, "name": "Все"}] + AdminService.get_departments()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text="Картотека сотрудников", bg='#FAD2E1', fg='#333333', font=("Arial", 11, "bold")).pack(
            side='left', padx=15)

        top = tk.Frame(self, bg='#FFFFFF')
        top.pack(fill='x', padx=10, pady=10)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(top, textvariable=self.search_var, width=30, relief='solid', bd=1)
        self.search_entry.pack(side='left', padx=(0, 10))
        self.search_entry.insert(0, "Поиск по ФИО...")
        self.search_entry.config(foreground="gray")

        def on_focus_in(event):
            if self.search_entry.get() == "Поиск по ФИО...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(foreground="black")

        def on_focus_out(event):
            if self.search_entry.get() == "":
                self.search_entry.insert(0, "Поиск по ФИО...")
                self.search_entry.config(foreground="gray")

        self.search_entry.bind("<FocusIn>", on_focus_in)
        self.search_entry.bind("<FocusOut>", on_focus_out)
        self.search_var.trace_add("write", lambda *args: self.refresh())

        self.dept_var = tk.StringVar(value="Все")
        dept_combo = ttk.Combobox(top, textvariable=self.dept_var, state='readonly', width=25,
                                  values=[d['name'] for d in self.depts])
        dept_combo.pack(side='left', padx=10)
        self.dept_var.trace('w', lambda *a: self.refresh())

        tk.Button(top, text="+ Добавить", command=self.add, bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                  relief='solid', bd=1).pack(side='right')
        tk.Button(top, text="- Удалить", command=self.delete, bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                  relief='solid', bd=1).pack(side='right', padx=10)

        cols = ("fio", "num", "dept", "pass")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=15)
        self.tree.heading("fio", text="ФИО")
        self.tree.heading("num", text="Таб. №")
        self.tree.heading("dept", text="Подразделение")
        self.tree.heading("pass", text="Пропуск")

        self.tree.column("fio", width=300)
        self.tree.column("num", width=100, anchor='center')
        self.tree.column("dept", width=250)
        self.tree.column("pass", width=150, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        self.footer = tk.Label(self, text="", fg='#666', bg='#FFFFFF', font=("Arial", 9))
        self.footer.pack(anchor='w', padx=15, pady=5)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())

        search_text = self.search_var.get().lower()
        if search_text == "поиск по фио...": search_text = ""

        dept_id = None
        for d in self.depts:
            if d['name'] == self.dept_var.get():
                dept_id = d['id']
                break

        employees = AdminService.get_employees(dept_id)

        total = 0
        active_passes = 0

        for e in employees:
            if search_text and search_text not in e['full_name'].lower():
                continue

            total += 1
            pass_num = e.get('card_number') or "не выдан"

            if pass_num != "не выдан":
                active_passes += 1
                if pass_num.startswith("EMP-"):
                    pass_num = pass_num.replace("EMP-", "004")

            self.tree.insert('', 'end', iid=e['id'],
                             values=(e['full_name'], e['personnel_number'], e['department_name'] or '', pass_num))

        self.footer.config(text=f"Всего сотрудников: {total} • с активным пропуском: {active_passes}")

    def add(self):
        AddEmployeeDialog(self, self.refresh)

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите сотрудника для удаления!")
            return

        emp_id = int(sel[0])
        fio = self.tree.item(sel[0], 'values')[0]

        if messagebox.askyesno("Подтверждение",
                               f"Вы уверены, что хотите УДАЛИТЬ сотрудника {fio}?\nВсе его пропуска также будут удалены!"):
            AdminService.delete_employee(emp_id)
            messagebox.showinfo("Готово", "Сотрудник удален.")
            self.refresh()


class AddEmployeeDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Добавление сотрудника")
        self.geometry("480x320")
        self.resizable(False, False)
        self.configure(bg='#FFFFFF')
        self.transient(parent)
        self.grab_set()

        f = tk.Frame(self, bg='#FFFFFF')
        f.pack(fill='both', expand=True, padx=20, pady=20)
        f.columnconfigure(1, weight=1)

        self.vars = {}
        fields = [
            ("personnel_number", "Табельный номер:"),
            ("full_name", "ФИО:"),
            ("position", "Должность:"),
            ("card_number", "Номер карты:")
        ]

        for i, (k, lbl) in enumerate(fields):
            tk.Label(f, text=lbl, bg='#FFFFFF').grid(row=i, column=0, sticky='e', pady=5, padx=(0, 10))
            v = tk.StringVar()
            self.vars[k] = v
            tk.Entry(f, textvariable=v, relief='solid', bd=1).grid(row=i, column=1, sticky='ew', pady=5)

        self.depts = AdminService.get_departments()
        self.levels = AdminService.get_access_levels()

        row_idx = len(fields)

        tk.Label(f, text="Подразделение:", bg='#FFFFFF').grid(row=row_idx, column=0, sticky='e', pady=5, padx=(0, 10))
        self.dept_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self.dept_var, state='readonly',
                     values=[d['name'] for d in self.depts]).grid(row=row_idx, column=1, sticky='ew', pady=5)

        tk.Label(f, text="Уровень доступа:", bg='#FFFFFF').grid(row=row_idx + 1, column=0, sticky='e', pady=5,
                                                                padx=(0, 10))
        self.level_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self.level_var, state='readonly',
                     values=[l['name'] for l in self.levels]).grid(row=row_idx + 1, column=1, sticky='ew', pady=5)

        btn_frame = tk.Frame(f, bg='#FFFFFF')
        btn_frame.grid(row=row_idx + 2, column=0, columnspan=2, pady=15)

        tk.Button(btn_frame, text="Сохранить", command=self.save,
                  bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                  relief='solid', bd=1, padx=25, pady=5, font=("Arial", 10, "bold")).pack()

    def save(self):
        num = self.vars['personnel_number'].get().strip()
        fio = self.vars['full_name'].get().strip()
        card = self.vars['card_number'].get().strip().upper()

        if not fio:
            messagebox.showerror("Ошибка", "Введите ФИО!")
            return
        if len(fio.split()) < 2 or not re.match(r'^[А-Яа-яЁё\s-]+$', fio):
            messagebox.showerror("Ошибка",
                                 "ФИО должно состоять минимум из двух слов (Фамилия Имя) и содержать только буквы!")
            return

        if not num.isdigit() or len(num) < 3:
            messagebox.showerror("Ошибка", "Табельный номер должен состоять только из цифр (минимум 3 знака)!")
            return

        if len(card) < 4:
            messagebox.showerror("Ошибка", "Номер карты слишком короткий (минимум 4 символа)!")
            return

        if AdminService.get_pass_by_card(card):
            messagebox.showerror("Ошибка", f"Карта с номером '{card}' уже существует в системе!")
            return

        if not self.dept_var.get() or not self.level_var.get():
            messagebox.showerror("Ошибка", "Выберите подразделение и уровень доступа!")
            return

        try:
            dept = next((d['id'] for d in self.depts if d['name'] == self.dept_var.get()), None)
            lvl = next((l['id'] for l in self.levels if l['name'] == self.level_var.get()), None)

            AdminService.add_employee(num, fio, self.vars['position'].get().strip(), dept, 1, card, lvl)
            self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))