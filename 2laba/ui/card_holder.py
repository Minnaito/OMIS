import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from datetime import datetime, date
from services import AdminService


class CardHolderWindow(tk.Toplevel):
    def __init__(self, parent, card_number=None):
        super().__init__(parent)
        self.geometry("850x650")
        self.configure(bg='#FFFFFF')
        self.card_number = card_number
        self.info = None
        self.tree = None
        self.current_photo = None

        if card_number:
            self._load_data()
        else:
            messagebox.showerror("Ошибка", "Номер карты не передан")
            self.destroy()

    def _load_data(self):
        self.info = AdminService.get_pass_by_card(self.card_number)
        if not self.info or not self.info['holder']:
            messagebox.showerror("Ошибка", f"Карта {self.card_number} не найдена или не назначена")
            self.destroy()
            return

        self.holder = self.info['holder']
        self.title("Карточка владельца пропуска")
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text=f"Карточка: {self.holder['full_name']}",
                 bg='#FAD2E1', fg='#333333', font=("Arial", 12, "bold")).pack(side='left', padx=15)

        main_frame = tk.Frame(self, padx=20, pady=15, bg='#FFFFFF')
        main_frame.pack(fill='both', expand=True)

        top_part = tk.Frame(main_frame, bg='#FFFFFF')
        top_part.pack(fill='x')

        photo_frame = tk.Frame(top_part, bg='#FFFFFF')
        photo_frame.pack(side='left', padx=(0, 20))

        self.photo_canvas = tk.Canvas(photo_frame, width=120, height=160, bg='#FFFFFF', highlightthickness=1,
                                      highlightbackground="#ccc")
        self.photo_canvas.pack()

        self._display_photo(self.holder.get('photo'))

        if 'personnel_number' in self.holder:
            btn_photo = tk.Button(photo_frame, text="Загрузить фото", command=self._upload_photo,
                                  bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2', relief='solid', bd=1)
            btn_photo.pack(pady=5)

        fields_frame = tk.Frame(top_part, bg='#FFFFFF')
        fields_frame.pack(side='left', fill='both', expand=True)

        if 'position' in self.holder:
            fields = [
                ("ФИО", self.holder['full_name']),
                ("Табельный номер", self.holder['personnel_number']),
                ("Подразделение", self.holder.get('department_name', '')),
                ("Должность", self.holder.get('position', '')),
                ("График работы",
                 f"{self.holder.get('start_time', '')} - {self.holder.get('end_time', '')}, {self.holder.get('days', 'пн-пт')}")
            ]
        else:
            fields = [
                ("ФИО", self.holder['full_name']),
                ("Документ", self.holder.get('document', '')),
                ("Цель визита", self.holder.get('purpose', ''))
            ]

        for i, (label_text, value) in enumerate(fields):
            tk.Label(fields_frame, text=label_text, bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w',
                                                                                                     pady=(2, 0))
            ent = tk.Entry(fields_frame, relief='solid', bd=1, font=("Arial", 10), bg='#FFFFFF')
            ent.insert(0, value)
            ent.config(state='readonly')
            ent.pack(fill='x', pady=(0, 5))

        tk.Label(main_frame, text="Пропуска владельца", bg='#FFFFFF', fg='#333333', font=("Arial", 10, "bold")).pack(
            anchor='w', pady=(15, 5))

        cols = ("card", "type", "level", "status", "valid_to")
        self.tree = ttk.Treeview(main_frame, columns=cols, show='headings', height=5)
        self.tree.heading("card", text="Номер карты")
        self.tree.heading("type", text="Тип")
        self.tree.heading("level", text="Уровень доступа")
        self.tree.heading("status", text="Статус")
        self.tree.heading("valid_to", text="Действителен до")

        self.tree.column("card", width=140)
        self.tree.column("type", width=120)
        self.tree.column("level", width=200)
        self.tree.column("status", width=100)
        self.tree.column("valid_to", width=100)

        self.tree.pack(fill='both', expand=True, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        btn_frame = tk.Frame(main_frame, pady=15, bg='#FFFFFF')
        btn_frame.pack(fill='x', side='bottom')

        self.btn_block = tk.Button(btn_frame, text="Заблокировать пропуск", command=self._block_pass,
                                   bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2', relief='solid', bd=1,
                                   state='disabled')
        self.btn_block.pack(side='left', padx=(0, 10))

        btn_new = tk.Button(btn_frame, text="Выдать новый пропуск", command=self._issue_new_pass,
                            bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2', relief='solid', bd=1)
        btn_new.pack(side='left', padx=10)

        btn_close = tk.Button(btn_frame, text="Закрыть", command=self.destroy,
                              bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2', relief='solid', bd=1)
        btn_close.pack(side='right', padx=10)

        self._load_passes()

    def _display_photo(self, photo_path):
        self.photo_canvas.delete("all")

        if not photo_path:
            full_name = self.holder['full_name']
            last_name = full_name.split()[0].lower()
            if last_name.endswith('а') or last_name.endswith('я'):
                photo_path = "assets/female.png"
            else:
                photo_path = "assets/male.png"

        if photo_path:
            try:
                img = Image.open(photo_path)
                img = img.resize((120, 160), Image.Resampling.LANCZOS)
                self.current_photo = ImageTk.PhotoImage(img)
                self.photo_canvas.create_image(0, 0, anchor='nw', image=self.current_photo)
                return
            except Exception:
                pass

        self.photo_canvas.create_rectangle(10, 10, 110, 150, outline='gray', dash=(4, 4))
        self.photo_canvas.create_text(60, 80, text="ФОТО", fill='gray')

    def _upload_photo(self):
        file_path = filedialog.askopenfilename(
            title="Выберите фото",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            AdminService.update_photo(self.holder['id'], file_path)
            self.holder['photo'] = file_path
            self._display_photo(file_path)

    def _load_passes(self):
        self.tree.delete(*self.tree.get_children())
        passes = AdminService.get_passes_for_holder(self.info['holder_type'], self.info['holder_id'])

        first_active_id = None
        for p in passes:
            card_num = p['card_number']
            if card_num.startswith("EMP-"):
                card_num = card_num.replace("EMP-", "004")

            iid = self.tree.insert('', 'end', iid=str(p['id']),
                                   values=(card_num, p['type'], p['level_name'] or '',
                                           "активен" if p['active'] else "заблокирован",
                                           p['valid_to'] or ''))
            if p['active'] and not first_active_id:
                first_active_id = iid

        if first_active_id:
            self.tree.selection_set(first_active_id)
            self.tree.focus(first_active_id)
            self._on_select()
        else:
            self.btn_block.config(state='disabled')

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if sel:
            values = self.tree.item(sel[0], 'values')
            self.btn_block.config(state='normal' if values[3] == "активен" else 'disabled')
        else:
            self.btn_block.config(state='disabled')

    def _block_pass(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Подтверждение", "Заблокировать выбранный пропуск?"):
            AdminService.set_pass_active(int(sel[0]), False)
            self._load_passes()
            messagebox.showinfo("Готово", "Пропуск заблокирован.")

    def _issue_new_pass(self):
        dialog = tk.Toplevel(self)
        dialog.title("Новый пропуск")
        dialog.geometry("350x380")
        dialog.configure(bg='#FFFFFF')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Номер карты:", bg='#FFFFFF').pack(pady=(15, 5))
        card_var = tk.StringVar()
        tk.Entry(dialog, textvariable=card_var, width=30, relief='solid', bd=1).pack()

        tk.Label(dialog, text="Тип пропуска:", bg='#FFFFFF').pack(pady=(10, 5))
        type_var = tk.StringVar(value="постоянный")
        ttk.Combobox(dialog, textvariable=type_var, values=["постоянный", "временный"], state='readonly').pack()

        tk.Label(dialog, text="Уровень доступа:", bg='#FFFFFF').pack(pady=(10, 5))
        levels = AdminService.get_access_levels()
        level_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=level_var, values=[l['name'] for l in levels], state='readonly').pack()

        tk.Label(dialog, text="Действителен до (ГГГГ-ММ-ДД):", bg='#FFFFFF').pack(pady=(10, 5))
        valid_var = tk.StringVar(value="2030-12-31")
        tk.Entry(dialog, textvariable=valid_var, relief='solid', bd=1).pack()

        def save():
            card = card_var.get().strip().upper()
            date_str = valid_var.get().strip()

            if not card:
                messagebox.showerror("Ошибка", "Введите номер карты!")
                return
            if len(card) < 4:
                messagebox.showerror("Ошибка",
                                     "Номер карты слишком короткий!\nМинимум 4 символа (например: 1234 или EMP-100).")
                return
            if AdminService.get_pass_by_card(card):
                messagebox.showerror("Ошибка", f"Карта с номером '{card}' уже существует в системе!")
                return

            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты!\nИспользуйте ГГГГ-ММ-ДД (например: 2030-12-31)")
                return

            if parsed_date < date.today():
                messagebox.showerror("Ошибка", "Дата окончания не может быть в прошлом!")
                return

            lvl = next((l['id'] for l in levels if l['name'] == level_var.get()), None)
            if not lvl:
                messagebox.showerror("Ошибка", "Выберите уровень доступа")
                return

            try:
                AdminService.add_new_pass(card, self.info['holder_type'], self.info['holder_id'],
                                          type_var.get(), lvl, date_str)
                self._load_passes()
                dialog.destroy()
                messagebox.showinfo("Готово", "Пропуск выдан")
            except Exception as e:
                messagebox.showerror("Ошибка базы данных", str(e))

        btn_save = tk.Button(dialog, text="Сохранить", command=save,
                             bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2', relief='solid', bd=1)
        btn_save.pack(pady=15)