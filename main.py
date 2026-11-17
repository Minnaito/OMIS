import tkinter as tk
from tkinter import ttk
from database import init_db
from ui.login import LoginFrame
from ui.main_window import MainFrame


class App:
    def __init__(self):
        init_db()
        self.root = tk.Tk()
        self.root.title("СКУД — Система контроля доступа и безопасности")
        self.root.geometry("1200x720")
        self.root.configure(bg='#FFFFFF')  # Чистый белый фон

        self.setup_styles()

        self.operator = None
        self.show_login()
        self.root.mainloop()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background="#FFFFFF")
        style.configure("TLabelframe", background="#FFFFFF", bordercolor="#FAD2E1")
        style.configure("TLabelframe.Label", background="#FFFFFF", foreground="#5A4A4D")

        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#333333", rowheight=25)
        style.configure("Treeview.Heading", background="#FAD2E1", foreground="#5A4A4D", font=("Arial", 10, "bold"))
        style.map('Treeview', background=[('selected', '#FFE4E1')], foreground=[('selected', '#333333')])

        style.configure("TButton", background="#FAD2E1", foreground="#5A4A4D", font=("Arial", 10), borderwidth=1,
                        relief="solid")
        style.map("TButton", background=[('active', '#FFB7B2')])

        style.configure("TCombobox", fieldbackground="#FFFFFF", background="#FAD2E1", foreground="#5A4A4D")

        style.configure("TNotebook", background="#FFFFFF")
        style.configure("TNotebook.Tab", background="#FAD2E1", foreground="#5A4A4D", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#FFB7B2")])

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def show_login(self):
        self._clear()
        LoginFrame(self.root, self)

    def on_login(self, operator):
        self.operator = operator
        self._clear()
        MainFrame(self.root, self)

    def logout(self):
        self.operator = None
        self.show_login()


if __name__ == '__main__':
    App()