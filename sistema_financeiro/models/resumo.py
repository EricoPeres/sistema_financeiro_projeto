"""Resumo financeiro mensal: dados consolidados + relatório em texto.

Esta classe é a ÚNICA fonte dos números do relatório: tanto a tela quanto a
exportação CSV (exportacao.py) usam os atributos preenchidos aqui.
"""

from datetime import datetime

from ..utils.formatacao import formatar_brl
from .lancamento import Lancamento
from .orcamento import Orcamento


class ResumoFinanceiro:
    def __init__(self, mes=None, ano=None):
        self.mes = mes or datetime.now().month
        self.ano = ano or datetime.now().year
        self.total_pagar = 0.0
        self.total_receber = 0.0
        self.saldo = 0.0
        # Preenchidos por carregar_detalhes():
        self.por_categoria_pagar = []     # [(categoria, total)]
        self.por_categoria_receber = []   # [(categoria, total)]
        self.orcamento = {"limite": 0.0, "gasto": 0.0, "restante": 0.0}

    def calcular(self, db_manager):
        """Só os totais do mês (leve; usado na tela inicial)."""
        self.total_pagar = Lancamento.total_por_tipo(db_manager, "PAGAR", self.mes, self.ano)
        self.total_receber = Lancamento.total_por_tipo(db_manager, "RECEBER", self.mes, self.ano)
        self.saldo = round(self.total_receber - self.total_pagar, 2)

    def carregar_detalhes(self, db_manager):
        """Totais + quebra por categoria + situação do orçamento."""
        self.calcular(db_manager)
        self.por_categoria_pagar = Lancamento.totais_por_categoria(
            db_manager, "PAGAR", self.mes, self.ano)
        self.por_categoria_receber = Lancamento.totais_por_categoria(
            db_manager, "RECEBER", self.mes, self.ano)
        self.orcamento = Orcamento.obter_resumo(db_manager, self.mes, self.ano)

    @staticmethod
    def percentual(valor, total):
        """Participação de 'valor' em 'total' (0 quando total é zero)."""
        return (valor / total * 100) if total else 0.0

    @staticmethod
    def _bloco_categorias(titulo, itens, total):
        linhas = [f" --- {titulo} ---"]
        if not itens:
            linhas.append("   (sem lançamentos)")
        for nome, valor in itens:
            pct = f"{ResumoFinanceiro.percentual(valor, total):.1f}".replace(".", ",")
            linhas.append(f"   {nome[:20]:<20} {formatar_brl(valor):>16} {pct:>6}%")
        return linhas

    def gerar_relatorio(self, db_manager):
        self.carregar_detalhes(db_manager)
        orc = self.orcamento

        sep = "=" * 47
        linhas = [
            sep,
            f"   RESUMO FINANCEIRO - {self.mes:02d}/{self.ano}",
            "   Desenvolvido por: e-ST Software",
            sep,
            "",
            f" (+) Total de Entradas (Receber): {formatar_brl(self.total_receber)}",
            f" (-) Total de Saídas (Pagar)   : {formatar_brl(self.total_pagar)}",
            " " + "-" * 45,
            f" (=) Saldo do Mês              : {formatar_brl(self.saldo)}",
            "",
        ]
        linhas += self._bloco_categorias("SAÍDAS POR CATEGORIA", self.por_categoria_pagar, self.total_pagar)
        linhas.append("")
        linhas += self._bloco_categorias("ENTRADAS POR CATEGORIA", self.por_categoria_receber, self.total_receber)
        linhas += [
            "",
            " --- CONTROLE DE ORÇAMENTO ---",
            f" Limite Definido : {formatar_brl(orc['limite'])}",
            f" Total Gasto     : {formatar_brl(orc['gasto'])}",
            f" Saldo Orçamento : {formatar_brl(orc['restante'])}",
        ]
        if orc["limite"] > 0 and orc["gasto"] > orc["limite"]:
            linhas.append(f" [ALERTA] Orçamento estourado em {formatar_brl(abs(orc['restante']))}!")
        linhas.append(sep)
        return "\n".join(linhas) + "\n"
