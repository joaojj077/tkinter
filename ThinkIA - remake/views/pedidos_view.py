import customtkinter as ctk
from tkinter import ttk, END
import db
import utils
from models import ItemPedido, Pedido
from typing import List, Tuple, Optional, Any
from datetime import date

class PedidosFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_pedido_id: Optional[int] = None
        self.current_itens: List[ItemPedido] = []
        self.clientes_map = {}  # {nome: id}
        self.produtos_map = {}  # {nome: preco}

        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=3) # Lista de pedidos
        main_container.grid_columnconfigure(1, weight=2) # Formulário de Pedido/Itens
        main_container.grid_rowconfigure(0, weight=1)

        # 1. Treeview (Lista de Pedidos)
        self.create_pedidos_treeview(main_container)

        # 2. Formulário de CRUD (no painel lateral)
        self.create_crud_form(main_container)
        
        self.load_dependencies()
        self.load_pedidos()

    def load_dependencies(self):
        """Carrega clientes e produtos para combobox/referência."""
        try:
            # Clientes
            clientes = db.query("SELECT id, nome FROM clientes ORDER BY nome")
            self.clientes_map = {nome: id for id, nome in clientes}
            
            # Produtos
            produtos = db.query("SELECT nome, preco_unit FROM produtos ORDER BY nome")
            self.produtos_map = {nome: preco for nome, preco in produtos}
            
            # Atualiza Comboboxes
            nomes_clientes = list(self.clientes_map.keys())
            if nomes_clientes:
                self.cliente_combobox.configure(values=nomes_clientes)
                self.cliente_var.set(nomes_clientes[0])

            nomes_produtos = list(self.produtos_map.keys())
            if nomes_produtos:
                self.produto_combobox.configure(values=nomes_produtos)
                self.produto_var.set(nomes_produtos[0])
                # Bind para atualizar o preço quando o produto muda
                self.produto_combobox.bind("<<ComboboxSelected>>", self.on_produto_select)

        except Exception as e:
            utils.log_and_alert(self, "Erro de Carga", f"Falha ao carregar dados: {e}")

    # --- Lista de Pedidos ---

    def create_pedidos_treeview(self, parent: ctk.CTkFrame):
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "cliente", "data", "total")
        self.pedidos_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
        self.pedidos_tree.grid(row=0, column=0, sticky="nsew")

        # Configurações das colunas
        self.pedidos_tree.heading("id", text="ID")
        self.pedidos_tree.column("id", width=40, anchor="center")
        self.pedidos_tree.heading("cliente", text="Cliente")
        self.pedidos_tree.column("cliente", width=200, anchor="w")
        self.pedidos_tree.heading("data", text="Data")
        self.pedidos_tree.column("data", width=100, anchor="center")
        self.pedidos_tree.heading("total", text="Total")
        self.pedidos_tree.column("total", width=100, anchor="e")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.pedidos_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.pedidos_tree.configure(yscrollcommand=scrollbar.set)
        
        self.pedidos_tree.bind("<<TreeviewSelect>>", self.on_pedido_select)

    # --- Formulário Principal e Itens ---

    def create_crud_form(self, parent: ctk.CTkFrame):
        form_frame = ctk.CTkFrame(parent) 
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=1)

        # 1. Header e Total
        header_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 15))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(header_frame, text="Novo Pedido", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        
        self.total_label = ctk.CTkLabel(header_frame, text="TOTAL: R$ 0,00", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_label.grid(row=0, column=1, sticky="e")

        # 2. Dados do Pedido
        data_frame = ctk.CTkFrame(form_frame)
        data_frame.grid(row=1, column=0, sticky="ew", pady=10)
        data_frame.grid_columnconfigure(0, weight=1)
        data_frame.grid_columnconfigure(1, weight=1)

        # Cliente (Combobox)
        ctk.CTkLabel(data_frame, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cliente_var = ctk.StringVar()
        self.cliente_combobox = ctk.CTkComboBox(data_frame, variable=self.cliente_var, values=[])
        self.cliente_combobox.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # Data
        ctk.CTkLabel(data_frame, text="Data (AAAA-MM-DD):").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.data_entry = ctk.CTkEntry(data_frame, placeholder_text=str(date.today()))
        self.data_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # 3. Formulário de Itens
        ctk.CTkLabel(form_frame, text="Adicionar Item:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        item_form_frame = ctk.CTkFrame(form_frame)
        item_form_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        item_form_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Produto
        ctk.CTkLabel(item_form_frame, text="Produto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.produto_var = ctk.StringVar()
        self.produto_combobox = ctk.CTkComboBox(item_form_frame, variable=self.produto_var, values=[])
        self.produto_combobox.grid(row=1, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        
        # Preço Unitário (apenas leitura)
        ctk.CTkLabel(item_form_frame, text="Preço Unit.:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.preco_entry = ctk.CTkEntry(item_form_frame, placeholder_text="0.00", state="readonly")
        self.preco_entry.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # Quantidade
        ctk.CTkLabel(item_form_frame, text="Qtd:").grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.qtd_entry = ctk.CTkEntry(item_form_frame, placeholder_text="1")
        self.qtd_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Botão Adicionar Item
        self.add_item_button = ctk.CTkButton(item_form_frame, text="Adicionar Item", command=self.add_item_to_list)
        self.add_item_button.grid(row=2, column=0, padx=5, pady=10, columnspan=4, sticky="ew")

        # 4. Treeview de Itens
        self.create_itens_treeview(form_frame)

        # 5. Botões de Ação do Pedido
        action_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        action_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.save_button = ctk.CTkButton(action_frame, text="Salvar Pedido", command=self.save_pedido)
        self.save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.delete_button = ctk.CTkButton(action_frame, text="Deletar Pedido", command=self.delete_pedido, fg_color="red", hover_color="darkred", state="disabled")
        self.delete_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.clear_button = ctk.CTkButton(action_frame, text="Limpar", command=self.clear_form)
        self.clear_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
    def create_itens_treeview(self, parent: ctk.CTkFrame):
        # Treeview para listar itens do pedido
        itens_frame = ctk.CTkFrame(parent)
        itens_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        itens_frame.grid_columnconfigure(0, weight=1)
        itens_frame.grid_rowconfigure(0, weight=1)
        
        columns = ("produto", "quantidade", "preco_unit", "subtotal")
        self.itens_tree = ttk.Treeview(itens_frame, columns=columns, show="headings", style="Treeview")
        self.itens_tree.grid(row=0, column=0, sticky="nsew")

        self.itens_tree.heading("produto", text="Produto")
        self.itens_tree.column("produto", width=150, anchor="w")
        self.itens_tree.heading("quantidade", text="Qtd")
        self.itens_tree.column("quantidade", width=50, anchor="center")
        self.itens_tree.heading("preco_unit", text="Preço Unit.")
        self.itens_tree.column("preco_unit", width=80, anchor="e")
        self.itens_tree.heading("subtotal", text="Subtotal")
        self.itens_tree.column("subtotal", width=80, anchor="e")
        
        scrollbar = ttk.Scrollbar(itens_frame, orient="vertical", command=self.itens_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.itens_tree.configure(yscrollcommand=scrollbar.set)
        
        # Botão de remover item abaixo da lista
        remove_item_button = ctk.CTkButton(itens_frame, text="Remover Item Selecionado", command=self.remove_item, fg_color="gray", hover_color="darkgray")
        remove_item_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

    # --- Lógica de Dados ---

    def load_pedidos(self):
        """Carrega todos os pedidos do banco e preenche a Treeview."""
        for item in self.pedidos_tree.get_children():
            self.pedidos_tree.delete(item)
            
        try:
            # Query que busca pedidos com o nome do cliente
            pedidos = db.query("""
                SELECT p.id, c.nome, p.data, p.total 
                FROM pedidos p JOIN clientes c ON p.cliente_id = c.id 
                ORDER BY p.data DESC
            """)
            for id, cliente_nome, data, total in pedidos:
                total_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                self.pedidos_tree.insert("", "end", iid=id, values=(id, cliente_nome, data, total_formatado))
        except Exception as e:
            utils.log_and_alert(self, "Erro de Carga", f"Falha ao carregar pedidos: {e}")

    def on_produto_select(self, event: Any):
        """Atualiza o campo de preço ao selecionar um produto."""
        produto_nome = self.produto_var.get()
        preco = self.produtos_map.get(produto_nome, 0.0)
        
        # Atualiza o campo de preço (é preciso temporariamente mudar o estado)
        self.preco_entry.configure(state="normal")
        self.preco_entry.delete(0, END)
        self.preco_entry.insert(0, f"{preco:.2f}")
        self.preco_entry.configure(state="readonly")


    def add_item_to_list(self):
        """Adiciona um item à lista temporária (current_itens) do pedido."""
        produto_nome = self.produto_var.get()
        qtd_str = self.qtd_entry.get().strip()
        
        if not produto_nome or not qtd_str:
            utils.erro(self, "Erro", "Selecione um produto e informe a quantidade.")
            return

        try:
            quantidade = int(qtd_str)
            if quantidade <= 0:
                utils.erro(self, "Erro", "Quantidade deve ser positiva.")
                return
            
            preco_unit = self.produtos_map.get(produto_nome, 0.0)
            
            # Cria o objeto ItemPedido
            novo_item = ItemPedido(
                id=None, 
                pedido_id=self.current_pedido_id, 
                produto=produto_nome, 
                quantidade=quantidade, 
                preco_unit=preco_unit
            )
            self.current_itens.append(novo_item)
            
            self.update_itens_treeview()
            self.update_total()
            self.qtd_entry.delete(0, END)
            self.qtd_entry.insert(0, "1") # Reseta para 1
            
        except ValueError:
            utils.erro(self, "Erro", "Quantidade inválida.")
        except Exception as e:
            utils.log_and_alert(self, "Erro", f"Falha ao adicionar item: {e}")

    def remove_item(self):
        """Remove o item selecionado da lista temporária."""
        selected_item_iid = self.itens_tree.focus()
        if not selected_item_iid:
            utils.erro(self, "Erro", "Selecione um item na lista de itens para remover.")
            return

        # O IID da Treeview de itens corresponde ao índice na lista self.current_itens
        try:
            # Obtém o índice do IID (que é a ordem de inserção)
            item_index = self.itens_tree.index(selected_item_iid)
            del self.current_itens[item_index]
            self.update_itens_treeview()
            self.update_total()
        except IndexError:
            utils.erro(self, "Erro", "Item não encontrado na lista.")

    def update_itens_treeview(self):
        """Atualiza a Treeview de itens com base em self.current_itens."""
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
            
        for i, item in enumerate(self.current_itens):
            subtotal = item.quantidade * item.preco_unit
            preco_formatado = f"R$ {item.preco_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            subtotal_formatado = f"R$ {subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            # Usa o índice i como iid para facilitar a exclusão
            self.itens_tree.insert("", "end", iid=i, values=(item.produto, item.quantidade, preco_formatado, subtotal_formatado))

    def update_total(self):
        """Calcula e atualiza o total do pedido."""
        total = sum(item.quantidade * item.preco_unit for item in self.current_itens)
        total_formatado = f"TOTAL: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.total_label.configure(text=total_formatado)
        return total

    def save_pedido(self):
        """Salva ou atualiza o pedido no banco de dados."""
        cliente_nome = self.cliente_var.get()
        data_str = self.data_entry.get().strip()
        total = self.update_total()

        cliente_id = self.clientes_map.get(cliente_nome)

        if not cliente_id or not data_str:
            utils.erro(self, "Erro", "Selecione um cliente e informe a data (AAAA-MM-DD).")
            return
        if not self.current_itens:
            utils.erro(self, "Erro", "O pedido deve ter pelo menos um item.")
            return

        if self.current_pedido_id:
            self._update_pedido(cliente_id, data_str, total)
        else:
            self._insert_pedido(cliente_id, data_str, total)

    def _insert_pedido(self, cliente_id: int, data_str: str, total: float):
        try:
            # 1. Insere o Pedido
            pedido_id = db.execute(
                "INSERT INTO pedidos (cliente_id, data, total) VALUES (?, ?, ?)",
                (cliente_id, data_str, total)
            )

            # 2. Insere os Itens do Pedido
            itens_to_insert = [
                (pedido_id, i.produto, i.quantidade, i.preco_unit) 
                for i in self.current_itens
            ]
            db.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit) VALUES (?, ?, ?, ?)",
                itens_to_insert
            )

            self.load_pedidos()
            self.clear_form()
            utils.info(self, "Sucesso", f"Pedido {pedido_id} criado.")
            utils.registrar_acao(f"Pedido criado: ID {pedido_id}, Cliente ID {cliente_id}")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Inserção", f"Falha ao salvar novo pedido: {e}")

    def _update_pedido(self, cliente_id: int, data_str: str, total: float):
        try:
            # 1. Atualiza o Pedido
            db.execute(
                "UPDATE pedidos SET cliente_id = ?, data = ?, total = ? WHERE id = ?",
                (cliente_id, data_str, total, self.current_pedido_id)
            )

            # 2. Deleta e Reinsere todos os Itens
            db.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (self.current_pedido_id,))
            
            itens_to_insert = [
                (self.current_pedido_id, i.produto, i.quantidade, i.preco_unit) 
                for i in self.current_itens
            ]
            if itens_to_insert:
                db.executemany(
                    "INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit) VALUES (?, ?, ?, ?)",
                    itens_to_insert
                )

            self.load_pedidos()
            self.clear_form()
            utils.info(self, "Sucesso", f"Pedido {self.current_pedido_id} atualizado.")
            utils.registrar_acao(f"Pedido atualizado: ID {self.current_pedido_id}, Cliente ID {cliente_id}")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Atualização", f"Falha ao atualizar pedido: {e}")

    def delete_pedido(self):
        if not self.current_pedido_id:
            utils.erro(self, "Erro", "Selecione um pedido para deletar.")
            return

        if utils.confirmar(self, "Confirmação", f"Tem certeza que deseja deletar o Pedido ID {self.current_pedido_id}?"):
            try:
                # O DELETE CASCADE no banco deve cuidar dos itens
                db.execute("DELETE FROM pedidos WHERE id = ?", (self.current_pedido_id,))
                
                self.load_pedidos()
                self.clear_form()
                utils.info(self, "Sucesso", f"Pedido ID {self.current_pedido_id} deletado.")
                utils.registrar_acao(f"Pedido deletado: ID {self.current_pedido_id}")

            except Exception as e:
                utils.log_and_alert(self, "Erro de Exclusão", f"Falha ao deletar pedido: {e}")

    # --- Funções de Interface ---

    def on_pedido_select(self, event: Any):
        """Carrega os dados do pedido selecionado no formulário."""
        selected_item = self.pedidos_tree.focus()
        if selected_item:
            values = self.pedidos_tree.item(selected_item, 'values')
            if values:
                self.current_pedido_id = int(values[0])
                
                # Preenche campos
                cliente_nome = values[1]
                data = values[2]
                
                self.cliente_var.set(cliente_nome)
                self.data_entry.delete(0, END)
                self.data_entry.insert(0, data)

                # Carrega itens
                self.load_itens_for_edit(self.current_pedido_id)
                
                self.save_button.configure(text="Atualizar Pedido")
                self.delete_button.configure(state="normal")
        else:
            self.clear_form()
    
    def load_itens_for_edit(self, pedido_id: int):
        """Carrega itens do banco para o estado self.current_itens."""
        self.current_itens = []
        try:
            itens_raw = db.query(
                "SELECT produto, quantidade, preco_unit FROM itens_pedido WHERE pedido_id = ?", 
                (pedido_id,)
            )
            for produto, quantidade, preco_unit in itens_raw:
                 self.current_itens.append(ItemPedido(
                    id=None, 
                    pedido_id=pedido_id, 
                    produto=produto, 
                    quantidade=quantidade, 
                    preco_unit=preco_unit
                ))
            
            self.update_itens_treeview()
            self.update_total()
        except Exception as e:
            utils.log_and_alert(self, "Erro de Carga", f"Falha ao carregar itens do pedido: {e}")


    def clear_form(self):
        """Limpa o formulário e reseta o estado para um novo pedido."""
        self.current_pedido_id = None
        self.current_itens = []
        
        # Limpa campos
        self.data_entry.delete(0, END)
        self.data_entry.insert(0, str(date.today()))
        self.qtd_entry.delete(0, END)
        self.qtd_entry.insert(0, "1")
        
        # Reseta o total e as treeviews
        self.total_label.configure(text="TOTAL: R$ 0,00")
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
            
        for item in self.pedidos_tree.selection():
            self.pedidos_tree.selection_remove(item)
            
        # Reseta botões
        self.save_button.configure(text="Salvar Pedido")
        self.delete_button.configure(state="disabled")