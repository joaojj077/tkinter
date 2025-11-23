import customtkinter as ctk
import db
import utils
from typing import Any


class IAView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Análise Inteligente de Pedidos (Gemini)",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(10, 20), sticky="w")

        # Botão de Ação
        # Nota: O texto do botão foi ajustado
        self.analyze_button = ctk.CTkButton(self, text="Gerar Análise (Pode demorar e requer GEMINI_API_KEY)",
                                            command=self.run_analysis)
        self.analyze_button.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Textbox de Resultado
        self.result_textbox = ctk.CTkTextbox(self, font=("Arial", 12))
        self.result_textbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.result_textbox.insert("1.0",
                                   "Clique em 'Gerar Análise' para que a IA (Gemini) analise todos os pedidos do sistema e forneça insights.")
        self.result_textbox.configure(state="disabled")  # Somente leitura

    def format_pedidos_for_ia(self) -> str:
        """Busca pedidos e itens e formata em uma string para a IA."""
        try:
            # Busca todos os pedidos
            pedidos_raw = db.query("""
                                   SELECT p.id, c.nome, p.data, p.total
                                   FROM pedidos p
                                            JOIN clientes c ON p.cliente_id = c.id
                                   ORDER BY p.data DESC
                                   """)

            if not pedidos_raw:
                return ""

            # Constrói o texto
            texto_pedidos = "Lista de Pedidos:\n"
            for p_id, c_nome, p_data, p_total in pedidos_raw:
                texto_pedidos += f"\n--- Pedido ID: {p_id}, Cliente: {c_nome}, Data: {p_data}, Total: R$ {p_total:.2f} ---\n"

                # Busca itens para o pedido
                itens_raw = db.query("SELECT produto, quantidade FROM itens_pedido WHERE pedido_id = ?", (p_id,))

                itens_list = []
                for produto, quantidade in itens_raw:
                    itens_list.append(f"{produto} (Qtd: {quantidade})")

                texto_pedidos += ", ".join(itens_list)

            return texto_pedidos

        except Exception as e:
            utils.log(f"Erro ao formatar pedidos para IA: {e}")
            return "Erro ao carregar dados do banco."

    def run_analysis(self):
        """Coleta dados, chama a função de análise da IA e exibe o resultado."""

        # Desabilita o botão para evitar cliques múltiplos
        self.analyze_button.configure(state="disabled", text="Analisando com Gemini... Por favor, aguarde.")

        # Habilita o textbox para limpar e inserir status
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", "Coletando dados dos pedidos...")

        pedidos_text = self.format_pedidos_for_ia()

        if not pedidos_text or "Erro" in pedidos_text:
            self.result_textbox.insert("end", "\nFalha ao coletar pedidos ou não há dados para analisar.")
            self.analyze_button.configure(state="normal", text="Gerar Análise (Pode demorar e requer GEMINI_API_KEY)")
            self.result_textbox.configure(state="disabled")
            return

        self.result_textbox.insert("end", "\nEnviando dados para o Gemini...")

        # Chama a função utilitária com a lógica da API
        result = utils.analisar_pedidos(pedidos_text)

        self.result_textbox.delete("1.0", "end")

        if result:
            self.result_textbox.insert("1.0", "✅ Análise Gemini Concluída:\n\n")
            self.result_textbox.insert("end", result)
            utils.info(self, "Sucesso", "Análise de IA concluída e exibida.")
        else:
            # Texto de erro ajustado para o Gemini
            self.result_textbox.insert("1.0",
                                       "❌ FALHA NA ANÁLISE GEMINI:\n\nVerifique se a variável de ambiente GEMINI_API_KEY está configurada corretamente e se você tem acesso à API.")
            utils.erro(self, "Erro de IA", "Falha na comunicação com a API do Gemini. Verifique os logs.")

        self.result_textbox.configure(state="disabled")
        self.analyze_button.configure(state="normal", text="Gerar Análise (Pode demorar e requer GEMINI_API_KEY)")