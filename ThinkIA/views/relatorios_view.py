import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import db
import os
from datetime import datetime

class RelatoriosFrame(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(self, text="📑 Relatórios de Pedidos", font=("Segoe UI", 16, "bold")).pack(pady=10)

        filtro = ttk.Frame(self)
        filtro.pack(pady=5)
        ttk.Label(filtro, text="Data Inicial:").grid(row=0, column=0)
        ttk.Label(filtro, text="Data Final:").grid(row=0, column=2)
        self.dt_ini = ttk.Entry(filtro, width=12)
        self.dt_fim = ttk.Entry(filtro, width=12)
        self.dt_ini.grid(row=0, column=1, padx=5)
        self.dt_fim.grid(row=0, column=3, padx=5)
        ttk.Button(filtro, text="Filtrar", command=self.load_data).grid(row=0, column=4, padx=5)

        self.tree = ttk.Treeview(self, columns=("cliente", "data", "total"), show="headings")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("data", text="Data")
        self.tree.heading("total", text="Total (R$)")
        self.tree.pack(fill="both", expand=True, pady=10)

        ttk.Button(self, text="Exportar CSV", command=self.export_csv).pack(side="left", padx=10)
        ttk.Button(self, text="Exportar PDF", command=self.export_pdf).pack(side="left")
        self.load_data()

    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        sql = """
            SELECT c.nome, p.data, p.total
            FROM pedidos p JOIN clientes c ON p.cliente_id=c.id
            WHERE p.data BETWEEN ? AND ?
            ORDER BY p.data DESC
        """
        ini = self.dt_ini.get() or "1900-01-01"
        fim = self.dt_fim.get() or "2999-12-31"
        rows = db.query(sql, (ini, fim))
        for nome, data, total in rows:
            self.tree.insert("", "end", values=(nome, data, f"{total:.2f}"))

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file: return
        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Cliente", "Data", "Total"])
            for item in self.tree.get_children():
                writer.writerow(self.tree.item(item)["values"])
        messagebox.showinfo("Exportado", "Arquivo CSV gerado com sucesso!")

    def export_pdf(self):
        file = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not file: return
        c = canvas.Canvas(file, pagesize=A4)
        c.drawString(100, 800, "Relatório de Pedidos")
        y = 760
        for item in self.tree.get_children():
            cliente, data, total = self.tree.item(item)["values"]
            c.drawString(80, y, f"{data} | {cliente} | R$ {total}")
            y -= 20
        c.save()
        messagebox.showinfo("Exportado", "PDF gerado com sucesso!")
        os.startfile(file)
