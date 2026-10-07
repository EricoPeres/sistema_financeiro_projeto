"""Modelo Categoria."""

from ..config import TIPOS


class Categoria:
    def __init__(self, cat_id=None, nome="", tipo="PAGAR"):
        self.id = cat_id
        self.nome = nome
        self.tipo = tipo

    @staticmethod
    def listar_todas(db_manager, tipo=None):
        sql = "SELECT id, nome, tipo FROM categoria"
        params = ()
        if tipo:
            sql += " WHERE tipo = ?"
            params = (tipo,)
        sql += " ORDER BY tipo, nome"
        with db_manager.conectar() as conn:
            return conn.execute(sql, params).fetchall()

    def _validar(self, db_manager):
        self.nome = (self.nome or "").strip()
        if not self.nome:
            raise ValueError("Informe o nome da categoria.")
        if len(self.nome) > 50:
            raise ValueError("O nome da categoria deve ter no máximo 50 caracteres.")
        if self.tipo not in TIPOS:
            raise ValueError("Tipo de categoria inválido.")
        for cid, nome, _ in Categoria.listar_todas(db_manager, self.tipo):
            if cid != self.id and nome.casefold() == self.nome.casefold():
                raise ValueError(f"Já existe uma categoria '{nome}' do tipo {self.tipo}.")

    def criar(self, db_manager):
        self._validar(db_manager)
        with db_manager.conectar() as conn:
            cursor = conn.execute(
                "INSERT INTO categoria (nome, tipo) VALUES (?, ?)", (self.nome, self.tipo)
            )
            self.id = cursor.lastrowid

    def editar(self, db_manager):
        self._validar(db_manager)
        with db_manager.conectar() as conn:
            atual = conn.execute("SELECT tipo FROM categoria WHERE id = ?", (self.id,)).fetchone()
            if atual is None:
                raise ValueError("Categoria não encontrada.")
            if atual[0] != self.tipo:
                em_uso = conn.execute(
                    "SELECT COUNT(*) FROM lancamento WHERE categoria_id = ?", (self.id,)
                ).fetchone()[0]
                if em_uso:
                    raise ValueError(
                        f"Não é possível mudar o tipo: a categoria é usada em {em_uso} lançamento(s)."
                    )
            conn.execute(
                "UPDATE categoria SET nome = ?, tipo = ? WHERE id = ?",
                (self.nome, self.tipo, self.id),
            )

    def excluir(self, db_manager):
        if self.id is None:
            return
        with db_manager.conectar() as conn:
            em_uso = conn.execute(
                "SELECT COUNT(*) FROM lancamento WHERE categoria_id = ?", (self.id,)
            ).fetchone()[0]
            if em_uso:
                raise ValueError(
                    f"Não é possível excluir: a categoria é usada em {em_uso} lançamento(s)."
                )
            conn.execute("DELETE FROM categoria WHERE id = ?", (self.id,))
