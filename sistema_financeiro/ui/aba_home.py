"""Aba 1: tela inicial com visão geral do mês atual."""

import tkinter as tk

from ..models import ResumoFinanceiro
from ..utils.formatacao import formatar_brl
from . import tema
from .base import AbaBase


class AbaHome(AbaBase):
    titulo = "  Início (e-ST Software)  "

    def __init__(self, master, app):
        super().__init__(master, app)
        frame = tk.Frame(self, bg=tema.COR_BRANCO, padx=30, pady=30)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Bem-vindo ao Sistema Financeiro Familiar",
                 font=("Helvetica", 18, "bold"), bg=tema.COR_BRANCO,
                 fg=tema.COR_FUNDO_ESCURO).pack(anchor="w", pady=(0, 5))
        tk.Label(frame, text="Desenvolvido por: e-ST Software — Soluções em Tecnologia",
                 font=("Helvetica", 11, "bold"), bg=tema.COR_BRANCO,
                 fg=tema.COR_DESTAQUE).pack(anchor="w", pady=(0, 20))

        info_text = (
            "Esta aplicação foi gerada com base no Diagrama UML de Sistema Financeiro Familiar.\n"
            "Atualmente o sistema está configurado no MODO LIVRE (sem necessidade de usuário e senha),\n"
            "permitindo navegação e uso imediato de todas as funcionalidades de gestão financeira.\n\n"
            "Recursos do Sistema:\n"
            " • Cadastrar e Gerenciar Contas a Pagar e a Receber (com edição e filtros)\n"
            " • Organização por Categorias Personalizadas\n"
            " • Definição e Controle de Limites de Orçamento Mensal\n"
            " • Emissão de Resumo Financeiro e Relatórios por Categoria\n"
            " • Exportação do Resumo Financeiro para CSV (Excel)\n"
            " • Módulo preparado para futura ativação de Login com Senha\n"
        )
        tk.Label(frame, text=info_text, font=("Helvetica", 10), justify="left",
                 bg=tema.COR_BRANCO, fg=tema.COR_TEXTO_SUAVE).pack(anchor="w", pady=(0, 25))

        kpi_frame = tk.LabelFrame(frame, text=" Visão Geral do Mês Atual ",
                                  font=("Helvetica", 11, "bold"), bg=tema.COR_BRANCO,
                                  padx=15, pady=15)
        kpi_frame.pack(fill=tk.X, pady=10)

        self.lbl_rec = tk.Label(kpi_frame, text="", font=("Helvetica", 12, "bold"),
                                fg=tema.COR_VERDE, bg=tema.COR_BRANCO)
        self.lbl_rec.grid(row=0, column=0, padx=20, pady=10)
        self.lbl_pag = tk.Label(kpi_frame, text="", font=("Helvetica", 12, "bold"),
                                fg=tema.COR_VERMELHO, bg=tema.COR_BRANCO)
        self.lbl_pag.grid(row=0, column=1, padx=20, pady=10)
        self.lbl_sal = tk.Label(kpi_frame, text="", font=("Helvetica", 12, "bold"),
                                fg=tema.COR_VERDE, bg=tema.COR_BRANCO)
        self.lbl_sal.grid(row=0, column=2, padx=20, pady=10)

    def atualizar(self):
        resumo = ResumoFinanceiro()
        resumo.calcular(self.db)
        self.lbl_rec.config(text=f"Entradas do mês: {formatar_brl(resumo.total_receber)}")
        self.lbl_pag.config(text=f"Saídas do mês: {formatar_brl(resumo.total_pagar)}")
        self.lbl_sal.config(text=f"Saldo do mês: {formatar_brl(resumo.saldo)}",
                            fg=tema.COR_VERDE if resumo.saldo >= 0 else tema.COR_VERMELHO)
