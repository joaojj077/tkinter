import tkinter as tk
from tkinter import ttk, messagebox
import os
import db
from views.clientes_view import ClientesFrame
from views.pedidos_view import PedidosFrame
from views.produtos_view import ProdutosFrame
from views.dashboard_view import DashboardFrame
from views.relatorios_view import RelatoriosFrame
from views.historico_view import HistoricoView
from views.ia_view import IAView
import utils


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ThinkIA — Gestão de Clientes e Pedidos")
        self.geometry("1000x650")
        self.minsize(900, 550)
        self.configure(bg="#1e1e1e")

        os.makedirs("logs", exist_ok=True)
        db.init_db()

        self.apply_dark_theme()
        self.create_menu()
        self.current_frame = None
        self.show_dashboard()

    # 🎨 Tema escuro estilizado
    def apply_dark_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Cores base
        bg = "#1e1e1e"
        surface = "#252526"
        fg = "#ffffff"
        accent = "#0078d4"
        hover = "#3a3d41"

        style.configure(
            ".",
            background=bg,
            foreground=fg,
            fieldbackground=surface,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 10)
        )

        style.configure(
            "TButton",
            background=surface,
            foreground=fg,
            padding=6,
            borderwidth=1,
            focusthickness=3,
            focuscolor=accent,
            relief="flat",
        )
        style.map(
            "TButton",
            background=[("active", hover)],
            relief=[("pressed", "sunken")]
        )

        style.configure(
            "TLabel",
            background=bg,
            foreground=fg
        )

        style.configure(
            "Treeview",
            background=surface,
            fieldbackground=surface,
            foreground=fg,
            borderwidth=0,
            rowheight=26
        )
        style.map("Treeview", background=[("selected", accent)], foreground=[("selected", "#ffffff")])

        style.configure("TEntry", fieldbackground=surface, foreground=fg, insertcolor=fg)
        style.configure("TCombobox", fieldbackground=surface, selectbackground=surface, foreground=fg)
        style.configure("TNotebook", background=bg, tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", background=surface, foreground=fg, padding=[8, 4])
        style.map("TNotebook.Tab", background=[("selected", accent)], foreground=[("selected", "#ffffff")])

    # 🧭 Menu superior
    def create_menu(self):
        menubar = tk.Menu(self, bg="#2d2d30", fg="#ffffff", tearoff=0, activebackground="#0078d4", activeforeground="#ffffff")

        cadastros = tk.Menu(menubar, tearoff=0, bg="#2d2d30", fg="#ffffff", activebackground="#0078d4", activeforeground="#ffffff")
        cadastros.add_command(label="Clientes", command=self.show_clientes)
        cadastros.add_command(label="Produtos", command=self.show_produtos)
        cadastros.add_command(label="Pedidos", command=self.show_pedidos)
        menubar.add_cascade(label="Cadastros", menu=cadastros)

        relatorios = tk.Menu(menubar, tearoff=0, bg="#2d2d30", fg="#ffffff", activebackground="#0078d4", activeforeground="#ffffff")
        relatorios.add_command(label="Relatórios", command=self.show_relatorios)
        menubar.add_cascade(label="Relatórios", menu=relatorios)

        ia_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d30", fg="#ffffff", activebackground="#0078d4", activeforeground="#ffffff")
        ia_menu.add_command(label="Análises com IA", command=self.show_ia)
        menubar.add_cascade(label="IA", menu=ia_menu)

        menubar.add_command(label="Histórico", command=self.show_historico)
        menubar.add_command(label="Dashboard", command=self.show_dashboard)
        menubar.add_command(label="Sair", command=self.confirm_exit)
        self.config(menu=menubar)

    # 🧩 Navegação entre frames
    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def show_dashboard(self):
        self.clear_frame()
        self.current_frame = DashboardFrame(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_clientes(self):
        self.clear_frame()
        self.current_frame = ClientesFrame(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_produtos(self):
        self.clear_frame()
        self.current_frame = ProdutosFrame(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_pedidos(self):
        self.clear_frame()
        self.current_frame = PedidosFrame(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_relatorios(self):
        self.clear_frame()
        self.current_frame = RelatoriosFrame(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_historico(self):
        self.clear_frame()
        self.current_frame = HistoricoView(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_ia(self):
        self.clear_frame()
        self.current_frame = IAView(self)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def confirm_exit(self):
        if messagebox.askyesno("Sair", "Deseja realmente encerrar o aplicativo?"):
            self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
