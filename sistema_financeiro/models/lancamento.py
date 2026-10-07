"""Modelo Lancamento (contas a pagar / a receber) e consultas de totais."""

import math

from ..config import TIPOS
from ..utils.validacao import intervalo_mes, parse_data


class Lancamento:
    def __init__(self, lanc_id=None, descricao="", valor=0.0, data="", tipo="PAGAR",
                 categoria_id=None, usuario_id=1, observacao=""):
        self.id = lanc_id
        self.descricao = descricao
        self.valor = valor
        self.data = data          # ISO (AAAA-MM-DD) depois de validar()
        self.tipo = tipo
        self.categoria_id = categoria_id
        self.usuario_id = usuario_id
        self.observacao = observacao

    def validar(self):
        self.descricao = (self.descricao or "").strip()
        if not self.descricao:
            raise ValueError("A descrição do lançamento é obrigatória.")
        if len(self.descricao) > 120:
            raise ValueError("A descrição deve ter no máximo 120 caracteres.")
        if self.tipo not in TIPOS:
            raise ValueError("Tipo de lançamento inválido.")
        if (not isinstance(self.valor, (int, float)) or not math.isfinite(self.valor)
                or self.valor <= 0):
            raise ValueError("O valor deve ser maior que zero.")
        self.valor = round(float(self.valor), 2)
        self.data = parse_data(self.data).isoformat()
        self.observacao = (self.observacao or "").strip()

    def salvar(self, db_manager):
        self.validar()
        with db_manager.conectar() as conn:
            if self.id is None:
                cursor = conn.execute('''
                    INSERT INTO lancamento (descricao, valor, data, tipo, categoria_id, usuario_id, observacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (self.descricao, self.valor, self.data, self.tipo,
                      self.categoria_id, self.usuario_id, self.observacao))
                self.id = cursor.lastrowid
            else:
                cursor = conn.execute('''
                    UPDATE lancamento
                    SET descricao = ?, valor = ?, data = ?, tipo = ?, categoria_id = ?,
                        usuario_id = ?, observacao = ?
                    WHERE id = ?
                ''', (self.descricao, self.valor, self.data, self.tipo, self.categoria_id,
                      self.usuario_id, self.observacao, self.id))
                if cursor.rowcount == 0:
                    raise ValueError("Lançamento não encontrado (talvez já tenha sido excluído).")

    def excluir(self, db_manager):
        if self.id is not None:
            with db_manager.conectar() as conn:
                conn.execute("DELETE FROM lancamento WHERE id = ?", (self.id,))

    @staticmethod
    def buscar(db_manager, lanc_id):
        with db_manager.conectar() as conn:
            row = conn.execute('''
                SELECT id, descricao, valor, data, tipo, categoria_id, usuario_id, observacao
                FROM lancamento WHERE id = ?
            ''', (lanc_id,)).fetchone()
        return Lancamento(*row) if row else None

    @staticmethod
    def listar(db_manager, mes=None, ano=None, tipo=None, busca=""):
        """Lista lançamentos com filtros opcionais (mês, ano, tipo, texto)."""
        sql = '''
            SELECT l.id, l.descricao, l.valor, l.data, l.tipo, c.nome, l.observacao
            FROM lancamento l
            LEFT JOIN categoria c ON l.categoria_id = c.id
            WHERE 1 = 1
        '''
        params = []
        if mes and ano:
            inicio, fim = intervalo_mes(mes, ano)
            sql += " AND l.data >= ? AND l.data < ?"
            params += [inicio, fim]
        elif ano:
            sql += " AND l.data >= ? AND l.data < ?"
            params += [f"{ano:04d}-01-01", f"{ano + 1:04d}-01-01"]
        elif mes:
            sql += " AND substr(l.data, 6, 2) = ?"
            params.append(f"{mes:02d}")
        if tipo:
            sql += " AND l.tipo = ?"
            params.append(tipo)
        if busca:
            padrao = "%" + busca.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            sql += " AND (l.descricao LIKE ? ESCAPE '\\' OR l.observacao LIKE ? ESCAPE '\\')"
            params += [padrao, padrao]
        sql += " ORDER BY l.data DESC, l.id DESC"
        with db_manager.conectar() as conn:
            return conn.execute(sql, params).fetchall()

    @staticmethod
    def total_por_tipo(db_manager, tipo, mes, ano):
        """Soma dos lançamentos do tipo no mês (única fonte dessa consulta)."""
        inicio, fim = intervalo_mes(mes, ano)
        with db_manager.conectar() as conn:
            return conn.execute('''
                SELECT ROUND(COALESCE(SUM(valor), 0), 2) FROM lancamento
                WHERE tipo = ? AND data >= ? AND data < ?
            ''', (tipo, inicio, fim)).fetchone()[0]

    @staticmethod
    def totais_por_categoria(db_manager, tipo, mes, ano):
        """[(nome_categoria, total)] do mês, do maior para o menor."""
        inicio, fim = intervalo_mes(mes, ano)
        with db_manager.conectar() as conn:
            return conn.execute('''
                SELECT COALESCE(c.nome, 'Sem Categoria'), ROUND(SUM(l.valor), 2) AS total
                FROM lancamento l
                LEFT JOIN categoria c ON c.id = l.categoria_id
                WHERE l.tipo = ? AND l.data >= ? AND l.data < ?
                GROUP BY l.categoria_id
                ORDER BY total DESC
            ''', (tipo, inicio, fim)).fetchall()
