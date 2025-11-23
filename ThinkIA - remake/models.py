"""
models.py
dataclasses simples para representar entidades do sistema.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class Cliente:
    id: Optional[int]
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None


@dataclass
class Produto:
    id: Optional[int]
    nome: str
    preco_unit: float


@dataclass
class ItemPedido:
    id: Optional[int]
    pedido_id: Optional[int]
    produto: str
    quantidade: int
    preco_unit: float


@dataclass
class Pedido:
    id: Optional[int]
    cliente_id: int
    data: str  # ISO date string yyyy-mm-dd
    total: float
    itens: Optional[List[ItemPedido]] = None
