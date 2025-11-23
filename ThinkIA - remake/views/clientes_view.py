import customtkinter as ctk
from tkinter import ttk, StringVar, END
import db
import utils
from models import Cliente
from typing import List, Tuple, Optional, Any


class ClientesFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_cliente_id: Optional[int] = None

        # Container principal (para o Treeview e Formulário)
        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=3)  # Treeview
        main_container.grid_columnconfigure(1, weight=1)  # Formulário
        main_container.grid_rowconfigure(0, weight=1)

        # 1. Treeview (Lista de Clientes)
        self.create_treeview(main_container)

        # 2. Formulário de CRUD (no painel lateral)
        self.create_crud_form(main_container)

        # Carregar dados
        self.load_clientes()

    # --- Treeview ---

    def create_treeview(self, parent: ctk.CTkFrame):
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "nome", "email", "telefone")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Treeview"  # Usa o estilo dark configurado em main.py
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Configurações das colunas
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=30, anchor="center")
        self.tree.heading("nome", text="Nome")
        self.tree.column("nome", width=200, anchor="w")
        self.tree.heading("email", text="E-mail")
        self.tree.column("email", width=150, anchor="w")
        self.tree.heading("telefone", text="Telefone")
        self.tree.column("telefone", width=100, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bind para seleção
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # --- Formulário CRUD ---

    def create_crud_form(self, parent: ctk.CTkFrame):
        # Usamos fg_color="transparent" para que o CustomTkinter Frame se adapte
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(form_frame, text="Gestão de Clientes", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0,
                                                                                                           column=0,
                                                                                                           pady=(0, 15))

        # Nome
        ctk.CTkLabel(form_frame, text="Nome:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.nome_entry = ctk.CTkEntry(form_frame, placeholder_text="Nome do Cliente")
        self.nome_entry.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # E-mail
        ctk.CTkLabel(form_frame, text="E-mail:").grid(row=3, column=0, sticky="w", pady=(5, 0))
        self.email_entry = ctk.CTkEntry(form_frame, placeholder_text="email@exemplo.com")
        self.email_entry.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # Telefone
        ctk.CTkLabel(form_frame, text="Telefone:").grid(row=5, column=0, sticky="w", pady=(5, 0))
        self.telefone_entry = ctk.CTkEntry(form_frame, placeholder_text="(99) 99999-9999")
        self.telefone_entry.grid(row=6, column=0, sticky="ew", pady=(0, 20))

        # Botões
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=7, column=0, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.add_button = ctk.CTkButton(button_frame, text="Adicionar", command=self.add_cliente)
        self.add_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.edit_button = ctk.CTkButton(button_frame, text="Atualizar", command=self.update_cliente, state="disabled")
        self.edit_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.delete_button = ctk.CTkButton(button_frame, text="Deletar", command=self.delete_cliente, fg_color="red",
                                           hover_color="darkred", state="disabled")
        self.delete_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.clear_button = ctk.CTkButton(form_frame, text="Limpar Formulário", command=self.clear_form)
        self.clear_button.grid(row=8, column=0, padx=5, pady=(10, 5), sticky="ew")

    # --- Lógica CRUD ---

    def load_clientes(self):
        """Carrega todos os clientes do banco e preenche a Treeview."""
        # Limpa Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Assumindo que db.query retorna (id, nome, email, telefone)
            clientes = db.query("SELECT id, nome, email, telefone FROM clientes ORDER BY nome")
            for row in clientes:
                self.tree.insert("", "end", iid=row[0], values=row)
        except Exception as e:
            utils.log_and_alert(self, "Erro de Carga", f"Falha ao carregar clientes: {e}")

    def on_select(self, event: Any):
        """Preenche o formulário quando uma linha é selecionada."""
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, 'values')
            if values:
                self.current_cliente_id = int(values[0])
                self.nome_entry.delete(0, END)
                self.nome_entry.insert(0, values[1])
                self.email_entry.delete(0, END)
                self.email_entry.insert(0, values[2])
                self.telefone_entry.delete(0, END)
                self.telefone_entry.insert(0, values[3])

                self.set_buttons_state("edit")
        else:
            self.set_buttons_state("add")
            self.clear_form()

    def add_cliente(self):
        nome = self.nome_entry.get().strip()
        email = self.email_entry.get().strip()
        telefone = self.telefone_entry.get().strip()

        if not nome:
            utils.erro(self, "Erro de Validação", "O nome do cliente é obrigatório.")
            return

        try:
            novo_cliente = Cliente(id=None, nome=nome, email=email, telefone=telefone)
            cliente_id = db.execute(
                "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
                (novo_cliente.nome, novo_cliente.email, novo_cliente.telefone)
            )

            self.load_clientes()
            self.clear_form()
            utils.info(self, "Sucesso", f"Cliente '{nome}' adicionado com ID {cliente_id}.")
            utils.registrar_acao(f"Cliente adicionado: {nome} (ID: {cliente_id})")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Inserção", f"Falha ao adicionar cliente: {e}")

    def update_cliente(self):
        if not self.current_cliente_id:
            utils.erro(self, "Erro", "Selecione um cliente para atualizar.")
            return

        nome = self.nome_entry.get().strip()
        email = self.email_entry.get().strip()
        telefone = self.telefone_entry.get().strip()

        if not nome:
            utils.erro(self, "Erro de Validação", "O nome do cliente é obrigatório.")
            return

        try:
            db.execute(
                "UPDATE clientes SET nome = ?, email = ?, telefone = ? WHERE id = ?",
                (nome, email, telefone, self.current_cliente_id)
            )

            self.load_clientes()
            self.clear_form()
            utils.info(self, "Sucesso", f"Cliente '{nome}' (ID: {self.current_cliente_id}) atualizado.")
            utils.registrar_acao(f"Cliente atualizado: {nome} (ID: {self.current_cliente_id})")

        except Exception as e:
            utils.log_and_alert(self, "Erro de Atualização", f"Falha ao atualizar cliente: {e}")

    def delete_cliente(self):
        if not self.current_cliente_id:
            utils.erro(self, "Erro", "Selecione um cliente para deletar.")
            return

        cliente_nome = self.nome_entry.get()
        # Usa a nova função utils.confirmar
        if utils.confirmar(self, "Confirmação",
                           f"Tem certeza que deseja deletar o cliente '{cliente_nome}' (ID: {self.current_cliente_id})?\nIsso pode deletar pedidos relacionados."):
            try:
                db.execute("DELETE FROM clientes WHERE id = ?", (self.current_cliente_id,))

                self.load_clientes()
                self.clear_form()
                utils.info(self, "Sucesso", f"Cliente '{cliente_nome}' deletado.")
                utils.registrar_acao(f"Cliente deletado: {cliente_nome} (ID: {self.current_cliente_id})")

            except Exception as e:
                utils.log_and_alert(self, "Erro de Exclusão", f"Falha ao deletar cliente: {e}")

    # --- Funções de Interface ---

    def clear_form(self):
        """Limpa todos os campos do formulário e redefine o estado."""
        self.current_cliente_id = None
        self.nome_entry.delete(0, END)
        self.email_entry.delete(0, END)
        self.telefone_entry.delete(0, END)

        # Remove seleção da Treeview
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