import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Iterable, Optional, List, Tuple

DB_PATH = "app.db"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@contextmanager
def get_connection(db_path: str = DB_PATH):
    """Context Manager para gerenciar a conexão com o banco de dados."""
    conn = None
    try:
        # isolation_level=None para gerenciar o commit manualmente
        conn = sqlite3.connect(db_path, isolation_level=None)
        # Permite acessar colunas por nome (dicionário)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error("Erro na conexão com o banco de dados: %s", e)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """Inicializa o banco SQLite criando tabelas necessárias."""
    logger.info("Inicializando banco de dados em %s", db_path)
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT,
                telefone TEXT
            );

            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco_unit REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS itens_pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                produto TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unit REAL NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    logger.info("Inicialização do banco de dados concluída.")


def execute(sql: str, params: Optional[Iterable[Any]] = None, db_path: str = DB_PATH, commit: bool = True) -> int:
    """
    Executa comando parametrizado. Retorna lastrowid quando aplicável ou rowcount.
    Trata erros e loga exceções.
    """
    params = params or ()
    try:
        with get_connection(db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            if commit:
                conn.commit()
            lastrowid = cur.lastrowid if cur.lastrowid else cur.rowcount
            return lastrowid
    except Exception as e:
        logger.exception("Erro executando SQL: %s | params=%s", sql, params)
        raise


def executemany(sql: str, seq_of_params: Iterable[Iterable[Any]], db_path: str = DB_PATH) -> None:
    """Executa many com tratamento de erro."""
    try:
        with get_connection(db_path) as conn:
            cur = conn.cursor()
            cur.executemany(sql, seq_of_params)
            conn.commit()
    except Exception:
        logger.exception("Erro em executemany SQL")
        raise


def query(sql: str, params: Optional[Iterable[Any]] = None, db_path: str = DB_PATH) -> List[Tuple]:
    """Retorna lista de tuplas com os resultados da query."""
    params = params or ()
    try:
        with get_connection(db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            # Retorna uma lista de tuplas (conversão do Row para tupla)
            return [tuple(row) for row in cur.fetchall()]
    except Exception:
        logger.exception("Erro em query SQL: %s | params=%s", sql, params)
        raise


# --------------------------
# REPOSITÓRIO (FUNÇÕES PARA RELATÓRIOS)
# --------------------------

def get_all_clientes_for_combo(db_path: str = DB_PATH) -> List[Tuple]:
    """Retorna ID e Nome de todos os clientes para popular o Combobox."""
    sql = "SELECT id, nome FROM clientes ORDER BY nome"
    return query(sql, db_path=db_path)


def query_relatorio_pedidos(data_inicial: str, data_final: str, cliente_id: Optional[int], db_path: str = DB_PATH) -> \
List[Tuple]:
    """Busca pedidos com cliente, filtrando por data e cliente."""
    sql = """
          SELECT p.id, \
                 c.nome, \
                 p.data, \
                 p.total
          FROM pedidos p
                   JOIN clientes c ON p.cliente_id = c.id
          WHERE 1 = 1 \
          """
    params = []

    if data_inicial:
        sql += " AND p.data >= ?"
        params.append(data_inicial)

    if data_final:
        sql += " AND p.data <= ?"
        params.append(data_final)

    if cliente_id:
        sql += " AND c.id = ?"
        params.append(cliente_id)

    # Ordena para melhor visualização
    sql += " ORDER BY p.data DESC"

    return query(sql, params, db_path=db_path)


def get_itens_pedido(pedido_id: int, db_path: str = DB_PATH) -> List[Tuple]:
    """Retorna os itens de um pedido específico."""
    sql = "SELECT produto, quantidade, preco_unit FROM itens_pedido WHERE pedido_id = ?"
    return query(sql, (pedido_id,), db_path=db_path)