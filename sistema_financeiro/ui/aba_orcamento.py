"""Aba 4: orçamento mensal."""

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from ..config import ANO_MAX, ANO_MIN
from ..models import Orcamento
from ..utils.formatacao import formatar_brl
from ..utils.validacao import parse_valor, validar_mes_ano
from . import tema
from .base import AbaBase


class AbaOrcamento(AbaBase):
    titulo = "  Orçamento  "

    def __init__(self, master, app):
        super().__init__(master, app)
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        form = tk.LabelFrame(frame, text=" Configurar Limite de Orçamento Mensal ", padx=15, pady=15)
        form.pack(fill=tk.X, pady=10)

        tk.Label(form, text="Mês:").grid(row=0, column=0, padx=5, pady=5)
        self.spn_mes = ttk.Spinbox(form, from_=1, to=12, width=5)
        self.spn_mes.set(datetime.now().month)
        self.spn_mes.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Ano:").grid(row=0, column=2, padx=5, pady=5)
        self.spn_ano = ttk.Spinbox(form, from_=ANO_MIN, to=ANO_MAX, width=8)
        self.spn_ano.set(datetime.now().year)
        self.spn_ano.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form, text="Limite (R$):").grid(row=0, column=4, padx=5, pady=5)
        self.ent_limite = ttk.Entry(form, width=15)
        self.ent_limite.grid(row=0, column=5, padx=5, pady=5)

        tk.Button(form, text="Definir Limite", bg=tema.COR_DESTAQUE, fg=tema.COR_BRANCO,
                  command=self.salvar_orcamento).grid(row=0, column=6, padx=15, pady=5)

        self.lbl_status_orc = tk.Label(frame, text="", font=("Helvetica", 12), justify="left",
                                       bg=tema.COR_FUNDO_CLARO, pady=15)
        self.lbl_status_orc.pack(fill=tk.X, pady=15)

        tk.Button(frame, text="Consultar Status do Mês",
                  command=self.consultar_orcamento).pack(anchor="w")

    def salvar_orcamento(self):
        try:
            mes, ano = validar_mes_ano(self.spn_mes.get(), self.spn_ano.get())
            limite = parse_valor(self.ent_limite.get())
            Orcamento(mes=mes, ano=ano).definir_limite(self.db, limite)
        except (ValueError, sqlite3.Error) as erro:
            messagebox.showwarning("Verifique os dados", str(erro))
            return

        self.app.atualizar_tudo()
        self.app.status(f"Limite de {formatar_brl(limite)} definido para {mes:02d}/{ano}.")

    def consultar_orcamento(self, silencioso=False):
        try:
            mes, ano = validar_mes_ano(self.spn_mes.get(), self.spn_ano.get())
            res = Orcamento.obter_resumo(self.db, mes, ano)
        except (ValueError, sqlite3.Error) as erro:
            if not silencioso:
                messagebox.showwarning("Verifique os dados", str(erro))
            return

        msg = f"Status do Orçamento para {mes:02d}/{ano}:\n"
        msg += f" • Limite Estabelecido : {formatar_brl(res['limite'])}\n"
        msg += f" • Total Gasto no Mês  : {formatar_brl(res['gasto'])}\n"
        msg += f" • Saldo Disponível    : {formatar_brl(res['restante'])}\n"
        if res["limite"] > 0:
            pct = f"{res['gasto'] / res['limite'] * 100:.1f}".replace(".", ",")
            msg += f" • Limite utilizado    : {pct}%\n"

        if res["limite"] > 0 and res["gasto"] > res["limite"]:
            msg += f"\n [ALERTA] Você excedeu seu limite em {formatar_brl(abs(res['restante']))}!"
            self.lbl_status_orc.config(text=msg, fg=tema.COR_VERMELHO)
        else:
            self.lbl_status_orc.config(text=msg, fg=tema.COR_VERDE)

    def atualizar(self):
        self.consultar_orcamento(silencioso=True)
