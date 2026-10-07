"""Camada de persistência: conexão, criação do esquema e migrações (SQLite3)."""

import sqlite3
from contextlib import contextmanager

from .config import DB_PATH, SCHEMA_VERSION, SENHA_INICIAL_ADMIN
from .utils.seguranca import hash_senha, senha_ja_hash
from .utils.validacao import parse_data


class DatabaseManager:
    """Gerenciador do banco de dados SQLite do Sistema Financeiro Familiar."""

    def __init__(self, db_name=DB_PATH):
        self.db_name = str(db_name)
        self.init_db()

    @contextmanager
    def conectar(self):
        """Abre uma conexão com FKs ativas; faz commit/rollback e SEMPRE fecha."""
        conn = sqlite3.connect(self.db_name)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        with self.conectar() as conn:
            self._criar_tabelas(conn)

            versao = conn.execute("PRAGMA user_version").fetchone()[0]
            if versao < 1:
                self._migrar_para_v1(conn)
                conn.execute(f"PRAGMA user_version = {int(SCHEMA_VERSION)}")

            self._inserir_dados_padrao(conn)

    @staticmethod
    def _criar_tabelas(conn):
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                senha TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('PAGAR', 'RECEBER')) NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lancamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('PAGAR', 'RECEBER')) NOT NULL,
                categoria_id INTEGER,
                usuario_id INTEGER,
                observacao TEXT,
                FOREIGN KEY (categoria_id) REFERENCES categoria (id),
                FOREIGN KEY (usuario_id) REFERENCES usuario (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orcamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                valor_limite REAL NOT NULL,
                UNIQUE(mes, ano)
            )
        ''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lancamento_data ON lancamento(data)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lancamento_categoria ON lancamento(categoria_id)")

    @staticmethod
    def _migrar_para_v1(conn):
        """v1: senhas em texto puro -> hash; datas DD/MM/AAAA -> AAAA-MM-DD."""
        for uid, senha in conn.execute("SELECT id, senha FROM usuario").fetchall():
            if not senha_ja_hash(senha):
                conn.execute("UPDATE usuario SET senha = ? WHERE id = ?", (hash_senha(senha), uid))

        for lid, data in conn.execute("SELECT id, data FROM lancamento").fetchall():
            try:
                iso = parse_data(data, validar_ano=False).isoformat()
            except ValueError:
                continue  # data irreconhecível: mantida como está (aparece na lista)
            if iso != data:
                conn.execute("UPDATE lancamento SET data = ? WHERE id = ?", (iso, lid))

    @staticmethod
    def _inserir_dados_padrao(conn):
        if conn.execute("SELECT COUNT(*) FROM categoria").fetchone()[0] == 0:
            categorias_padrao = [
                ('Alimentação', 'PAGAR'),
                ('Moradia', 'PAGAR'),
                ('Transporte', 'PAGAR'),
                ('Saúde', 'PAGAR'),
                ('Lazer', 'PAGAR'),
                ('Salário', 'RECEBER'),
                ('Investimentos', 'RECEBER'),
                ('Outros Recebimentos', 'RECEBER'),
            ]
            conn.executemany("INSERT INTO categoria (nome, tipo) VALUES (?, ?)", categorias_padrao)

        if conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO usuario (nome, senha) VALUES (?, ?)",
                ('Administrador', hash_senha(SENHA_INICIAL_ADMIN)),
            )
