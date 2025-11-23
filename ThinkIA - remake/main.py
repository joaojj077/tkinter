import customtkinter as ctk  # Importar ctk
import os
import db
# Importar frames CustomTkinter
from views.clientes_view import ClientesFrame
from views.pedidos_view import PedidosFrame
from views.produtos_view import ProdutosFrame
from views.dashboard_view import DashboardFrame
from views.relatorios_view import RelatoriosFrame  # Assumindo que esta view será migrada
from views.historico_view import HistoricoView
from views.ia_view import IAView
import utils


# Subclasse de ctk.CTk (o objeto principal da janela)
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ThinkIA — Gestão de Clientes e Pedidos")
        self.geometry("1000x650")
        self.minsize(900, 550)

        # --- Configurações Nativas do CustomTkinter ---
        ctk.set_appearance_mode("Dark")  # Define o modo de aparência (Dark, Light, System)
        ctk.set_default_color_theme("blue")  # Define o tema de cores
        # -----------------------------------------------

        os.makedirs("logs", exist_ok=True)
        db.init_db()

        # O menu bar Tkinter padrão é mais complexo de estilizar.
        # Você pode usar ctk.CTkButton para um menu lateral, como na imagem,
        # ou manter o menu superior padrão por enquanto, sabendo que ele
        # terá o visual padrão do SO.

        # Vamos simular o menu lateral visto na imagem (Image of ThinkIA Dashboard)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_sidebar()

        self.current_frame = None
        self.show_dashboard()

    # 🧭 Menu Lateral (Sidebar)
    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nswe")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="ThinkIA", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0,
                                                                                                        padx=20,
                                                                                                        pady=(20, 10))

        # --- Botões de Navegação ---

        # Dashboard
        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.dashboard_button.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="ew")

        # Clientes
        self.clientes_button = ctk.CTkButton(self.sidebar_frame, text="Clientes", command=self.show_clientes)
        self.clientes_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Produtos
        self.produtos_button = ctk.CTkButton(self.sidebar_frame, text="Produtos", command=self.show_produtos)
        self.produtos_button.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # Pedidos
        self.pedidos_button = ctk.CTkButton(self.sidebar_frame, text="Pedidos", command=self.show_pedidos)
        self.pedidos_button.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # Relatórios
        self.relatorios_button = ctk.CTkButton(self.sidebar_frame, text="Relatórios", command=self.show_relatorios)
        self.relatorios_button.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # Histórico/Log
        self.historico_button = ctk.CTkButton(self.sidebar_frame, text="Histórico/Log", command=self.show_historico)
        self.historico_button.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        # Análise IA
        self.ia_button = ctk.CTkButton(self.sidebar_frame, text="Análise IA", command=self.show_ia)
        self.ia_button.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

    # 🧩 Navegação entre frames (na coluna 1)
    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def show_dashboard(self):
        self.clear_frame()
        self.current_frame = DashboardFrame(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_clientes(self):
        self.clear_frame()
        self.current_frame = ClientesFrame(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_produtos(self):
        self.clear_frame()
        self.current_frame = ProdutosFrame(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_pedidos(self):
        self.clear_frame()
        self.current_frame = PedidosFrame(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_relatorios(self):
        self.clear_frame()
        # NOTE: Certifique-se de que RelatoriosFrame é um CTkFrame
        self.current_frame = RelatoriosFrame(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_historico(self):
        self.clear_frame()
        self.current_frame = HistoricoView(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_ia(self):
        self.clear_frame()
        self.current_frame = IAView(self)
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)


if __name__ == "__main__":
    app = App()
    app.mainloop()