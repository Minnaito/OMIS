import tkinter as tk
from tkinter import ttk, messagebox
from services import AdminService


class AccessLevelsFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#FFFFFF')
        self.app = app
        self.levels = []
        self.checked_state = {}
        self.point_zone_map = {}

        self._build_ui()
        self._load_levels()

    def _build_ui(self):
        header = tk.Frame(self, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text="Уровни доступа", bg='#FAD2E1', fg='#333333', font=("Arial", 11, "bold")).pack(
            side='left', padx=15)

        main_frame = tk.Frame(self, padx=20, pady=15, bg='#FFFFFF')
        main_frame.pack(fill='both', expand=True)

        cols_frame = tk.Frame(main_frame, bg='#FFFFFF')
        cols_frame.pack(fill='both', expand=True)

        left_col = tk.Frame(cols_frame, width=200, bg='#FFFFFF')
        left_col.pack(side='left', fill='y', padx=(0, 20))
        left_col.pack_propagate(False)

        tk.Label(left_col, text="Уровни доступа", bg='#FFFFFF', fg='#333333', font=("Arial", 10, "bold")).pack(
            anchor='w', pady=(0, 5))

        self.listbox = tk.Listbox(left_col, height=12, exportselection=False, bg='#FFFFFF', relief='solid', bd=1)
        self.listbox.pack(fill='x', pady=(0, 10))
        self.listbox.bind('<<ListboxSelect>>', self._on_level_select)

        btn_frame = tk.Frame(left_col, bg='#FFFFFF')
        btn_frame.pack(fill='x')
        tk.Button(btn_frame, text="+ Новый", command=self._add_level, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1).pack(side='left', expand=True, padx=(0, 2))
        tk.Button(btn_frame, text="- Удалить", command=self._delete_level, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1).pack(side='left', expand=True, padx=(2, 0))

        right_col = tk.Frame(cols_frame, bg='#FFFFFF')
        right_col.pack(side='left', fill='both', expand=True)

        pts_header = tk.Frame(right_col, bg='#FFFFFF')
        pts_header.pack(fill='x', pady=(0, 5))
        tk.Label(pts_header, text="Разрешённые точки доступа", bg='#FFFFFF', fg='#333333',
                 font=("Arial", 10, "bold")).pack(side='left')

        tk.Button(pts_header, text="+ Точка", command=self._add_point, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1).pack(side='right', padx=2)
        tk.Button(pts_header, text="- Точка", command=self._delete_point, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1).pack(side='right', padx=2)

        cols = ("chk", "name", "zone", "type")
        self.tree = ttk.Treeview(right_col, columns=cols, show='headings', height=8)
        self.tree.heading("chk", text="")
        self.tree.heading("name", text="Точка доступа")
        self.tree.heading("zone", text="Зона")
        self.tree.heading("type", text="Вход/выход")

        self.tree.column("chk", width=30, anchor='center')
        self.tree.column("name", width=200)
        self.tree.column("zone", width=150)
        self.tree.column("type", width=100)

        self.tree.pack(fill='both', expand=True, pady=(0, 15))
        self.tree.bind('<Button-1>', self._toggle_check)

        time_frame = tk.Frame(right_col, bg='#FFFFFF')
        time_frame.pack(fill='x', pady=5)

        tk.Label(time_frame, text="Временной интервал", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w')
        t_entry_frame = tk.Frame(time_frame, bg='#FFFFFF')
        t_entry_frame.pack(anchor='w', pady=(0, 10))

        self.time_start = tk.StringVar(value="08:00")
        self.time_end = tk.StringVar(value="19:00")
        tk.Entry(t_entry_frame, textvariable=self.time_start, width=10, relief='solid', bd=1).pack(side='left')
        tk.Label(t_entry_frame, text="—", bg='#FFFFFF').pack(side='left', padx=5)
        tk.Entry(t_entry_frame, textvariable=self.time_end, width=10, relief='solid', bd=1).pack(side='left')

        tk.Label(time_frame, text="Дни недели:", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w')
        self.days_var = tk.StringVar(value="пн вт ср чт пт")
        tk.Entry(time_frame, textvariable=self.days_var, width=30, relief='solid', bd=1).pack(anchor='w', pady=(0, 15))

        action_frame = tk.Frame(right_col, bg='#FFFFFF')
        action_frame.pack(anchor='w', pady=10)
        tk.Button(action_frame, text="Сохранить", command=self._save, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left', padx=(0, 10))
        tk.Button(action_frame, text="Отмена", command=self._cancel, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left')

    def _load_levels(self):
        self.levels = AdminService.get_access_levels()
        self.listbox.delete(0, tk.END)
        for l in self.levels:
            self.listbox.insert(tk.END, l['name'])
        if self.levels:
            self.listbox.selection_set(0)
            self._on_level_select()

    def _on_level_select(self, event=None):
        sel = self.listbox.curselection()
        if not sel: return

        level = self.levels[sel[0]]
        self.time_start.set(level.get('time_start') or "08:00")
        self.time_end.set(level.get('time_end') or "19:00")
        self.days_var.set(level.get('days') or "пн вт ср чт пт")
        self._load_points(level['id'])

    def _load_points(self, level_id):
        self.tree.delete(*self.tree.get_children())
        allowed_zones = {z['id'] for z in AdminService.get_zones_for_level(level_id)}
        points = AdminService.get_access_points()

        points.sort(key=lambda x: x['name'])
        self.checked_state = {}
        self.point_zone_map = {}

        for p in points:
            is_checked = p['zone_id'] in allowed_zones
            chk_char = "☑" if is_checked else "☐"
            iid = str(p['id'])
            self.tree.insert('', 'end', iid=iid, values=(chk_char, p['name'], p['zone_name'] or '', p['type'] or ''))
            self.checked_state[iid] = is_checked
            self.point_zone_map[iid] = p['zone_id']

    def _toggle_check(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == '#1':
                item = self.tree.identify_row(event.y)
                if item:
                    current = self.checked_state.get(item, False)
                    new_state = not current
                    self.checked_state[item] = new_state
                    self.tree.set(item, "chk", "☑" if new_state else "☐")

    def _add_level(self):
        dialog = tk.Toplevel(self)
        dialog.title("Новый уровень")
        dialog.geometry("300x150")
        dialog.configure(bg='#FFFFFF')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Название уровня:", bg='#FFFFFF').pack(pady=(15, 5))
        name_var = tk.StringVar()
        tk.Entry(dialog, textvariable=name_var, width=30, relief='solid', bd=1).pack()

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название!")
                return
            AdminService.add_access_level(name)
            dialog.destroy()
            self._load_levels()

        tk.Button(dialog, text="Добавить", command=save, bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                  relief='solid', bd=1).pack(pady=20)

    def _delete_level(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите уровень доступа")
            return

        level = self.levels[sel[0]]
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить уровень «{level['name']}»?"):
            success = AdminService.delete_access_level(level['id'])
            if success:
                messagebox.showinfo("Готово", "Уровень удален.")
                self._load_levels()
            else:
                messagebox.showerror("Ошибка", "Нельзя удалить этот уровень!\nОн назначен хотя бы одному пропуску.")

    def _add_point(self):
        dialog = tk.Toplevel(self)
        dialog.title("Новая точка доступа")
        dialog.geometry("350x300")
        dialog.configure(bg='#FFFFFF')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Название:", bg='#FFFFFF').pack(pady=(10, 5))
        name_var = tk.StringVar()
        tk.Entry(dialog, textvariable=name_var, width=30, relief='solid', bd=1).pack()

        tk.Label(dialog, text="Зона:", bg='#FFFFFF').pack(pady=(10, 5))
        zones = AdminService.get_zones()
        zone_var = tk.StringVar()
        zone_combo = ttk.Combobox(dialog, textvariable=zone_var, values=[z['name'] for z in zones], state='readonly')
        zone_combo.pack()
        if zones: zone_combo.current(0)

        tk.Label(dialog, text="Устройство:", bg='#FFFFFF').pack(pady=(10, 5))
        devices = AdminService.get_devices()
        dev_var = tk.StringVar()
        dev_combo = ttk.Combobox(dialog, textvariable=dev_var, values=[d['type'] for d in devices], state='readonly')
        dev_combo.pack()
        if devices: dev_combo.current(0)

        tk.Label(dialog, text="Тип (вход/выход):", bg='#FFFFFF').pack(pady=(10, 5))
        type_var = tk.StringVar(value="вход/выход")
        ttk.Combobox(dialog, textvariable=type_var, values=["вход", "выход", "вход/выход", "двунаправленная"],
                     state='readonly').pack()

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название!")
                return
            zone_id = next((z['id'] for z in zones if z['name'] == zone_var.get()), None)
            dev_id = next((d['id'] for d in devices if d['type'] == dev_var.get()), None)

            if not zone_id or not dev_id:
                messagebox.showerror("Ошибка", "Выберите зону и устройство!")
                return

            AdminService.add_access_point(name, zone_id, dev_id, type_var.get())
            dialog.destroy()

            sel = self.listbox.curselection()
            if sel:
                self._load_points(self.levels[sel[0]]['id'])

        tk.Button(dialog, text="Сохранить", command=save, bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                  relief='solid', bd=1).pack(pady=20)

    def _delete_point(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите точку доступа для удаления!")
            return

        point_id = int(sel[0])
        name = self.tree.item(sel[0], 'values')[1]

        if messagebox.askyesno("Подтверждение",
                               f"Удалить точку доступа «{name}»?\nВсе события этой точки также будут удалены!"):
            AdminService.delete_access_point(point_id)
            lvl_sel = self.listbox.curselection()
            if lvl_sel:
                self._load_points(self.levels[lvl_sel[0]]['id'])

    def _save(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите уровень доступа")
            return

        level_id = self.levels[sel[0]]['id']
        AdminService.update_access_level_details(level_id, self.time_start.get(), self.time_end.get(),
                                                 self.days_var.get())

        allowed_zones = set()
        for iid, is_checked in self.checked_state.items():
            if is_checked:
                zone_id = self.point_zone_map.get(iid)
                if zone_id:
                    allowed_zones.add(zone_id)

        AdminService.set_zones_for_level(level_id, list(allowed_zones))
        messagebox.showinfo("Готово", "Изменения сохранены!")

    def _cancel(self):
        self._on_level_select()