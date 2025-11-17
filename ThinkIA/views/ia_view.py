import tkinter as tk
from tkinter import ttk, messagebox
import utils

class IAView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(self, text="🧠 Análise com IA", font=("Segoe UI", 16, "bold")).pack(pady=10)
        ttk.Button(self, text="Analisar Pedidos", command=self.run_analysis).pack(pady=5)
        self.text = tk.Text(self, wrap="word", height=20)
        self.text.pack(fill="both", expand=True)

    def run_analysis(self):
        self.text.delete("1.0", tk.END)
        resultado = utils.analisar_pedidos()
        self.text.insert("1.0", resultado)
