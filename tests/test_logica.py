"""Testes da lógica (utilitários, banco, migração e modelos). Não exigem tkinter."""

import os
import sqlite3
import tempfile
import unittest

from sistema_financeiro.database import DatabaseManager
from sistema_financeiro.models import Categoria, Lancamento, Orcamento, ResumoFinanceiro, Usuario
from sistema_financeiro.utils import (
    formatar_brl, formatar_numero, hash_senha, intervalo_mes, iso_para_br,
    parse_data, parse_valor, validar_mes_ano, verificar_senha,
)


def banco_temporario():
    return DatabaseManager(os.path.join(tempfile.mkdtemp(), "teste.db"))


class TestUtilitarios(unittest.TestCase):
    def test_parse_valor_formatos(self):
        self.assertEqual(parse_valor("1234.56"), 1234.56)
        self.assertEqual(parse_valor("1234,56"), 1234.56)
        self.assertEqual(parse_valor("1.234,56"), 1234.56)
        self.assertEqual(parse_valor("R$ 10,5"), 10.5)
        self.assertEqual(parse_valor("0,005"), 0.01)

    def test_parse_valor_invalidos(self):
        for ruim in ["", "abc", "nan", "inf", "-5", "0", "1e30", "  "]:
            with self.subTest(ruim=ruim):
                with self.assertRaises(ValueError):
                    parse_valor(ruim)

    def test_parse_data(self):
        self.assertEqual(str(parse_data("06/10/2026")), "2026-10-06")
        self.assertEqual(str(parse_data("2026-10-06")), "2026-10-06")
        for ruim in ["31/02/2026", "2026-13-01", "abc", "", "06/10/1500"]:
            with self.subTest(ruim=ruim):
                with self.assertRaises(ValueError):
                    parse_data(ruim)

    def test_formatacao(self):
        self.assertEqual(iso_para_br("2026-10-06"), "06/10/2026")
        self.assertEqual(iso_para_br("lixo"), "lixo")
        self.assertEqual(formatar_brl(1234.5), "R$ 1.234,50")
        self.assertEqual(formatar_brl(1234567.891), "R$ 1.234.567,89")
        self.assertEqual(formatar_brl(-0.5), "R$ -0,50")
        self.assertEqual(formatar_brl(-0.0), "R$ 0,00")
        self.assertEqual(formatar_numero(1234.5), "1234,50")
        self.assertEqual(formatar_numero(1234.5, decimal="."), "1234.50")
        self.assertEqual(formatar_numero(-0.001), "0,00")

    def test_intervalos(self):
        self.assertEqual(intervalo_mes(12, 2026), ("2026-12-01", "2027-01-01"))
        self.assertEqual(intervalo_mes(2, 2024), ("2024-02-01", "2024-03-01"))
        with self.assertRaises(ValueError):
            intervalo_mes(13, 2026)
        self.assertEqual(validar_mes_ano("10", "2026"), (10, 2026))
        for mes, ano in [("abc", "2026"), ("0", "2026"), ("5", "1800"), ("", "")]:
            with self.assertRaises(ValueError):
                validar_mes_ano(mes, ano)

    def test_hash_senha(self):
        h = hash_senha("segredo")
        self.assertTrue(verificar_senha("segredo", h))
        self.assertFalse(verificar_senha("errada", h))
        self.assertNotEqual(h, hash_senha("segredo"))            # salt aleatório
        self.assertFalse(verificar_senha("x", "1234"))           # hash malformado
        self.assertFalse(verificar_senha("x", ""))


class TestMigracao(unittest.TestCase):
    def setUp(self):
        self.caminho = os.path.join(tempfile.mkdtemp(), "legado.db")
        c = sqlite3.connect(self.caminho)
        c.executescript('''
        CREATE TABLE usuario (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, senha TEXT NOT NULL);
        CREATE TABLE categoria (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('PAGAR','RECEBER')) NOT NULL);
        CREATE TABLE lancamento (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT NOT NULL,
            valor REAL NOT NULL, data TEXT NOT NULL, tipo TEXT CHECK(tipo IN ('PAGAR','RECEBER')) NOT NULL,
            categoria_id INTEGER, usuario_id INTEGER, observacao TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categoria (id), FOREIGN KEY (usuario_id) REFERENCES usuario (id));
        CREATE TABLE orcamento (id INTEGER PRIMARY KEY AUTOINCREMENT, mes INTEGER NOT NULL,
            ano INTEGER NOT NULL, valor_limite REAL NOT NULL, UNIQUE(mes, ano));
        INSERT INTO usuario (nome, senha) VALUES ('Administrador', '1234');
        INSERT INTO categoria (nome, tipo) VALUES ('Alimentação','PAGAR'), ('Salário','RECEBER');
        INSERT INTO lancamento (descricao, valor, data, tipo, categoria_id, usuario_id) VALUES
         ('Mercado', 100.10, '06/10/2026', 'PAGAR', 1, 1),
         ('Padaria', 20.20, '2026-10-05', 'PAGAR', 1, 1),
         ('Lixo', 5, 'abc', 'PAGAR', 1, 1),
         ('Salario', 3000, '2026-10-01', 'RECEBER', 2, 1);
        ''')
        c.commit()
        c.close()

    def test_migra_senha_e_datas(self):
        db = DatabaseManager(self.caminho)
        with db.conectar() as conn:
            senha = conn.execute("SELECT senha FROM usuario").fetchone()[0]
            datas = dict(conn.execute("SELECT descricao, data FROM lancamento").fetchall())
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertTrue(senha.startswith("pbkdf2_sha256$"))
        self.assertTrue(verificar_senha("1234", senha))
        self.assertEqual(datas["Mercado"], "2026-10-06")     # DD/MM/AAAA normalizada
        self.assertEqual(datas["Lixo"], "abc")               # irreconhecível: preservada

    def test_migracao_idempotente_e_totais(self):
        db = DatabaseManager(self.caminho)
        with db.conectar() as conn:
            antes = conn.execute("SELECT senha FROM usuario").fetchone()[0]
        db = DatabaseManager(self.caminho)                   # reabre
        with db.conectar() as conn:
            self.assertEqual(conn.execute("SELECT senha FROM usuario").fetchone()[0], antes)
        self.assertEqual(Lancamento.total_por_tipo(db, "PAGAR", 10, 2026), 120.30)
        self.assertEqual(Lancamento.total_por_tipo(db, "RECEBER", 10, 2026), 3000)
        self.assertEqual(Lancamento.total_por_tipo(db, "PAGAR", 11, 2026), 0)


class TestModelos(unittest.TestCase):
    def setUp(self):
        self.db = banco_temporario()

    def test_dados_padrao(self):
        with self.db.conectar() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM categoria").fetchone()[0], 8)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0], 1)

    def test_usuario(self):
        u = Usuario.buscar_por_nome(self.db, "Administrador")
        self.assertTrue(u.autenticar("1234"))
        self.assertFalse(u.autenticar("0000"))
        with self.assertRaises(ValueError):
            u.alterar_senha(self.db, "errada", "novasenha")
        with self.assertRaises(ValueError):
            u.alterar_senha(self.db, "1234", "123")
        u.alterar_senha(self.db, "1234", "novasenha")
        self.assertTrue(Usuario.buscar_por_nome(self.db, "Administrador").autenticar("novasenha"))
        self.assertIsNone(Usuario.buscar_por_nome(self.db, "Fulano"))

    def test_categorias(self):
        self.assertEqual(len(Categoria.listar_todas(self.db, "PAGAR")), 5)
        with self.assertRaises(ValueError):
            Categoria(nome="  ", tipo="PAGAR").criar(self.db)
        with self.assertRaises(ValueError):
            Categoria(nome="alimentação", tipo="PAGAR").criar(self.db)   # duplicada
        Categoria(nome="Alimentação", tipo="RECEBER").criar(self.db)     # tipo diferente: ok
        with self.assertRaises(ValueError):
            Categoria(nome="x", tipo="FOO").criar(self.db)

    def test_categoria_em_uso(self):
        alim = [c for c in Categoria.listar_todas(self.db, "PAGAR") if c[1] == "Alimentação"][0][0]
        Lancamento(descricao="Feira", valor=50.5, data="06/10/2026", tipo="PAGAR",
                   categoria_id=alim).salvar(self.db)
        with self.assertRaises(ValueError):
            Categoria(cat_id=alim).excluir(self.db)
        with self.assertRaises(ValueError):
            Categoria(cat_id=alim, nome="Alimentação", tipo="RECEBER").editar(self.db)
        livre = Categoria(nome="Temp", tipo="PAGAR")
        livre.criar(self.db)
        livre.excluir(self.db)
        self.assertTrue(all(c[1] != "Temp" for c in Categoria.listar_todas(self.db)))

    def test_lancamento_validacoes(self):
        base = dict(descricao="x", valor=1, data="2026-10-06")
        casos = [dict(valor=float("nan")), dict(valor=-1), dict(data="lixo"), dict(descricao=""),
                 dict(lanc_id=9999)]                     # update de id inexistente
        for caso in casos:
            with self.subTest(caso=caso):
                with self.assertRaises(ValueError):
                    Lancamento(**{**base, **caso}).salvar(self.db)
        with self.assertRaises(sqlite3.IntegrityError):  # FK ativa
            Lancamento(**base, categoria_id=424242).salvar(self.db)

    def test_lancamento_normaliza_e_edita(self):
        lanc = Lancamento(descricao="Feira", valor=50.5, data="06/10/2026")
        lanc.salvar(self.db)
        self.assertEqual(lanc.data, "2026-10-06")
        b = Lancamento.buscar(self.db, lanc.id)
        b.valor, b.descricao = 60.0, "Feira grande"
        b.salvar(self.db)
        self.assertEqual(Lancamento.buscar(self.db, lanc.id).valor, 60.0)

    def test_soma_sem_erro_de_float(self):
        for _ in range(10):
            Lancamento(descricao="c", valor=0.1, data="2025-03-10", tipo="RECEBER").salvar(self.db)
        self.assertEqual(Lancamento.total_por_tipo(self.db, "RECEBER", 3, 2025), 1.0)

    def test_filtros_e_busca(self):
        Lancamento(descricao="Feira", valor=60, data="2026-10-06").salvar(self.db)
        Lancamento(descricao="100% suco_gelado", valor=5, data="2026-09-30").salvar(self.db)
        for _ in range(3):
            Lancamento(descricao="c", valor=1, data="2025-03-10", tipo="RECEBER").salvar(self.db)
        n = lambda **k: len(Lancamento.listar(self.db, **k))
        self.assertEqual(n(mes=9, ano=2026), 1)
        self.assertEqual(n(ano=2026), 2)
        self.assertEqual(n(mes=3), 3)
        self.assertEqual(n(tipo="RECEBER"), 3)
        self.assertEqual(n(busca="100%"), 1)
        self.assertEqual(n(busca="_gelado"), 1)
        self.assertEqual(n(busca="%"), 1)                # '%' é literal, não curinga
        self.assertEqual(n(busca="FEIRA"), 1)
        datas = [r[3] for r in Lancamento.listar(self.db)]
        self.assertEqual(datas, sorted(datas, reverse=True))

    def test_orcamento_e_relatorio(self):
        alim = [c for c in Categoria.listar_todas(self.db, "PAGAR") if c[1] == "Alimentação"][0][0]
        Lancamento(descricao="Feira", valor=60, data="2026-10-06", categoria_id=alim).salvar(self.db)
        o = Orcamento(mes=10, ano=2026)
        with self.assertRaises(ValueError):
            o.definir_limite(self.db, 0)
        with self.assertRaises(ValueError):
            o.definir_limite(self.db, float("inf"))
        with self.assertRaises(ValueError):
            Orcamento(mes=13, ano=2026).definir_limite(self.db, 10)
        o.definir_limite(self.db, 100.0)
        o.definir_limite(self.db, 50.0)                  # upsert
        r = Orcamento.obter_resumo(self.db, 10, 2026)
        self.assertEqual((r["limite"], r["gasto"], r["restante"]), (50.0, 60.0, -10.0))
        rel = ResumoFinanceiro(10, 2026).gerar_relatorio(self.db)
        for trecho in ("ALERTA", "Alimentação", "R$ 60,00", "100,0%"):
            self.assertIn(trecho, rel)


if __name__ == "__main__":
    unittest.main()
