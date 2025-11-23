import customtkinter as ctk
from tkinter import ttk, END
import db
import utils
from models import Produto
from typing import Optional, Any

class ProdutosFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_produto_id: Optional[int] = None

        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=3) # Treeview
        main_container.grid_columnconfigure(1, weight=1) # Formulário
        main_container.grid_rowconfigure(0, weight=1)

        # 1. Treeview (Lista de Produtos)
        self.create_treeview(main_container)

        # 2. Formulário de CRUD
        self.create_crud_form(main_container)
        
        self.load_produtos()

    # --- Treeview ---

    def create_treeview(self, parent: ctk.CTkFrame):
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "nome", "preco_unit")
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            style="Treeview" 
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Configurações das colunas
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=30, anchor="center")
        self.tree.heading("nome", text="Nome do Produto")
        self.tree.column("nome", width=300, anchor="w")
        self.tree.heading("preco_unit", text="Preço Unitário")
        self.tree.column("preco_unit", width=150, anchor="e")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # --- Formulário CRUD ---

    def create_crud_form(self, parent: ctk.CTkFrame):
        form_frame = ctk.CTkFrame(parent, fg_color="transparent") 
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        ctk.CTkLabel(form_frame, text="Gestão de Produtos", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(0, 15))

        # Nome
        ctk.CTkLabel(form_frame, text="Nome:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.nome_entry = ctk.CTkEntry(form_frame, placeholder_text="Nome do Produto")
        self.nome_entry.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Preço Unitário
        ctk.CTkLabel(form_frame, text="Preço Unitário: (Ex: 15.99)").grid(row=3, column=0, sticky="w", pady=(5, 0))
        self.preco_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.preco_entry.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        
        # Botões
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.add_button = ctk.CTkButton(button_frame, text="Adicionar", command=self.add_produto)
        self.add_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.edit_button = ctk.CTkButton(button_frame, text="Atualizar", command=self.update_produto, state="disabled")
        self.edit_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.delete_button = ctk.CTkButton(button_frame, text="Deletar", command=self.delete_produto, fg_color="red", hover_color="darkred", state="disabled")
        self.delete_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.clear_button = ctk.CTkButton(form_frame, text="Limpar Formulário", command=self.clear_form)
        self.clear_button.grid(row=6, column=0, padx=5, pady=(10, 5), sticky="ew")


    # --- Lógica CRUD ---

    def load_produtos(self):
        """Carrega todos os produtos do banco e preenche a Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            produtos = db.query("SELECT id, nome, preco_unit FROM produtos ORDER BY nome")
            for id, nome, preco in produtos:
                preco_formatado = f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                self.tree.insert("", "end", iid=id, values=(id, nome, preco_formatado))
        except Exception as e:
            utils.log_and_alert(self, "Erro de Carga", f"Falha ao carregar produtos: {e}")

    def on_select(self, event: Any):
        """Preenche o formulário quando uma linha é selecionada."""
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, 'values')
            if values:
                self.current_produto_id = int(values[0])
                
                # O preço está formatado (R$ X.XXX,XX), precisamos do valor original no banco para edição (float)
                produto_raw = db.query("SELECT preco_unit FROM produtos WHERE id = ?", (self.current_produto_id,))
                preco_float = produto_raw[0][0] if produto_raw else 0.0
                
                self.nome_entry.delete(0, END)
                self.nome_entry.insert(0, values[1])
                self.preco_entry.delete(0, END)
                self.preco_entry.insert(0, str(preco_float))
                
                self.set_buttons_state("edit")
        else:
            self.set_buttons_state("add")
            self.clear_form()

    def get_form_data(self):
        """Valida e retorna os dados do formulário."""
        nome = self.nome_entry.get().strip()
        preco_str = self.preco_entry.get().strip().replace(",", ".")

        if not nome:
            utils.erro(self, "Erro de Validação", "O nome do produto é obrigatório.")
            return None
        try:
            preco = float(preco_str)
            if preco <= 0:
                 utils.erro(self, "Erro de Validação", "O preço deve ser maior que zero.")
                 return None
            return Produto(id=None, nome=nome, preco_unit=preco)
        except ValueError:
            utils.erro(self, "Erro de Validação", "Preço inválido. Use um formato numérico.")
            return None

    def add_produto(self):
        produto_data = self.get_form_data()
        if not produto_data: return

        try:
            produto_id = db.execute(
                "INSERT INTO produtos (nome, preco_unit) VALUES (?, ?)", 
                (produto_data.nome, produto_data.preco_unit)
            )
            
            self.load_produtos()
            self.clear_form()
            utils.info(self, "Sucesso", f"Produto '{produto_data.nome}' adicionado com ID {produto_id}.")
            utils.registrar_acao(f"Produto adicionado: {produto_data.nome} (ID: {produto_id})")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Inserção", f"Falha ao adicionar produto: {e}")

    def update_produto(self):
        if not self.current_produto_id:
            utils.erro(self, "Erro", "Selecione um produto para atualizar.")
            return
            
        produto_data = self.get_form_data()
        if not produto_data: return

        try:
            db.execute(
                "UPDATE produtos SET nome = ?, preco_unit = ? WHERE id = ?", 
                (produto_data.nome, produto_data.preco_unit, self.current_produto_id)
            )
            
            self.load_produtos()
            self.clear_form()
            utils.info(self, "Sucesso", f"Produto '{produto_data.nome}' (ID: {self.current_produto_id}) atualizado.")
            utils.registrar_acao(f"Produto atualizado: {produto_data.nome} (ID: {self.current_produto_id})")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Atualização", f"Falha ao atualizar produto: {e}")

    def delete_produto(self):
        if not self.current_produto_id:
            utils.erro(self, "Erro", "Selecione um produto para deletar.")
            return

        produto_nome = self.nome_entry.get()
        if utils.confirmar(self, "Confirmação", f"Tem certeza que deseja deletar o produto '{produto_nome}'?"):
            try:
                db.execute("DELETE FROM produtos WHERE id = ?", (self.current_produto_id,))
                
                self.load_produtos()
                self.clear_form()
                utils.info(self, "Sucesso", f"Produto '{produto_nome}' deletado.")
                utils.registrar_acao(f"Produto deletado: {produto_nome} (ID: {self.current_produto_id})")

            except Exception as e:
                utils.log_and_alert(self, "Erro de Exclusão", f"Falha ao deletar produto: {e}")

    # --- Funções de Interface ---

    def clear_form(self):
        """Limpa todos os campos do formulário e redefine o estado."""
        self.current_produto_id = None
        self.nome_entry.delete(0, END)
        self.preco_entry.delete(0, END)
        
        for item in self.tree.selection():
            self.tree.selection_remove(item)
            
        self.set_buttons_state("add")

    def set_buttons_state(self, mode: str):
        """Define o estado dos botões CRUD."""
        if mode == "add":
            self.add_button.configure(state="normal")
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
        elif mode == "edit":
            self.add_button.configure(state="disabled")
            self.edit_button.configure(state="normal")
            self.delete_button.configure(state="normal")