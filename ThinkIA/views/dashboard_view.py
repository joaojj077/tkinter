import tkinter as tk
from tkinter import ttk, messagebox
import db

class DashboardFrame(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(self, text="📊 Dashboard", font=("Segoe UI", 18, "bold")).pack(pady=10)

        self.lbl_clientes = ttk.Label(self, text="Clientes: ...", font=("Segoe UI", 12))
        self.lbl_clientes.pack(pady=5)
        self.lbl_pedidos = ttk.Label(self, text="Pedidos no mês: ...", font=("Segoe UI", 12))
        self.lbl_pedidos.pack(pady=5)
        self.lbl_ticket = ttk.Label(self, text="Ticket médio: ...", font=("Segoe UI", 12))
        self.lbl_ticket.pack(pady=5)

        ttk.Button(self, text="Atualizar", command=self.update_metrics).pack(pady=10)
        self.update_metrics()

    def update_metrics(self):
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM clientes")
                total_clientes = cur.fetchone()[0]
                cur.execute("""
                    SELECT COUNT(*), COALESCE(AVG(total),0)
                    FROM pedidos
                    WHERE strftime('%Y-%m', data)=strftime('%Y-%m','now')
                """)
                qtd, ticket = cur.fetchone()
            self.lbl_clientes.config(text=f"Clientes: {total_clientes}")
            self.lbl_pedidos.config(text=f"Pedidos no mês: {qtd}")
            self.lbl_ticket.config(text=f"Ticket médio: R$ {ticket:.2f}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar métricas: {e}")
