"""Hash e verificação de senhas (PBKDF2-HMAC-SHA256 com salt aleatório)."""

import hashlib
import hmac
import os

from ..config import PBKDF2_ITERACOES


def hash_senha(senha, salt=None, iteracoes=PBKDF2_ITERACOES):
    """Gera 'pbkdf2_sha256$iteracoes$salt$hash'."""
    salt = salt if salt is not None else os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)
    return f"pbkdf2_sha256${iteracoes}${salt.hex()}${h.hex()}"


def senha_ja_hash(valor):
    return isinstance(valor, str) and valor.startswith("pbkdf2_sha256$")


def verificar_senha(senha, armazenado):
    """Compara a senha informada com o hash armazenado (tempo constante)."""
    try:
        algoritmo, iteracoes, salt_hex, hash_hex = armazenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        calculado = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), int(iteracoes)
        )
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(calculado.hex(), hash_hex)
