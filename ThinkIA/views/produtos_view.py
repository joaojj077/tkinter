"""
views/produtos_view.py
CRUD simples para produtos: nome + preco_unit.
"""

import tkinter as tk
from tkinter import ttk
import db
import utils
from models import Produto
from typing import Optional


class ProdutoForm(tk.Toplevel):
    def __init__(self, master, produto: Produto = None, on_saved=None):
        super().__init__(master)
        self.title("Produto" + (" — Editar" if produto and produto.id else " — Novo"))
        self.produto = produto
        self.on_saved = on_saved
        self.var_nome = tk.StringVar(value=produto.nome if produto else "")
        self.var_preco = tk.StringVar(value=f"{produto.preco_unit:.2f}" if produto else "0.00")
        self._dirty = False
        self.build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Nome *").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_nome, width=40).grid(row=0, column=1, **pad)
        ttk.Label(frm, text="Preço unit. *").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_preco, width=20).grid(row=1, column=1, **pad)
        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Salvar", command=self.on_save).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancelar", command=self.on_close).pack(side="left")

    def on_close(self):
        if self._dirty and not utils.confirmar(self, "Sair", "Existem alterações não salvas. Sair mesmo?"):
            return
        self.destroy()

    def on_save(self):
        nome = self.var_nome.get().strip()
        try:
            preco = float(self.var_preco.get())
        except ValueError:
            utils.erro(self, "Validação", "Preço inválido.")
            return
        if not nome:
            utils.erro(self, "Validação", "Nome é obrigatório.")
            return
        try:
            if self.produto and self.produto.id:
                db.execute("UPDATE produtos SET nome=?, preco_unit=? WHERE id=?", (nome, preco, self.produto.id))
                utils.info(self, "Sucesso", "Produto atualizado.")
            else:
                db.execute("INSERT INTO produtos (nome, preco_unit) VALUES (?,?)", (nome, preco))
                utils.info(self, "Sucesso", "Produto criado.")
            if callable(self.on_saved):
                self.on_saved()
            self.destroy()
        except Exception as e:
            utils.log_and_alert(self, "Erro produto", str(e))


class ProdutosFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.build()

    def build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=6)
        ttk.Button(top, text="Novo", command=self.on_new).pack(side="left", padx=6)
        ttk.Button(top, text="Editar", command=self.on_edit).pack(side="left", padx=6)
        ttk.Button(top, text="Excluir", command=self.on_delete).pack(side="left", padx=6)
        ttk.Button(top, text="Atualizar", command=self.load).pack(side="right", padx=6)

        cols = ("id", "nome", "preco_unit")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=140)
        self.tree.pack(fill="both", expand=True, padx=6)
        self.load()

    def load(self):
        rows = db.query("SELECT id, nome, preco_unit FROM produtos ORDER BY nome")
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], f"{r[2]:.2f}"))

    def get_selected(self) -> Optional[Produto]:
        sel = self.tree.selection()
        if not sel:
            return None
        v = self.tree.item(sel[0], "values")
        return Produto(id=int(v[0]), nome=v[1], preco_unit=float(v[2]))

    def on_new(self):
        ProdutoForm(self.master, on_saved=self.load)

    def on_edit(self):
        p = self.get_selected()
        if not p:
            utils.erro(self, "Editar", "Selecione um produto.")
            return
        ProdutoForm(self.master, produto=p, on_saved=self.load)

    def on_delete(self):
        p = self.get_selected()
        if not p:
            utils.erro(self, "Excluir", "Selecione um produto.")
            return
        if not utils.confirmar(self, "Excluir", f"Excluir produto '{p.nome}'?"):
            return
        try:
            db.execute("DELETE FROM produtos WHERE id=?", (p.id,))
            utils.info(self, "Sucesso", "Produto excluído.")
            self.load()
        except Exception as e:
            utils.log_and_alert(self, "Erro excluindo produto", str(e))
