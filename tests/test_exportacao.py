"""Testes da exportação do resumo financeiro para CSV."""

import csv
import io
import os
import tempfile
import unittest

from sistema_financeiro.database import DatabaseManager
from sistema_financeiro.exportacao import (
    CABECALHO, exportar_resumo_csv, gerar_csv_resumo, texto_seguro,
)
from sistema_financeiro.models import Categoria, Lancamento, Orcamento


def ler_csv(caminho, delimitador=";"):
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter=delimitador))


class TestExportacaoCSV(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.db = DatabaseManager(os.path.join(self.pasta, "t.db"))
        cats = {c[1]: c[0] for c in Categoria.listar_todas(self.db)}
        Lancamento(descricao="Mercado", valor=1234.56, data="2026-10-06", tipo="PAGAR",
                   categoria_id=cats["Alimentação"]).salvar(self.db)
        Lancamento(descricao="Cinema", valor=40, data="2026-10-10", tipo="PAGAR",
                   categoria_id=cats["Lazer"]).salvar(self.db)
        Lancamento(descricao="Salário", valor=5000, data="2026-10-01", tipo="RECEBER",
                   categoria_id=cats["Salário"]).salvar(self.db)
        Lancamento(descricao="Outro mês", valor=999, data="2026-09-30", tipo="PAGAR").salvar(self.db)
        Orcamento(mes=10, ano=2026).definir_limite(self.db, 1000.0)
        self.caminho = os.path.join(self.pasta, "saida.csv")

    def linhas_por_chave(self, linhas):
        return {(l[2], l[3]): l for l in linhas[1:]}

    def test_arquivo_estrutura_e_valores(self):
        exportar_resumo_csv(self.db, 10, 2026, self.caminho)
        linhas = ler_csv(self.caminho)
        self.assertEqual(tuple(linhas[0]), CABECALHO)
        self.assertTrue(all(len(l) == len(CABECALHO) for l in linhas))
        idx = self.linhas_por_chave(linhas)

        self.assertEqual(idx[("Resumo", "Total de Entradas")][4], "5000,00")
        self.assertEqual(idx[("Resumo", "Total de Saídas")][4], "1274,56")       # sem 'Outro mês'
        self.assertEqual(idx[("Resumo", "Saldo do Mês")][4], "3725,44")
        self.assertEqual(idx[("Saídas por categoria", "Alimentação")][4:], ["1234,56", "96,86"])
        self.assertEqual(idx[("Saídas por categoria", "Lazer")][4:], ["40,00", "3,14"])
        self.assertEqual(idx[("Entradas por categoria", "Salário")][4:], ["5000,00", "100,00"])
        self.assertEqual(idx[("Orçamento", "Limite Definido")][4], "1000,00")
        self.assertEqual(idx[("Orçamento", "Total Gasto")][4:], ["1274,56", "127,46"])
        self.assertEqual(idx[("Orçamento", "Saldo do Orçamento")][4], "-274,56")
        self.assertTrue(all(l[0] == "2026" and l[1] == "10" for l in linhas[1:]))

    def test_bate_com_o_relatorio_em_tela(self):
        """CSV e relatório vêm da mesma fonte: os totais precisam coincidir."""
        from sistema_financeiro.models import ResumoFinanceiro
        rel = ResumoFinanceiro(10, 2026).gerar_relatorio(self.db)
        self.assertIn("R$ 1.274,56", rel)
        self.assertIn("R$ 3.725,44", rel)

    def test_bom_e_codificacao(self):
        exportar_resumo_csv(self.db, 10, 2026, self.caminho)
        with open(self.caminho, "rb") as f:
            self.assertEqual(f.read(3), b"\xef\xbb\xbf")        # BOM p/ o Excel
        with open(self.caminho, encoding="utf-8-sig") as f:
            self.assertIn("Mês;Seção", f.readline())

    def test_delimitador_e_decimal_configuraveis(self):
        exportar_resumo_csv(self.db, 10, 2026, self.caminho, delimitador=",", decimal=".")
        idx = self.linhas_por_chave(ler_csv(self.caminho, ","))
        self.assertEqual(idx[("Resumo", "Total de Entradas")][4], "5000.00")
        with self.assertRaises(ValueError):
            gerar_csv_resumo(self.db, 10, 2026, delimitador=",", decimal=",")
        with self.assertRaises(ValueError):
            gerar_csv_resumo(self.db, 10, 2026, delimitador=";;")

    def test_mes_sem_dados(self):
        exportar_resumo_csv(self.db, 1, 2026, self.caminho)
        idx = self.linhas_por_chave(ler_csv(self.caminho))
        self.assertEqual(idx[("Resumo", "Saldo do Mês")][4], "0,00")
        self.assertEqual(idx[("Orçamento", "Total Gasto")][5], "")  # sem limite: sem %
        self.assertFalse(any(k[0].endswith("por categoria") for k in idx))

    def test_nome_de_categoria_nao_vira_formula(self):
        Categoria(nome="=1+1", tipo="PAGAR").criar(self.db)
        cat = [c for c in Categoria.listar_todas(self.db) if c[1] == "=1+1"][0][0]
        Lancamento(descricao="x", valor=10, data="2026-10-12", categoria_id=cat).salvar(self.db)
        exportar_resumo_csv(self.db, 10, 2026, self.caminho)
        itens = [l[3] for l in ler_csv(self.caminho)[1:]]
        self.assertIn("'=1+1", itens)
        self.assertNotIn("=1+1", itens)
        self.assertEqual(texto_seguro("@soma"), "'@soma")
        self.assertEqual(texto_seguro("Lazer"), "Lazer")

    def test_categoria_com_delimitador_e_aspas(self):
        Categoria(nome='Pão; "caseiro"', tipo="PAGAR").criar(self.db)
        cat = [c for c in Categoria.listar_todas(self.db) if c[1].startswith("Pão")][0][0]
        Lancamento(descricao="x", valor=10, data="2026-10-12", categoria_id=cat).salvar(self.db)
        exportar_resumo_csv(self.db, 10, 2026, self.caminho)
        self.assertIn('Pão; "caseiro"', [l[3] for l in ler_csv(self.caminho)])   # ida e volta íntegra

    def test_erros(self):
        with self.assertRaises(ValueError):
            exportar_resumo_csv(self.db, 13, 2026, self.caminho)
        self.assertFalse(os.path.exists(self.caminho))              # nada gravado
        with self.assertRaises(OSError):
            exportar_resumo_csv(self.db, 10, 2026, os.path.join(self.pasta, "nao_existe", "a.csv"))

    def test_sobrescreve_arquivo_existente(self):
        with open(self.caminho, "w") as f:
            f.write("lixo antigo" * 1000)
        exportar_resumo_csv(self.db, 10, 2026, self.caminho)
        self.assertEqual(tuple(ler_csv(self.caminho)[0]), CABECALHO)


if __name__ == "__main__":
    unittest.main()
