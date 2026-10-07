"""Constantes e configurações do sistema (sem dependência de interface)."""

import os
from decimal import Decimal
from pathlib import Path

# Pasta do projeto = pasta que contém main.py e o pacote sistema_financeiro/
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# O banco fica na raiz do projeto. Para usar outro local, defina a variável de
# ambiente SISTEMA_FINANCEIRO_DB com o caminho completo do arquivo .db.
DB_PATH = Path(os.environ.get("SISTEMA_FINANCEIRO_DB", RAIZ_PROJETO / "financeiro_familiar.db"))
SCHEMA_VERSION = 1

TIPOS = ("PAGAR", "RECEBER")
ANO_MIN, ANO_MAX = 2000, 2100
VALOR_MAXIMO = Decimal("999999999.99")

PBKDF2_ITERACOES = 600_000
SENHA_MIN = 6
SENHA_INICIAL_ADMIN = "1234"
