import os
import tkinter as tk
from tkinter import ttk, messagebox

LOG_PATH = "logs/app.log"


class HistoricoView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_widgets()
        self.load_logs()

    def create_widgets(self):
        ttk.Label(
            self,
            text="🪵 Histórico de Ações",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        self.text = tk.Text(
            self,
            wrap="word",
            height=20,
            bg="#252526",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
        )
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(
            self,
            text="Limpar Histórico",
            command=self.clear_logs
        ).pack(pady=5)

    def load_logs(self):
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.write("")
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", f.read())

    def clear_logs(self):
        """Apaga o conteúdo do arquivo de log e limpa a exibição."""
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.close()

        if messagebox.askyesno("Confirmação", "Deseja realmente limpar o histórico?"):
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.write("")
            self.text.delete("1.0", tk.END)
            messagebox.showinfo("Limpo", "Histórico apagado.")
