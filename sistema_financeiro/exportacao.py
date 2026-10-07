"""Exportação do resumo financeiro mensal para CSV.

Formato (uma tabela "longa", fácil de filtrar/pivotar no Excel):

    Ano;Mês;Seção;Item;Valor;Percentual
    2026;10;Resumo;Total de Entradas;5000,00;
    2026;10;Saídas por categoria;Alimentação;60,00;100,00
    ...

Padrões pensados para o Excel em português: separador ';', decimal ',',
UTF-8 com BOM (acentos corretos) e números "puros" (sem 'R$'), para que a
planilha os reconheça como números. Os dois primeiros ficam configuráveis.
"""

import csv
import io

from .models.resumo import ResumoFinanceiro
from .utils.formatacao import formatar_numero

CABECALHO = ("Ano", "Mês", "Seção", "Item", "Valor", "Percentual")

# Textos que o Excel interpretaria como fórmula (ex.: uma categoria chamada "=1+1").
_PREFIXOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def texto_seguro(texto):
    """Neutraliza 'injeção de fórmula' em campos de texto escolhidos pelo usuário."""
    texto = str(texto)
    return "'" + texto if texto.startswith(_PREFIXOS_FORMULA) else texto


def linhas_resumo(resumo):
    """Converte um ResumoFinanceiro (já com carregar_detalhes) em linhas do CSV.

    Cada linha: (ano, mes, secao, item, valor|None, percentual|None).
    """
    linhas = []

    def add(secao, item, valor=None, pct=None):
        linhas.append((resumo.ano, resumo.mes, secao, item, valor, pct))

    add("Resumo", "Total de Entradas", resumo.total_receber)
    add("Resumo", "Total de Saídas", resumo.total_pagar)
    add("Resumo", "Saldo do Mês", resumo.saldo)

    for nome, valor in resumo.por_categoria_pagar:
        add("Saídas por categoria", nome, valor,
            ResumoFinanceiro.percentual(valor, resumo.total_pagar))
    for nome, valor in resumo.por_categoria_receber:
        add("Entradas por categoria", nome, valor,
            ResumoFinanceiro.percentual(valor, resumo.total_receber))

    orc = resumo.orcamento
    pct_usado = ResumoFinanceiro.percentual(orc["gasto"], orc["limite"]) if orc["limite"] > 0 else None
    add("Orçamento", "Limite Definido", orc["limite"])
    add("Orçamento", "Total Gasto", orc["gasto"], pct_usado)   # % do limite utilizado
    add("Orçamento", "Saldo do Orçamento", orc["restante"])
    return linhas


def gerar_csv_resumo(db_manager, mes, ano, delimitador=";", decimal=","):
    """Devolve o conteúdo do CSV (str). Levanta ValueError para mês/ano inválidos."""
    if len(delimitador) != 1 or delimitador == decimal:
        raise ValueError("Delimitador inválido: use 1 caractere diferente do separador decimal.")

    resumo = ResumoFinanceiro(mes=mes, ano=ano)
    resumo.carregar_detalhes(db_manager)

    saida = io.StringIO(newline="")
    escritor = csv.writer(saida, delimiter=delimitador)
    escritor.writerow(CABECALHO)
    for ano_l, mes_l, secao, item, valor, pct in linhas_resumo(resumo):
        escritor.writerow([
            ano_l,
            mes_l,
            texto_seguro(secao),
            texto_seguro(item),
            "" if valor is None else formatar_numero(valor, decimal),
            "" if pct is None else formatar_numero(pct, decimal),
        ])
    return saida.getvalue()


def exportar_resumo_csv(db_manager, mes, ano, caminho, delimitador=";", decimal=","):
    """Grava o resumo do mês em 'caminho' (CSV, UTF-8 com BOM) e devolve o caminho.

    Levanta ValueError (mês/ano/delimitador inválidos) ou OSError (arquivo
    aberto em outro programa, pasta inexistente, sem permissão...).
    """
    conteudo = gerar_csv_resumo(db_manager, mes, ano, delimitador, decimal)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        arquivo.write(conteudo)
    return caminho
