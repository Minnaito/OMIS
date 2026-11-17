import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from services import MonitoringService, AdminService
from ui.card_holder import CardHolderWindow
import database as db


class EventMonitorFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._after_id = None
        self.current_image = None
        self._build()
        self.refresh()

    def _build(self):
        header = tk.Frame(self, bg='#FAD2E1', pady=10)
        header.pack(fill='x')
        tk.Label(header, text=f"Монитор событий — оператор: {self.app.operator['full_name']}",
                 bg='#FAD2E1', fg='#5A4A4D', font=("Arial", 11, "bold")).pack(side='left', padx=10)

        filter_bar = tk.Frame(self, pady=5, bg='#FFF9FB')
        filter_bar.pack(fill='x', padx=10)

        tk.Label(filter_bar, text="Точка доступа:", bg='#FFF9FB', fg='#5A4A4D').pack(side='left')
        self.filter_point = ttk.Combobox(filter_bar, state='readonly', width=25)
        self.points_list = [("все", None)] + [(p['name'], p['id']) for p in AdminService.get_access_points()]
        self.filter_point['values'] = [p[0] for p in self.points_list]
        self.filter_point.set("все")
        self.filter_point.pack(side='left', padx=5)
        self.filter_point.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        tk.Label(filter_bar, text="Период: сегодня", bg='#FFF9FB', fg='#5A4A4D').pack(side='left', padx=20)

        search_frame = tk.Frame(filter_bar, bg='#FFF9FB')
        search_frame.pack(side='right')
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left')
        self.search_entry.insert(0, "Поиск...")
        self.search_entry.config(foreground="gray")

        def on_focus_in(event):
            if self.search_entry.get() == "Поиск...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(foreground="black")

        def on_focus_out(event):
            if self.search_entry.get() == "":
                self.search_entry.insert(0, "Поиск...")
                self.search_entry.config(foreground="gray")

        self.search_entry.bind("<FocusIn>", on_focus_in)
        self.search_entry.bind("<FocusOut>", on_focus_out)
        self.search_var.trace_add("write", lambda *args: self.refresh())

        cols = ("time", "holder", "point", "result")
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.heading("time", text="Время")
        self.tree.heading("holder", text="ФИО")
        self.tree.heading("point", text="Точка доступа")
        self.tree.heading("result", text="Результат")

        self.tree.column("time", width=160, anchor='center')
        self.tree.column("holder", width=250)
        self.tree.column("point", width=250)
        self.tree.column("result", width=150, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        self.tree.tag_configure('denied', background='#FFE4E1', foreground='#333333', font=('Arial', 9, 'bold'))
        self.tree.tag_configure('alarm', background='#FFE4E1', foreground='#333333', font=('Arial', 9, 'bold'))

        self.detail_frame = tk.Frame(self, bd=1, relief='solid', bg='#FFFFFF')
        self.detail_frame.pack(fill='x', padx=10, pady=10, side='bottom')

        self.photo_canvas = tk.Canvas(self.detail_frame, width=100, height=120, bg='#FFF9FB')
        self.photo_canvas.grid(row=0, column=0, rowspan=5, padx=20, pady=20)

        self.lbl_name = tk.Label(self.detail_frame, text="", bg='#FFFFFF', fg='#333333', font=("Arial", 12, "bold"))
        self.lbl_name.grid(row=0, column=1, sticky='w', pady=(20, 5))

        self.lbl_dept = tk.Label(self.detail_frame, text="", bg='#FFFFFF', fg='#5A4A4D', font=("Arial", 10))
        self.lbl_dept.grid(row=1, column=1, sticky='w', pady=2)

        self.lbl_pass = tk.Label(self.detail_frame, text="", bg='#FFFFFF', fg='#5A4A4D', font=("Arial", 10))
        self.lbl_pass.grid(row=2, column=1, sticky='w', pady=2)

        self.lbl_reason = tk.Label(self.detail_frame, text="", bg='#FFFFFF', fg='#5A4A4D', font=("Arial", 10))
        self.lbl_reason.grid(row=3, column=1, sticky='w', pady=2)

        self.btn_open = ttk.Button(self.detail_frame, text="Открыть карточку", command=self.open_card)
        self.btn_open.grid(row=4, column=1, sticky='w', pady=(10, 20))

        self.current_card_number = None

    def _get_point_filter(self):
        name = self.filter_point.get()
        for n, i in self.points_list:
            if n == name:
                return i
        return None

    def refresh(self):
        if not self.winfo_exists():
            return

        events = MonitoringService.get_events(self._get_point_filter())

        search_text = self.search_var.get().lower()
        if search_text == "поиск...":
            search_text = ""

        self.tree.delete(*self.tree.get_children())

        for ev in events:
            if search_text:
                searchable = f"{ev['holder_name']} {ev['point_name']} {ev['event_type']}".lower()
                if search_text not in searchable:
                    continue

            time_str = ev['timestamp']

            if ev['event_type'] == 'неизвестный пропуск':
                tag = 'alarm'
                res_text = "ТРЕВОГА"
            elif ev['result'] == 'отказ':
                tag = 'denied'
                res_text = "ОТКАЗ"
            else:
                tag = ''
                res_text = "разрешён"

            self.tree.insert('', 'end', iid=str(ev['id']),
                             values=(time_str, ev['holder_name'], ev['point_name'] or '', res_text),
                             tags=(tag,))

        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except:
                pass
        self._after_id = self.after(3000, self.refresh)

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return

        conn = db.get_connection()
        row = conn.execute("SELECT card_number, event_type FROM access_event WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()

        if not row or not row['card_number']:
            self._clear_details()
            return

        info = AdminService.get_pass_by_card(row['card_number'])

        if not info or not info['holder']:
            self._clear_details()
            self.lbl_name.config(text="Неизвестный")
            self.lbl_pass.config(text=f"Карта: {row['card_number']}")
            self.lbl_reason.config(text="Причина: карта не найдена в базе")
            self._draw_photo(None, "Неизвестно")
            return

        h = info['holder']
        self.current_card_number = info['card_number']
        self.lbl_name.config(text=h['full_name'])

        card_num_display = info['card_number']
        if card_num_display.startswith("EMP-"):
            card_num_display = card_num_display.replace("EMP-", "004")
        elif card_num_display.startswith("GUEST-"):
            card_num_display = card_num_display.replace("GUEST-", "00")

        if 'position' in h:
            self.lbl_dept.config(text=f"{h.get('department_name', '')} • {h.get('position', '')}")
            self.lbl_pass.config(
                text=f"Пропуск № {card_num_display} • {'активен' if info['active'] else 'заблокирован'}")
            self._draw_photo(h.get('photo'), h['full_name'])
        else:
            self.lbl_dept.config(text="Посетитель")
            self.lbl_pass.config(
                text=f"Пропуск № {card_num_display} • {'активен' if info['active'] else 'заблокирован'}")
            self._draw_photo(None, h['full_name'])

        if row['event_type'] == 'неизвестный пропуск':
            self.lbl_reason.config(text="Причина: неизвестная карта")
        elif row['event_type'] == 'нет прав доступа':
            self.lbl_reason.config(text="Причина отказа: зона запрещена уровнем доступа")
        elif row['event_type'] == 'пропуск заблокирован':
            self.lbl_reason.config(text="Причина отказа: пропуск заблокирован")
        else:
            self.lbl_reason.config(text="")

    def _draw_photo(self, photo_path, full_name=""):
        self.photo_canvas.delete("all")

        if not photo_path and full_name and full_name != "Неизвестно":
            last_name = full_name.split()[0].lower()
            if last_name.endswith('а') or last_name.endswith('я'):
                photo_path = "assets/female.png"
            else:
                photo_path = "assets/male.png"

        if photo_path:
            try:
                img = Image.open(photo_path)
                img = img.resize((100, 120), Image.Resampling.LANCZOS)
                self.current_image = ImageTk.PhotoImage(img)
                self.photo_canvas.create_image(0, 0, anchor='nw', image=self.current_image)
                return
            except Exception:
                pass

        self.photo_canvas.create_rectangle(5, 5, 95, 115, outline='gray')
        self.photo_canvas.create_text(50, 60, text="Фото", fill='gray')

    def _clear_details(self):
        self.current_card_number = None
        self.lbl_name.config(text="")
        self.lbl_dept.config(text="")
        self.lbl_pass.config(text="")
        self.lbl_reason.config(text="")
        self._draw_photo(None, "")

    def open_card(self):
        if self.current_card_number:
            win = CardHolderWindow(self.winfo_toplevel(), self.current_card_number)
            self.wait_window(win)

            if self.winfo_exists() and self.tree.winfo_exists():
                try:
                    self._on_select()
                except Exception:
                    pass