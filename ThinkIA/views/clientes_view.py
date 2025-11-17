"""
views/clientes_view.py
Lista de clientes (Frame com Treeview) + formulário de cadastro/edição (Toplevel).
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional
from models import Cliente
import db
import utils


class ClienteForm(tk.Toplevel):
    """Formulário para criar/editar um Cliente."""

    def __init__(self, master, cliente: Optional[Cliente] = None, on_saved=None):
        super().__init__(master)
        self.title("Cliente" + (" — Editar" if cliente and cliente.id else " — Novo"))
        self.resizable(False, False)
        self.cliente = cliente
        self.on_saved = on_saved
        self._dirty = False

        # vars
        self.var_nome = tk.StringVar(value=cliente.nome if cliente else "")
        self.var_email = tk.StringVar(value=cliente.email if cliente else "")
        self.var_telefone = tk.StringVar(value=cliente.telefone if cliente else "")

        self.build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Nome *").grid(row=0, column=0, sticky="w", **pad)
        e_nome = ttk.Entry(frm, textvariable=self.var_nome, width=40)
        e_nome.grid(row=0, column=1, **pad)
        e_nome.bind("<Key>", lambda e: self.mark_dirty())

        ttk.Label(frm, text="E-mail").grid(row=1, column=0, sticky="w", **pad)
        e_email = ttk.Entry(frm, textvariable=self.var_email, width=40)
        e_email.grid(row=1, column=1, **pad)
        e_email.bind("<Key>", lambda e: self.mark_dirty())

        ttk.Label(frm, text="Telefone").grid(row=2, column=0, sticky="w", **pad)
        e_tel = ttk.Entry(frm, textvariable=self.var_telefone, width=40)
        e_tel.grid(row=2, column=1, **pad)
        e_tel.bind("<Key>", lambda e: self.mark_dirty())

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        btn_salvar = ttk.Button(btn_frame, text="Salvar", command=self.on_save)
        btn_salvar.pack(side="left", padx=6)
        btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self.on_close)
        btn_cancel.pack(side="left")

    def mark_dirty(self):
        self._dirty = True

    def on_close(self):
        if self._dirty and not messagebox.askokcancel("Sair", "Existem alterações não salvas. Sair mesmo?", parent=self):
            return
        self.destroy()

    def on_save(self):
        nome = self.var_nome.get().strip()
        email = self.var_email.get().strip()
        telefone = self.var_telefone.get().strip()

        if not utils.validar_nome(nome):
            utils.erro(self, "Validação", "Nome é obrigatório.")
            return
        if not utils.validar_email(email):
            utils.erro(self, "Validação", "E-mail em formato inválido.")
            return
        if not utils.validar_telefone(telefone):
            utils.erro(self, "Validação", "Telefone deve ter entre 8 e 15 dígitos.")
            return

        try:
            if self.cliente and self.cliente.id:
                # update
                db.execute(
                    "UPDATE clientes SET nome=?, email=?, telefone=? WHERE id=?",
                    (nome, email or None, telefone or None, self.cliente.id),
                )
                utils.info(self, "Sucesso", "Cliente atualizado.")
            else:
                # insert
                new_id = db.execute(
                    "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
                    (nome, email or None, telefone or None),
                )
                utils.info(self, "Sucesso", "Cliente criado.")
            if callable(self.on_saved):
                self.on_saved()
            self._dirty = False
            self.destroy()
        except Exception as e:
            utils.log_and_alert(self, "Erro salvando cliente", str(e))


class ClientesFrame(ttk.Frame):
    """Frame com Treeview listando clientes e controles de CRUD."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.search_var = tk.StringVar()
        self.build()

    def build(self):
        # Search
        top = ttk.Frame(self)
        top.pack(fill="x", pady=6)
        ttk.Label(top, text="Buscar (nome/email):").pack(side="left", padx=(6, 4))
        e = ttk.Entry(top, textvariable=self.search_var)
        e.pack(side="left", fill="x", expand=True, padx=(0, 6))
        e.bind("<Return>", lambda ev: self.load())
        ttk.Button(top, text="Buscar", command=self.load).pack(side="left", padx=(0, 6))

        # Treeview
        cols = ("id", "nome", "email", "telefone")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=120 if c != "nome" else 200)
        self.tree.pack(fill="both", expand=True, padx=6)

        # Buttons
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Novo", command=self.on_new).pack(side="left", padx=6)
        ttk.Button(btns, text="Editar", command=self.on_edit).pack(side="left", padx=6)
        ttk.Button(btns, text="Excluir", command=self.on_delete).pack(side="left", padx=6)
        ttk.Button(btns, text="Atualizar", command=self.load).pack(side="right", padx=6)

        self.load()

    def load(self):
        q = self.search_var.get().strip()
        if q:
            rows = db.query(
                "SELECT id, nome, email, telefone FROM clientes WHERE nome LIKE ? OR email LIKE ? ORDER BY nome",
                (f"%{q}%", f"%{q}%"),
            )
        else:
            rows = db.query("SELECT id, nome, email, telefone FROM clientes ORDER BY nome")
        # limpar
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=r)

    def get_selected(self) -> Optional[Cliente]:
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        return Cliente(id=int(values[0]), nome=values[1], email=values[2], telefone=values[3])

    def on_new(self):
        ClienteForm(self.master, on_saved=self.load)

    def on_edit(self):
        c = self.get_selected()
        if not c:
            utils.erro(self, "Editar", "Selecione um cliente para editar.")
            return
        ClienteForm(self.master, cliente=c, on_saved=self.load)

    def on_delete(self):
        c = self.get_selected()
        if not c:
            utils.erro(self, "Excluir", "Selecione um cliente para excluir.")
            return
        if not utils.confirmar(self, "Excluir", f"Confirmar exclusão de '{c.nome}'?"):
            return
        try:
            db.execute("DELETE FROM clientes WHERE id = ?", (c.id,))
            utils.info(self, "Sucesso", "Cliente excluído.")
            self.load()
        except Exception as e:
            utils.log_and_alert(self, "Erro excluindo cliente", str(e))
