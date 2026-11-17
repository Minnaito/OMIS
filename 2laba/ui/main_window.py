import tkinter as tk
from tkinter import ttk
from ui.event_monitor import EventMonitorFrame
from ui.card_holder import CardHolderWindow
from ui.guest_pass import GuestPassFrame
from ui.employees import EmployeesFrame
from ui.access_levels import AccessLevelsFrame
from ui.report import ReportFrame
from ui.incidents import IncidentsFrame


class MainFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill='both', expand=True)

        self.menu_buttons = {}
        self._build_ui()
        self.show_monitor()

    def _build_ui(self):
        self.sidebar = tk.Frame(self, width=200, bg='#FAD2E1')
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="СКУД — меню", font=("Arial", 12, "bold"), bg='#FAD2E1', fg='#5A4A4D').pack(pady=20)

        role = self.app.operator['role']
        buttons = []

        buttons.append(("Монитор событий", self.show_monitor))
        if role in ['hr_specialist', 'system_admin']:
            buttons.append(("Картотека", self.open_employees))
        if role in ['security_guard', 'system_admin']:
            buttons.append(("Гостевые пропуска", self.open_guest_pass))
        if role in ['system_admin']:
            buttons.append(("Уровни доступа", self.open_levels))
        if role in ['hr_specialist', 'system_admin']:
            buttons.append(("Отчёты", self.open_report))
        if role in ['security_guard', 'system_admin']:
            buttons.append(("Журнал инцидентов", self.open_incidents))

        for text, cmd in buttons:
            btn = tk.Button(self.sidebar, text=text, relief='solid', bd=1, anchor='w',
                            bg='#FAD2E1', fg='#5A4A4D', font=("Arial", 10), padx=10, pady=8)
            btn.pack(fill='x', padx=5, pady=2)
            self.menu_buttons[text] = btn
            btn.config(command=lambda t=text, c=cmd: self._on_menu_click(t, c))

        logout_btn = tk.Button(self.sidebar, text="Выйти из системы", command=self.app.logout,
                               bg='#FFB7B2', fg='#333333', activebackground='#FF9A9E',
                               relief='solid', bd=1, font=("Arial", 10, "bold"))
        logout_btn.pack(side='bottom', fill='x', padx=10, pady=20)

        self.content_frame = tk.Frame(self, bg='#FFFFFF')
        self.content_frame.pack(side='left', fill='both', expand=True)

    def _on_menu_click(self, text, command):
        self._set_active(text)
        command()

    def _set_active(self, text):
        for name, btn in self.menu_buttons.items():
            btn.config(bg='#FAD2E1', font=("Arial", 10, "normal"), relief='solid')
        if text in self.menu_buttons:
            self.menu_buttons[text].config(bg='#FFB7B2', font=("Arial", 10, "bold"), relief='sunken')

    def _clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def show_monitor(self):
        self._set_active("Монитор событий")
        self._clear_content()
        self.monitor = EventMonitorFrame(self.content_frame, self.app)
        self.monitor.pack(fill='both', expand=True)

    def open_employees(self):
        self._set_active("Картотека")
        self._clear_content()
        self.emp_frame = EmployeesFrame(self.content_frame, self.app)
        self.emp_frame.pack(fill='both', expand=True)

    def open_guest_pass(self):
        self._set_active("Гостевые пропуска")
        self._clear_content()
        self.guest_pass_frame = GuestPassFrame(self.content_frame, self.app)
        self.guest_pass_frame.pack(fill='both', expand=True)

    def open_levels(self):
        self._set_active("Уровни доступа")
        self._clear_content()
        self.levels_frame = AccessLevelsFrame(self.content_frame, self.app)
        self.levels_frame.pack(fill='both', expand=True)

    def open_report(self):
        self._set_active("Отчёты")
        self._clear_content()
        self.report_frame = ReportFrame(self.content_frame, self.app)
        self.report_frame.pack(fill='both', expand=True)

    def open_incidents(self):
        self._set_active("Журнал инцидентов")
        self._clear_content()
        self.incidents_frame = IncidentsFrame(self.content_frame, self.app)
        self.incidents_frame.pack(fill='both', expand=True)

    def open_card_holder(self, card_number=None):
        CardHolderWindow(self.app.root, card_number)