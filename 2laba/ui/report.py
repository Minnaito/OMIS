import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
import openpyxl
from openpyxl.styles import Font, Alignment
from services import TimeTrackingService, AdminService


def format_minutes(total_min):
    if not total_min or total_min <= 0:
        return "—"
    hours = total_min // 60
    mins = total_min % 60
    return f"{hours} ч {mins} м"


class ReportFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#FFFFFF')
        self.app = app
        self.depts = [{"id": None, "name": "Все"}] + AdminService.get_departments()
        self.report_data = []
        self._build_ui()
        self.build()

    def _build_ui(self):
        header = tk.Frame(self, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text="Отчёт по трудовой дисциплине", bg='#FAD2E1', fg='#333333',
                 font=("Arial", 11, "bold")).pack(side='left', padx=15)

        top = tk.Frame(self, bg='#FFFFFF')
        top.pack(fill='x', padx=10, pady=10)

        self.dept_var = tk.StringVar(value="Все")
        dept_combo = ttk.Combobox(top, textvariable=self.dept_var, state='readonly', width=25,
                                  values=[d['name'] for d in self.depts])
        dept_combo.pack(side='left', padx=(0, 10))
        dept_combo.bind('<<ComboboxSelected>>', lambda e: self.build())

        self.date_from = tk.StringVar(value=(date.today() - timedelta(days=7)).strftime("%d.%m.%Y"))
        tk.Entry(top, textvariable=self.date_from, width=12, relief='solid', bd=1).pack(side='left')
        tk.Label(top, text="—", bg='#FFFFFF').pack(side='left', padx=5)

        self.date_to = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        tk.Entry(top, textvariable=self.date_to, width=12, relief='solid', bd=1).pack(side='left', padx=(0, 10))

        tk.Button(top, text="Построить", command=self.build, bg='#FAD2E1', fg='#333333', activebackground='#FFB7B2',
                  relief='solid', bd=1).pack(side='left')

        cols = ("fio", "days", "hours", "late", "overtime")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=15)
        self.tree.heading("fio", text="ФИО")
        self.tree.heading("days", text="Явок")
        self.tree.heading("hours", text="Отработано")
        self.tree.heading("late", text="Опозданий")
        self.tree.heading("overtime", text="Переработка")

        self.tree.column("fio", width=250)
        self.tree.column("days", width=80, anchor='center')
        self.tree.column("hours", width=150, anchor='center')
        self.tree.column("late", width=100, anchor='center')
        self.tree.column("overtime", width=150, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        self.summary_frame = tk.Frame(self, bg='#FFFFFF')
        self.summary_frame.pack(fill='x', padx=10, pady=10)

        self.lbl_summary = tk.Label(self.summary_frame, text="", bg='#FFFFFF', fg='#333333', font=("Arial", 10, "bold"))
        self.lbl_summary.pack(anchor='w')

        btn_frame = tk.Frame(self.summary_frame, bg='#FFFFFF')
        btn_frame.pack(anchor='w', pady=(10, 0))

        tk.Button(btn_frame, text="Экспорт в XLSX", command=self.export, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left', padx=(0, 10))
        tk.Button(btn_frame, text="Печать", command=self.print_report, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left')

    def build(self):
        self.tree.delete(*self.tree.get_children())

        dept_id = None
        for d in self.depts:
            if d['name'] == self.dept_var.get():
                dept_id = d['id']
                break

        try:
            d1, m1, y1 = self.date_from.get().split('.')
            d2, m2, y2 = self.date_to.get().split('.')
            date_from = f"{y1}-{m1}-{d1}"
            date_to = f"{y2}-{m2}-{d2}"
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ДД.ММ.ГГГГ")
            return

        self.report_data = TimeTrackingService.build_discipline_report(dept_id, date_from, date_to)

        total_days = 0
        total_mins = 0
        total_late = 0

        for r in self.report_data:
            days = r['days']
            mins = r['total_min']
            late = r['late']

            total_days += days
            total_mins += mins
            total_late += late

            self.tree.insert('', 'end', values=(
                r['full_name'],
                days,
                format_minutes(mins),
                late if late > 0 else "—",
                format_minutes(r['overtime'] * 60) if r['overtime'] > 0 else "—"
            ))

        self.lbl_summary.config(
            text=f"Итого по подразделению: {total_days} явок, {format_minutes(total_mins)}, опозданий {total_late}")

    def export(self):
        if not self.report_data:
            messagebox.showwarning("Внимание", "Сначала постройте отчёт")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel файл", "*.xlsx")],
            title="Сохранить отчёт в Excel"
        )
        if not path: return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Отчет по дисциплине"

            headers = ["ФИО", "Явок", "Отработано", "Опозданий", "Переработка"]
            ws.append(headers)

            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')

            for r in self.report_data:
                ws.append([
                    r['full_name'],
                    r['days'],
                    format_minutes(r['total_min']),
                    r['late'],
                    format_minutes(r['overtime'] * 60) if r['overtime'] > 0 else "—"
                ])

            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width

            wb.save(path)
            messagebox.showinfo("Готово", f"Отчёт успешно сохранён в Excel:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def print_report(self):
        messagebox.showinfo("Печать", "Отчёт отправлен на печать (демонстрация).")