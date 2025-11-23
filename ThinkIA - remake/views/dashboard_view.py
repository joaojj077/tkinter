import customtkinter as ctk
import db
import utils
from typing import Dict, Any


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Row 2 para conteúdo futuro, mas mantém o espaço

        # 1. Título
        ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0,
                                                                                            pady=(10, 5), sticky="w",
                                                                                            padx=10)

        # 2. Frame Container para as Métricas Principais (3 Colunas)
        self.top_metrics_frame = ctk.CTkFrame(self)
        self.top_metrics_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 20))
        # Configura 3 colunas iguais para os cards principais
        self.top_metrics_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="metric_top")

        # 3. Frame Container para as Métricas de Detalhe/Botão (Layout de 2 Colunas)
        self.detail_frame = ctk.CTkFrame(self)
        self.detail_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.detail_frame.grid_columnconfigure((0, 1), weight=1, uniform="metric_detail")
        self.detail_frame.grid_rowconfigure((0, 1), weight=1)  # Garante que os cards internos tenham altura decente

        self.load_metrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Calcula métricas agregadas do banco de dados."""
        metrics = {}
        try:
            # [cite_start]Total de Clientes [cite: 33]
            metrics['total_clientes'] = db.query("SELECT COUNT(id) FROM clientes")[0][0]

            # [cite_start]Total de Pedidos [cite: 31]
            metrics['total_pedidos'] = db.query("SELECT COUNT(id) FROM pedidos")[0][0]

            # [cite_start]Faturamento Total [cite: 31]
            metrics['faturamento_total'] = db.query("SELECT SUM(total) FROM pedidos")[0][0] or 0.0

            # [cite_start]Produtos Mais Vendidos (Top 1) [cite: 30]
            top_produto = db.query("""
                                   SELECT produto, SUM(quantidade) AS total_vendido
                                   FROM itens_pedido
                                   GROUP BY produto
                                   ORDER BY total_vendido DESC LIMIT 1
                                   """)
            metrics['top_produto'] = top_produto[0][0] if top_produto else "N/A"

            # [cite_start]Cliente com Maior Gasto [cite: 31, 33]
            top_cliente = db.query("""
                                   SELECT c.nome, SUM(p.total) AS total_gasto
                                   FROM pedidos p
                                            JOIN clientes c ON p.cliente_id = c.id
                                   GROUP BY c.id
                                   ORDER BY total_gasto DESC LIMIT 1
                                   """)
            metrics['top_cliente'] = top_cliente[0][0] if top_cliente and top_cliente[0][0] else "N/A"

        except Exception as e:
            utils.log(f"Erro ao calcular métricas do dashboard: {e}")
            metrics = {
                'total_clientes': 'Erro', 'total_pedidos': 'Erro',
                'faturamento_total': 0.0, 'top_produto': 'Erro',
                'top_cliente': 'Erro'
            }

        return metrics

    def create_metric_card(self, parent: ctk.CTkFrame, title: str, value: Any, row: int, col: int,
                           is_large: bool = False):
        """Cria um card de métrica CustomTkinter estilizado."""

        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#2d2d30")  # Cor de fundo levemente diferente
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="normal"),
            text_color="#999999"
        )
        title_label.grid(row=0, column=0, pady=(15, 5), padx=15, sticky="w")

        value_font_size = 28 if is_large else 20
        value_label = ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(size=value_font_size, weight="bold"),
            text_color="#ffffff"
        )
        value_label.grid(row=1, column=0, pady=(0, 15), padx=15, sticky="w")

        return card

    def load_metrics(self):
        """Preenche o dashboard com as métricas calculadas."""

        # Limpa frames de métricas existentes
        for widget in self.top_metrics_frame.winfo_children():
            widget.destroy()
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        metrics = self.get_metrics()

        # --- CARDS PRINCIPAIS (3 COLUNAS) ---

        # 1. Total de Clientes
        self.create_metric_card(self.top_metrics_frame,
                                "Total de Clientes",
                                metrics['total_clientes'],
                                0, 0, is_large=True)

        # 2. Total de Pedidos
        self.create_metric_card(self.top_metrics_frame,
                                "Total de Pedidos",
                                metrics['total_pedidos'],
                                0, 1, is_large=True)

        # 3. Faturamento Total
        faturamento_formatado = f"R$ {metrics['faturamento_total']:,.2f}".replace(",", "X").replace(".", ",").replace(
            "X", ".")
        self.create_metric_card(self.top_metrics_frame,
                                "Faturamento Total",
                                faturamento_formatado,
                                0, 2, is_large=True)

        # --- CARDS DE DETALHE (2 COLUNAS) ---

        # 4. Produto Mais Vendido
        self.create_metric_card(self.detail_frame,
                                "Produto Mais Vendido",
                                metrics['top_produto'],
                                0, 0)

        # 5. Cliente Top
        self.create_metric_card(self.detail_frame,
                                "Cliente com Maior Gasto",
                                metrics['top_cliente'],
                                0, 1)

        # --- BOTÃO DE ATUALIZAÇÃO ---

        # Colocado abaixo dos detalhes para não interferir nos cards principais
        self.reload_button = ctk.CTkButton(self.detail_frame,
                                           text="Atualizar Métricas",
                                           command=self.load_metrics,
                                           height=40)
        self.reload_button.grid(row=1, column=0, columnspan=2, pady=(10, 15), padx=10, sticky="ew")