import os
import datetime
import logging
from tkinter import messagebox
# Troca: from openai import OpenAI
from google import genai # Importa o SDK do Google Gemini
from google.genai.errors import APIError # Importa a classe de erro
from typing import Any, Optional

LOG_PATH = "logs/app.log"
logger = logging.getLogger(__name__)


# --------------------------
# MENSAGENS AMIGÁVEIS
# --------------------------

# Usamos tkinter.messagebox pois CustomTkinter não possui um substituto nativo para dialogos simples.

def info(master: Any, titulo: str, mensagem: str) -> None:
    """Exibe mensagem informativa."""
    messagebox.showinfo(titulo, mensagem, parent=master)


def erro(master: Any, titulo: str, mensagem: str) -> None:
    """Exibe mensagem de erro."""
    messagebox.showerror(titulo, mensagem, parent=master)


def log_and_alert(master: Any, titulo: str, mensagem: str) -> None:
    """Registra erro no log e exibe alerta."""
    registrar_acao(f"ERRO: {mensagem}")
    messagebox.showerror(titulo, mensagem, parent=master)


def confirmar(master: Any, titulo: str, mensagem: str) -> bool:
    """Exibe mensagem de confirmação e retorna True/False."""
    return messagebox.askyesno(titulo, mensagem, parent=master)


# --------------------------
# LOGS
# --------------------------

def registrar_acao(acao: str) -> None:
    """Registra ação no arquivo de log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {acao}\n")
    except Exception as e:
        logger.error(f"Falha ao registrar log: {e}")

def log(msg: str) -> None:
    """Atalho para registrar ação no log."""
    registrar_acao(msg)


# --------------------------
# INTEGRAÇÃO COM IA (GEMINI)
# --------------------------

def analisar_pedidos(pedidos: str) -> Optional[str]:
    """
    Recebe os pedidos formatados como string e gera insights via IA (Gemini).
    A chave deve estar configurada na variável de ambiente GEMINI_API_KEY.
    """
    try:
        # 1. OBTÉM A CHAVE DIRETAMENTE DA VARIÁVEL DE AMBIENTE
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            # Lança um erro se a chave não for encontrada, facilitando a depuração
            raise ValueError("Chave GEMINI_API_KEY não encontrada no ambiente. Configure-a antes de rodar o app.")

        # 2. Inicializa o cliente, passando a chave explicitamente
        client = genai.Client(api_key=api_key)
        model_name = "gemini-2.5-flash"  # Modelo rápido e eficiente

        prompt = (
            "Você é um excelente analista de vendas. Analise os seguintes pedidos e gere um resumo conciso em português. "
            "Inclua: produtos mais recorrentes, valor médio, padrões e qualquer insight relevante.\\n\\n"
            f"{pedidos}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
        )

        texto = response.text.strip()
        registrar_acao("Análise de pedidos realizada via IA (Gemini).")
        return texto

    except ValueError as ve:
        # Captura a falha de configuração que definimos
        registrar_acao(f"Falha na configuração da chave Gemini: {ve}")
        return None
    except APIError as e:
        registrar_acao(f"Falha na integração com Gemini API: {e}")
        # A API pode retornar 401 Unauthorized se a chave for inválida ou tiver expirado.
        if "API key" in str(e):
            return "Falha na comunicação com a API (código de erro 400+). A chave GEMINI_API_KEY pode estar inválida, incorreta ou expirada."
        return None
    except Exception as e:
        registrar_acao(f"Falha geral na integração com IA: {e}")
        return None