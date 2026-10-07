"""Formatação de valores e datas para exibição."""

from datetime import datetime


def _sem_zero_negativo(valor, casas=2):
    """Evita exibir '-0,00' quando o valor arredondado é zero."""
    return 0.0 if round(valor, casas) == 0 else valor


def formatar_brl(valor):
    """1234.5 -> 'R$ 1.234,50' (formato brasileiro, independente do locale)."""
    texto = f"{_sem_zero_negativo(valor):,.2f}"
    return "R$ " + texto.replace(",", "#").replace(".", ",").replace("#", ".")


def formatar_numero(valor, decimal=",", casas=2):
    """Número puro, sem 'R$' e sem separador de milhar (ideal para planilhas/CSV)."""
    return f"{_sem_zero_negativo(valor, casas):.{casas}f}".replace(".", decimal)


def iso_para_br(texto_iso):
    """'2026-10-06' -> '06/10/2026'. Se não for data ISO, devolve o texto original."""
    try:
        return datetime.strptime(texto_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return texto_iso
