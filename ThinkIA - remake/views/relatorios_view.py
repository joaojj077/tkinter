import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from datetime import date
import os
import db  # Importa o db atualizado com as funções de repositório
import utils
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import csv
from typing import List, Any


class RelatoriosFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Treeview ocupa a maior parte

        self.clientes_map = {}  # {nome: id}

        # 1. Componentes de Filtro
        self.create_filter_widgets()

        # 2. Treeview de Resultados
        self.create_treeview()

        # 3. Componentes de Exportação
        self.create_export_widgets()

        # Carregar dados iniciais
        self.load_clientes()
        self.run_report()

    def load_clientes(self):
        """Carrega clientes para o Combobox usando a função do db."""
        try:
            # db.get_all_clientes_for_combo é a nova função no db.py
            clientes = db.get_all_clientes_for_combo()
            self.clientes_map = {nome: id for id, nome in clientes}
            nomes_clientes = ["TODOS"] + list(self.clientes_map.keys())
            self.cliente_var.set("TODOS")
            self.cliente_combobox.configure(values=nomes_clientes)
        except Exception as e:
            utils.log_and_alert(self, "Erro de Carga", f"Falha ao carregar clientes: {e}")

    # --- Criação de Widgets ---

    def create_filter_widgets(self):
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        filter_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Datas
        ctk.CTkLabel(filter_frame, text="Data Inicial:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.data_inicial_entry = ctk.CTkEntry(filter_frame, placeholder_text="AAAA-MM-DD")
        self.data_inicial_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(filter_frame, text="Data Final:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.data_final_entry = ctk.CTkEntry(filter_frame, placeholder_text="AAAA-MM-DD")
        self.data_final_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Cliente (Combobox)
        ctk.CTkLabel(filter_frame, text="Cliente:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cliente_var = ctk.StringVar()
        self.cliente_combobox = ctk.CTkComboBox(filter_frame, variable=self.cliente_var, values=["TODOS"])
        self.cliente_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Botão de Aplicar Filtro
        self.apply_button = ctk.CTkButton(filter_frame, text="Aplicar Filtros", command=self.run_report)
        self.apply_button.grid(row=1, column=3, padx=5, pady=5, sticky="e")

    def create_treeview(self):
        # Frame para conter a Treeview e a Scrollbar
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Treeview (usando ttk.Treeview e o estilo dark configurado em main.py)
        columns = ("id", "cliente", "data", "itens", "total")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Treeview"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Configurações das colunas
        self.tree.heading("id", text="ID", anchor="center")
        self.tree.column("id", width=40, anchor="center")
        self.tree.heading("cliente", text="Cliente")
        self.tree.column("cliente", width=200, anchor="w")
        self.tree.heading("data", text="Data")
        self.tree.column("data", width=100, anchor="center")
        self.tree.heading("itens", text="Itens (Produto x Qtd)")
        self.tree.column("itens", width=350, anchor="w")
        self.tree.heading("total", text="Total")
        self.tree.column("total", width=100, anchor="e")

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def create_export_widgets(self):
        export_frame = ctk.CTkFrame(self)
        export_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        export_frame.grid_columnconfigure((0, 1), weight=1)

        self.export_csv_button = ctk.CTkButton(export_frame, text="Exportar CSV", command=self.export_csv)
        self.export_csv_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.export_pdf_button = ctk.CTkButton(export_frame, text="Exportar PDF", command=self.export_pdf)
        self.export_pdf_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # --- Lógica de Dados e Exibição ---

    def run_report(self):
        """Executa a query com os filtros e atualiza a Treeview."""
        # Limpa a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        data_inicial = self.data_inicial_entry.get().strip()
        data_final = self.data_final_entry.get().strip()
        cliente_nome = self.cliente_var.get()
        cliente_id = self.clientes_map.get(cliente_nome) if cliente_nome != "TODOS" else None

        if not self.validate_dates(data_inicial, data_final):
            return

        try:
            # db.query_relatorio_pedidos é a nova função no db.py
            pedidos_data = db.query_relatorio_pedidos(data_inicial, data_final, cliente_id)

            if not pedidos_data:
                utils.info(self, "Relatório", "Nenhum pedido encontrado com os filtros aplicados.")
                return

            for id, cliente_nome, data, total in pedidos_data:
                # Busca os itens para o resumo na Treeview 
                itens_resumo = self.format_itens_resumo(id)
                # Formata total para exibir corretamente no Treeview
                total_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                # Insere o pedido como item pai na Treeview
                self.tree.insert(
                    "",
                    "end",
                    iid=id,  # Usa o ID do pedido como identificador
                    values=(id, cliente_nome, data, itens_resumo, total_formatado)
                )

        except Exception as e:
            utils.log_and_alert(self, "Erro no Relatório", f"Falha ao gerar relatório: {e}")

    def format_itens_resumo(self, pedido_id: int) -> str:
        """Busca itens do pedido e retorna uma string resumida."""
        try:
            # db.get_itens_pedido é a nova função no db.py
            itens = db.get_itens_pedido(pedido_id)
            resumo = [f"{i[0]} x {i[1]}" for i in itens]
            # Limita a 3 itens para visualização
            resumo_str = ", ".join(resumo[:3])
            if len(resumo) > 3:
                resumo_str += f", (+{len(resumo) - 3} mais)"
            return resumo_str
        except Exception as e:
            utils.log(f"Erro ao buscar itens do pedido {pedido_id}: {e}")
            return "Erro ao carregar itens"

    def validate_dates(self, start_date_str, end_date_str) -> bool:
        """Valida se as strings de data são datas válidas, se preenchidas."""
        from datetime import datetime  # Importação local para evitar circular
        if start_date_str:
            try:
                datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                utils.erro(self, "Filtro Inválido", "A Data Inicial não está no formato AAAA-MM-DD.")
                return False
        if end_date_str:
            try:
                datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                utils.erro(self, "Filtro Inválido", "A Data Final não está no formato AAAA-MM-DD.")
                return False
        return True

    # --- Funções de Exportação ---

    def get_all_data_for_export(self) -> List[List[Any]]:
        """Prepara os dados da Treeview e busca itens completos para exportação."""
        data = []
        # Cabeçalhos
        data.append(["ID Pedido", "Cliente", "Data", "Total", "Produto", "Quantidade", "Preço Unitário Item"])

        for pedido_iid in self.tree.get_children():
            # (id, cliente_nome, data, itens_resumo, total_formatado)
            pedido_vals = self.tree.item(pedido_iid, "values")
            pedido_id = int(pedido_vals[0])
            cliente_nome = pedido_vals[1]
            data_pedido = pedido_vals[2]
            # Remove formatação R$ para exportar como valor numérico no CSV/PDF
            total = pedido_vals[4].replace("R$ ", "").replace(".", "").replace(",", ".")

            # Busca itens completos para a exportação
            itens = db.get_itens_pedido(pedido_id)

            if itens:
                for produto, quantidade, preco_unit in itens:
                    # Linha do relatório (repete dados do pedido para cada item)
                    data.append([
                        pedido_id,
                        cliente_nome,
                        data_pedido,
                        total,
                        produto,
                        quantidade,
                        preco_unit
                    ])
            else:
                # Linha para pedidos sem itens (embora não deva acontecer)
                data.append([pedido_id, cliente_nome, data_pedido, total, "N/A", 0, 0.00])

        return data

    def export_csv(self):
        """Exporta os dados filtrados para um arquivo CSV e abre-o."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Salvar Relatório CSV"
        )
        if not file_path:
            return

        try:
            data = self.get_all_data_for_export()
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                # Usando ';' como delimitador para evitar problemas com vírgulas em números e nomes de produtos
                writer = csv.writer(f, delimiter=';')
                writer.writerows(data)

            utils.info(self, "Exportação Concluída", f"Relatório CSV gerado com sucesso:\n{file_path}")
            # Tenta abrir o arquivo no sistema operacional
            os.startfile(file_path)
            utils.registrar_acao(f"Relatório exportado para CSV: {file_path}")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Exportação", f"Falha ao exportar CSV: {e}")

    def export_pdf(self):
        """Exporta os dados filtrados para um arquivo PDF usando ReportLab e abre-o."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
            title="Salvar Relatório PDF"
        )
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            # Título
            elements.append(Paragraph("Relatório de Pedidos - ThinkIA", styles['h1']))
            elements.append(Paragraph(f"Gerado em: {date.today():%Y-%m-%d}", styles['Normal']))
            elements.append(Paragraph("<br/>", styles['Normal']))

            # Preparar dados para a tabela do PDF
            raw_data = self.get_all_data_for_export()

            # Formatação para o PDF: remove colunas desnecessárias e formata valores
            pdf_data = []
            for row in raw_data:
                if row[0] == "ID Pedido":  # Cabeçalho
                    pdf_data.append(["ID", "Cliente", "Data", "Total Pedido", "Produto", "Qtd", "Preço Unit."])
                else:
                    # row: [ID Pedido, Cliente, Data, Total, Produto, Quantidade, Preço Unitário Item]
                    # Formata o total do pedido e o preço unitário para moeda
                    total_formatado = f"R$ {float(row[3]):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    preco_unit_formatado = f"R$ {float(row[6]):,.2f}".replace(",", "X").replace(".", ",").replace("X",
                                                                                                                  ".")

                    pdf_data.append([
                        row[0],
                        row[1],
                        row[2],
                        total_formatado,
                        row[4],
                        row[5],
                        preco_unit_formatado
                    ])

            # Tabela
            table = Table(pdf_data)

            # Estilo da tabela
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),  # Azul CTk
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ])
            table.setStyle(style)
            elements.append(table)

            doc.build(elements)

            utils.info(self, "Exportação Concluída", f"Relatório PDF gerado com sucesso:\n{file_path}")
            os.startfile(file_path)  # Abre o arquivo
            utils.registrar_acao(f"Relatório exportado para PDF: {file_path}")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Exportação",
                                f"Falha ao exportar PDF. Verifique se o ReportLab está instalado: {e}")