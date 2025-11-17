
import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Iterable, Optional, List, Tuple

DB_PATH = "app.db"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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
    logger.info("Banco inicializado.")


@contextmanager
def get_connection(db_path: str = DB_PATH):
    """Context manager que fornece conexão SQLite com foreign_keys ativado."""
    conn = sqlite3.connect(db_path, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


def execute(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    commit: bool = True,
    db_path: str = DB_PATH,
) -> int:
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
            rows = cur.fetchall()
            return rows
    except Exception:
        logger.exception("Erro fazendo query SQL: %s | params=%s", sql, params)
        raise
