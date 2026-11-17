import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, Alignment
from services import MonitoringService, AdminService


class IncidentsFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#FFFFFF')
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg='#FAD2E1', pady=8)
        header.pack(fill='x')
        tk.Label(header, text="Журнал инцидентов и аудита", bg='#FAD2E1', fg='#333333',
                 font=("Arial", 11, "bold")).pack(side='left', padx=15)

        top = tk.Frame(self, pady=10, bg='#FFFFFF')
        top.pack(fill='x', padx=10)

        tk.Label(top, text="Тип:", bg='#FFFFFF').pack(side='left')
        self.type_var = tk.StringVar(value="все")
        type_combo = ttk.Combobox(top, textvariable=self.type_var, state='readonly', width=15,
                                  values=["все", "Тревога", "Отказ", "Аудит"])
        type_combo.pack(side='left', padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        tk.Label(top, text="Период:", bg='#FFFFFF').pack(side='left', padx=(15, 5))
        self.period_var = tk.StringVar(value="неделя")
        period_combo = ttk.Combobox(top, textvariable=self.period_var, state='readonly', width=15,
                                    values=["сутки", "неделя", "месяц"])
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>',
                          lambda e: self.refresh())

        cols = ("time", "type", "desc", "status")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=10)
        self.tree.heading("time", text="Время")
        self.tree.heading("type", text="Тип")
        self.tree.heading("desc", text="Описание")
        self.tree.heading("status", text="Статус")

        self.tree.column("time", width=100, anchor='center')
        self.tree.column("type", width=100, anchor='center')
        self.tree.column("desc", width=400)
        self.tree.column("status", width=150, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        self.tree.tag_configure('unprocessed', font=('Arial', 9, 'bold'))
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        tk.Label(self, text="Комментарий оператора", bg='#FFFFFF', fg='#666', font=("Arial", 8)).pack(anchor='w',
                                                                                                      padx=10,
                                                                                                      pady=(10, 0))
        self.comment_text = tk.Text(self, height=4, relief='solid', bd=1, font=("Arial", 10), bg='#FFFFFF')
        self.comment_text.pack(fill='x', padx=10, pady=(0, 10))

        btn_frame = tk.Frame(self, bg='#FFFFFF')
        btn_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(btn_frame, text="Пометить обработанным", command=self.mark, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left')
        tk.Button(btn_frame, text="Выгрузить журнал", command=self.export, bg='#FAD2E1', fg='#333333',
                  activebackground='#FFB7B2', relief='solid', bd=1, padx=10, pady=5).pack(side='left', padx=10)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.comment_text.delete("1.0", tk.END)

        inc_type = self.type_var.get()
        period = self.period_var.get()

        now = datetime.now()
        if period == "сутки":
            start_date = now - timedelta(days=1)
        elif period == "неделя":
            start_date = now - timedelta(days=7)
        else:
            start_date = now - timedelta(days=30)

        incidents = MonitoringService.get_incidents()

        for inc in incidents:
            if inc_type != "все" and inc.get('type') != inc_type:
                continue

            try:
                inc_date = datetime.strptime(inc['timestamp'].split(' ')[0], "%Y-%m-%d")
                if inc_date.date() < start_date.date():
                    continue
            except:
                pass

            time_str = inc['timestamp'].split(' ')[1] if ' ' in inc['timestamp'] else inc['timestamp']

            status = inc['status']
            if status == "новый":
                status = "не обработан"
                tag = 'unprocessed'
            else:
                tag = ''

            desc_text = inc['description'].replace("EMP-", "004")

            iid = str(inc['id'])
            self.tree.insert('', 'end', iid=iid, values=(
                time_str, inc.get('type', 'Тревога'), desc_text, status
            ), tags=(tag,))


    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel: return

        import database as db
        conn = db.get_connection()
        row = conn.execute("SELECT comment FROM incident WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()

        self.comment_text.delete("1.0", tk.END)
        if row and row['comment']:
            self.comment_text.insert("1.0", row['comment'])

    def mark(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите инцидент!")
            return

        comment = self.comment_text.get("1.0", tk.END).strip()
        AdminService.mark_incident_processed(int(sel[0]), comment)
        messagebox.showinfo("Готово", "Инцидент помечен как обработанный.")
        self.refresh()

    def export(self):
        if not self.tree.get_children():
            messagebox.showwarning("Внимание", "Журнал пуст, нечего выгружать.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel файл", "*.xlsx")],
            title="Выгрузить журнал в Excel"
        )
        if not path: return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Журнал инцидентов"

            headers = ["Время", "Тип", "Описание", "Статус"]
            ws.append(headers)

            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')

            for item in self.tree.get_children():
                row_data = self.tree.item(item, 'values')
                ws.append(row_data)

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
            messagebox.showinfo("Готово", f"Журнал успешно сохранён в Excel:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")