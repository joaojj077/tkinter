import customtkinter as ctk
import os
import utils
from typing import Any


class HistoricoView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Histórico de Ações (logs/app.log)", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, pady=(10, 10), sticky="w")

        # Botão para Recarregar (melhoria de UX)
        reload_button = ctk.CTkButton(self, text="Recarregar Log", command=self.load_log)
        reload_button.grid(row=0, column=0, pady=(10, 10), padx=10, sticky="e")

        self.textbox = ctk.CTkTextbox(self, wrap="none", font=("Consolas", 10))  # Wrap="none" para logs longos
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.load_log()

    def load_log(self):
        """Carrega o conteúdo do arquivo de log e exibe no Textbox."""
        self.textbox.delete("1.0", "end")

        if not os.path.exists(utils.LOG_PATH):
            self.textbox.insert("1.0", "Arquivo de log não encontrado. Nenhuma ação registrada ainda.")
            return

        try:
            with open(utils.LOG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                self.textbox.insert("1.0", content)
            self.textbox.see("end")  # Rola para o final
        except Exception as e:
            self.textbox.insert("1.0", f"Erro ao ler arquivo de log: {e}")
            utils.log(f"Falha ao ler log para exibição: {e}")