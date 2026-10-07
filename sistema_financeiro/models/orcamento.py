"""Modelo Orcamento (limite mensal de gastos)."""

import math
from datetime import datetime

from ..utils.validacao import intervalo_mes
from .lancamento import Lancamento


class Orcamento:
    def __init__(self, orc_id=None, mes=None, ano=None, valor_limite=0.0):
        self.id = orc_id
        self.mes = mes or datetime.now().month
        self.ano = ano or datetime.now().year
        self.valor_limite = valor_limite

    def definir_limite(self, db_manager, valor):
        intervalo_mes(self.mes, self.ano)  # valida mês e ano
        if not math.isfinite(valor) or valor <= 0:
            raise ValueError("O limite deve ser maior que zero.")
        self.valor_limite = valor
        with db_manager.conectar() as conn:
            conn.execute('''
                INSERT INTO orcamento (mes, ano, valor_limite)
                VALUES (?, ?, ?)
                ON CONFLICT(mes, ano) DO UPDATE SET valor_limite = excluded.valor_limite
            ''', (self.mes, self.ano, self.valor_limite))

    @staticmethod
    def obter_resumo(db_manager, mes, ano):
        with db_manager.conectar() as conn:
            row = conn.execute(
                "SELECT valor_limite FROM orcamento WHERE mes = ? AND ano = ?", (mes, ano)
            ).fetchone()
        limite = row[0] if row else 0.0
        gasto = Lancamento.total_por_tipo(db_manager, "PAGAR", mes, ano)
        return {
            "mes": mes,
            "ano": ano,
            "limite": limite,
            "gasto": gasto,
            "restante": round(limite - gasto, 2),
        }
