"""Conversão e validação de entradas do usuário (valor, data, mês/ano)."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..config import ANO_MAX, ANO_MIN, VALOR_MAXIMO


def parse_valor(texto):
    """Converte texto em valor monetário (float com 2 casas). Levanta ValueError.

    Aceita '1234.56', '1234,56' e '1.234,56'. Rejeita vazio, NaN, infinito,
    zero e negativos.
    """
    t = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        v = Decimal(t)
    except InvalidOperation:
        raise ValueError("Informe um valor numérico válido (ex.: 1.234,56).") from None
    if not v.is_finite():
        raise ValueError("Informe um valor numérico válido (ex.: 1.234,56).")
    if v <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    if v > VALOR_MAXIMO:
        raise ValueError("O valor informado é grande demais.")
    return float(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def parse_data(texto, validar_ano=True):
    """Converte 'DD/MM/AAAA' ou 'AAAA-MM-DD' em date. Levanta ValueError."""
    texto = (texto or "").strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(texto, formato).date()
        except ValueError:
            continue
        if validar_ano and not ANO_MIN <= d.year <= ANO_MAX:
            raise ValueError(f"O ano deve estar entre {ANO_MIN} e {ANO_MAX}.")
        return d
    raise ValueError("Data inválida. Use o formato DD/MM/AAAA.")


def intervalo_mes(mes, ano):
    """Devolve (inicio, fim_exclusivo) em ISO para consultas 'data >= ? AND data < ?'."""
    if not 1 <= mes <= 12:
        raise ValueError("O mês deve estar entre 1 e 12.")
    if not ANO_MIN <= ano <= ANO_MAX:
        raise ValueError(f"O ano deve estar entre {ANO_MIN} e {ANO_MAX}.")
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio.isoformat(), fim.isoformat()


def validar_mes_ano(mes_txt, ano_txt):
    """Lê mês/ano digitados (ex.: de dois Spinbox) e valida. Levanta ValueError."""
    try:
        mes, ano = int(mes_txt), int(ano_txt)
    except (TypeError, ValueError):
        raise ValueError("Mês e ano devem ser números inteiros.") from None
    intervalo_mes(mes, ano)  # valida as faixas e gera a mensagem adequada
    return mes, ano
