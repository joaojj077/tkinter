"""
utils.py — Funções utilitárias para mensagens, logs e integração com IA.
"""

import os
import datetime
import logging
from tkinter import messagebox
from openai import OpenAI

LOG_PATH = "logs/app.log"


# === Mensagens amigáveis ===

def info(master, titulo: str, mensagem: str):
    """Exibe mensagem informativa."""
    messagebox.showinfo(titulo, mensagem, parent=master)


def erro(master, titulo: str, mensagem: str):
    """Exibe mensagem de erro."""
    messagebox.showerror(titulo, mensagem, parent=master)


def log_and_alert(master, titulo: str, mensagem: str):
    """Registra erro no log e mostra alerta na interface."""
    registrar_acao(f"ERRO: {mensagem}")
    messagebox.showerror(titulo, mensagem, parent=master)


# === Logs ===

def registrar_acao(acao: str):
    """Registra ação no arquivo de log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {acao}\n")


# === Integração com IA ===

def analisar_pedidos(pedidos):
    """
    Lê últimos pedidos e gera um resumo automatizado via API oficial da OpenAI.
    Necessário definir variável de ambiente OPENAI_API_KEY.
    """
    try:
        client = OpenAI()  # lê chave da variável de ambiente OPENAI_API_KEY

        prompt = (
            "Analise os seguintes pedidos e gere um resumo em português: "
            "quais produtos aparecem com mais frequência, valores médios e qualquer insight interessante.\n\n"
            f"{pedidos}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um analista de dados de vendas."},
                {"role": "user", "content": prompt},
            ],
        )

        texto = response.choices[0].message.content.strip()
        registrar_acao("Análise de pedidos executada via IA.")
        return texto

    except Exception as e:
        registrar_acao(f"Falha na análise IA: {e}")
        return "Erro ao conectar à IA. Verifique sua chave API (OPENAI_API_KEY)."
