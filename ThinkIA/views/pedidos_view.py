"""
views/pedidos_view.py
Janela para criar e gerenciar pedidos: seleção cliente, data, itens, total e salvamento transacional.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import List
import db
import utils
from models import Pedido, ItemPedido


# -----------------------------
# FORMULÁRIO DE NOVO PEDIDO
# -----------------------------
class PedidoForm(tk.Toplevel):
    """Formulário para criação de novo pedido."""

    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.title("Novo Pedido")
        self.on_saved = on_saved
        self._dirty = False

        self.var_cliente = tk.StringVar()
        self.var_data = tk.StringVar(value=date.today().isoformat())
        self.total_var = tk.StringVar(value="0.00")

        self.itens: List[ItemPedido] = []
        self.build()
        self.load_clientes()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Cliente *").grid(row=0, column=0, sticky="w", **pad)
        self.cmb_cliente = ttk.Combobox(frm, textvariable=self.var_cliente, state="readonly", width=40)
        self.cmb_cliente.grid(row=0, column=1, **pad)

        ttk.Label(frm, text="Data").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_data, width=20).grid(row=1, column=1, sticky="w", **pad)

        # Itens
        cols = ("produto", "quantidade", "preco_unit", "subtotal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=100)
        self.tree.grid(row=2, column=0, columnspan=2, padx=8, pady=6)

        item_controls = ttk.Frame(frm)
        item_controls.grid(row=3, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Button(item_controls, text="Adicionar Item", command=self.on_add_item).pack(side="left", padx=4)
        ttk.Button(item_controls, text="Remover Item", command=self.on_remove_item).pack(side="left", padx=4)

        # Total
        ttk.Label(frm, text="Total:").grid(row=4, column=0, sticky="e", padx=8, pady=8)
        ttk.Label(frm, textvariable=self.total_var).grid(row=4, column=1, sticky="w", padx=8)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Salvar Pedido", command=self.on_save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=self.on_close).pack(side="left")

    def load_clientes(self):
        rows = db.query("SELECT id, nome FROM clientes ORDER BY nome")
        self.clientes = {f"{r[1]} (#{r[0]})": r[0] for r in rows}
        self.cmb_cliente["values"] = list(self.clientes.keys())
        if rows:
            self.cmb_cliente.current(0)

    def on_add_item(self):
        dlg = AddItemDialog(self, on_added=self.add_item)
        dlg.grab_set()

    def add_item(self, produto: str, quantidade: int, preco_unit: float):
        subtotal = quantidade * preco_unit
        item = ItemPedido(id=None, pedido_id=None, produto=produto, quantidade=quantidade, preco_unit=preco_unit)
        self.itens.append(item)
        self.tree.insert("", "end", values=(produto, quantidade, f"{preco_unit:.2f}", f"{subtotal:.2f}"))
        self._dirty = True
        self.update_total()

    def on_remove_item(self):
        sel = self.tree.selection()
        if not sel:
            utils.erro(self, "Remover item", "Selecione um item para remover.")
            return
        idx = self.tree.index(sel[0])
        self.tree.delete(sel[0])
        del self.itens[idx]
        self._dirty = True
        self.update_total()

    def update_total(self):
        total = sum(i.quantidade * i.preco_unit for i in self.itens)
        self.total_var.set(f"{total:.2f}")

    def on_close(self):
        if self._dirty and not messagebox.askokcancel("Sair", "Existem alterações não salvas. Sair mesmo?", parent=self):
            return
        self.destroy()

    def on_save(self):
        cliente_label = self.var_cliente.get()
        cliente_id = self.clientes.get(cliente_label)
        data_str = self.var_data.get().strip()

        if not cliente_id:
            utils.erro(self, "Validação", "Selecione um cliente.")
            return
        if not self.itens:
            utils.erro(self, "Validação", "Adicione pelo menos um item.")
            return

        try:
            total = sum(i.quantidade * i.preco_unit for i in self.itens)
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("BEGIN")
                cur.execute(
                    "INSERT INTO pedidos (cliente_id, data, total) VALUES (?, ?, ?)",
                    (cliente_id, data_str, total),
                )
                pedido_id = cur.lastrowid
                items_params = [(pedido_id, it.produto, it.quantidade, it.preco_unit) for it in self.itens]
                cur.executemany(
                    "INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit) VALUES (?, ?, ?, ?)",
                    items_params,
                )
                conn.commit()

            utils.info(self, "Sucesso", f"Pedido salvo com total {total:.2f}")
            utils.log(f"Novo pedido #{pedido_id} criado para cliente {cliente_label} (total R$ {total:.2f})")

            self._dirty = False
            if callable(self.on_saved):
                self.on_saved()
            self.destroy()

        except Exception as e:
            utils.log_and_alert(self, "Erro salvando pedido", str(e))
            try:
                conn.rollback()
            except Exception:
                pass


# -----------------------------
# DIÁLOGO PARA ADICIONAR ITEM
# -----------------------------
class AddItemDialog(tk.Toplevel):
    """Diálogo para adicionar item."""

    def __init__(self, master, on_added=None):
        super().__init__(master)
        self.title("Adicionar Item")
        self.on_added = on_added
        self.var_produto = tk.StringVar()
        self.var_quant = tk.StringVar(value="1")
        self.var_preco = tk.StringVar(value="0.00")
        self.build()
        self.grab_set()
        self.resizable(False, False)

    def build(self):
        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Produto").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_produto, width=40).grid(row=0, column=1, **pad)
        ttk.Label(frm, text="Quantidade").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_quant, width=20).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(frm, text="Preço unit.").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_preco, width=20).grid(row=2, column=1, sticky="w", **pad)
        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Adicionar", command=self.on_add).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="left")

    def on_add(self):
        produto = self.var_produto.get().strip()
        try:
            quant = int(self.var_quant.get())
            preco = float(self.var_preco.get())
        except ValueError:
            utils.erro(self, "Validação", "Quantidade deve ser inteiro e preço numérico.")
            return
        if not produto:
            utils.erro(self, "Validação", "Produto é obrigatório.")
            return
        if quant <= 0 or preco < 0:
            utils.erro(self, "Validação", "Quantidade/Preço inválidos.")
            return
        if callable(self.on_added):
            self.on_added(produto, quant, preco)
        self.destroy()


# -----------------------------
# FRAME PRINCIPAL DE PEDIDOS
# -----------------------------
class PedidosFrame(ttk.Frame):
    """Janela para gerenciamento de pedidos."""

    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_widgets()
        self.load_pedidos()

    def create_widgets(self):
        ttk.Label(self, text="📦 Pedidos", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # Tabela de pedidos
        cols = ("id", "cliente", "data", "total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        btns = ttk.Frame(self)
        btns.pack(pady=5)
        ttk.Button(btns, text="Novo Pedido", command=self.on_new_pedido).pack(side="left", padx=6)
        ttk.Button(btns, text="Atualizar", command=self.load_pedidos).pack(side="left", padx=6)

    def load_pedidos(self):
        self.tree.delete(*self.tree.get_children())
        rows = db.query(
            """
            SELECT p.id, c.nome, p.data, p.total
            FROM pedidos p
            JOIN clientes c ON c.id = p.cliente_id
            ORDER BY p.id DESC
            """
        )
        for r in rows:
            self.tree.insert("", "end", values=r)

    def on_new_pedido(self):
        PedidoForm(self, on_saved=self.load_pedidos)
