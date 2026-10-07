"""Modelo Usuario (autenticação por hash)."""

from ..config import SENHA_MIN
from ..utils.seguranca import hash_senha, verificar_senha


class Usuario:
    def __init__(self, user_id=None, nome="", senha_hash=""):
        self.id = user_id
        self.nome = nome
        self.senha_hash = senha_hash

    @staticmethod
    def buscar_por_nome(db_manager, nome):
        with db_manager.conectar() as conn:
            row = conn.execute(
                "SELECT id, nome, senha FROM usuario WHERE nome = ?", (nome,)
            ).fetchone()
        return Usuario(*row) if row else None

    def autenticar(self, senha):
        """Verifica se a senha informada corresponde à senha do usuário."""
        return verificar_senha(senha, self.senha_hash)

    def alterar_senha(self, db_manager, senha_atual, nova_senha):
        """Altera a senha (exige a senha atual) e grava somente o hash."""
        if not self.autenticar(senha_atual):
            raise ValueError("Senha atual incorreta.")
        if len(nova_senha) < SENHA_MIN:
            raise ValueError(f"A nova senha deve ter pelo menos {SENHA_MIN} caracteres.")
        novo_hash = hash_senha(nova_senha)
        with db_manager.conectar() as conn:
            conn.execute("UPDATE usuario SET senha = ? WHERE id = ?", (novo_hash, self.id))
        self.senha_hash = novo_hash
