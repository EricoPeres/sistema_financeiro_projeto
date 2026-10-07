"""Aba 5: resumo financeiro, relatório em tela e exportação para CSV."""

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from ..config import ANO_MAX, ANO_MIN
from ..exportacao import exportar_resumo_csv
from ..models import ResumoFinanceiro
from ..utils.validacao import validar_mes_ano
from . import tema
from .base import AbaBase


class AbaResumo(AbaBase):
    titulo = "  Resumo & Relatórios  "

    def __init__(self, master, app):
        super().__init__(master, app)
        frame = tk.Frame(self, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ctrl_frame = tk.Frame(frame)
        ctrl_frame.pack(fill=tk.X, pady=5)

        tk.Label(ctrl_frame, text="Mês:").pack(side=tk.LEFT, padx=5)
        self.spn_res_mes = ttk.Spinbox(ctrl_frame, from_=1, to=12, width=5)
        self.spn_res_mes.set(datetime.now().month)
        self.spn_res_mes.pack(side=tk.LEFT, padx=5)

        tk.Label(ctrl_frame, text="Ano:").pack(side=tk.LEFT, padx=5)
        self.spn_res_ano = ttk.Spinbox(ctrl_frame, from_=ANO_MIN, to=ANO_MAX, width=8)
        self.spn_res_ano.set(datetime.now().year)
        self.spn_res_ano.pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="Gerar Relatório Completo", bg=tema.COR_DESTAQUE,
                  fg=tema.COR_BRANCO, command=self.gerar_relatorio).pack(side=tk.LEFT, padx=15)
        tk.Button(ctrl_frame, text="Exportar CSV", bg=tema.COR_VERDE, fg=tema.COR_BRANCO,
                  command=self.exportar_csv).pack(side=tk.LEFT, padx=5)

        self.txt_relatorio = tk.Text(frame, font=("Courier", 11), bg=tema.COR_FUNDO_ESCURO,
                                     fg=tema.COR_FUNDO_CLARO, padx=10, pady=10, state=tk.DISABLED)
        self.txt_relatorio.pack(fill=tk.BOTH, expand=True, pady=10)

    def _ler_periodo(self):
        return validar_mes_ano(self.spn_res_mes.get(), self.spn_res_ano.get())

    def gerar_relatorio(self, silencioso=False):
        try:
            mes, ano = self._ler_periodo()
            texto = ResumoFinanceiro(mes=mes, ano=ano).gerar_relatorio(self.db)
        except (ValueError, sqlite3.Error) as erro:
            if not silencioso:
                messagebox.showwarning("Verifique os dados", str(erro))
            return

        self.txt_relatorio.config(state=tk.NORMAL)
        self.txt_relatorio.delete("1.0", tk.END)
        self.txt_relatorio.insert(tk.END, texto)
        self.txt_relatorio.config(state=tk.DISABLED)

    def exportar_csv(self):
        """Exporta o resumo do mês/ano selecionado para um arquivo CSV."""
        try:
            mes, ano = self._ler_periodo()
        except ValueError as erro:
            messagebox.showwarning("Verifique os dados", str(erro))
            return

        caminho = filedialog.asksaveasfilename(
            parent=self.app,
            title="Exportar resumo financeiro",
            defaultextension=".csv",
            initialfile=f"resumo_financeiro_{ano}-{mes:02d}.csv",
            filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:      # usuário cancelou
            return

        try:
            exportar_resumo_csv(self.db, mes, ano, caminho)
        except PermissionError:
            messagebox.showerror(
                "Não foi possível exportar",
                "Sem permissão para gravar o arquivo. Se ele estiver aberto no Excel, "
                "feche-o e tente novamente.")
            return
        except (OSError, ValueError, sqlite3.Error) as erro:
            messagebox.showerror("Não foi possível exportar", str(erro))
            return

        self.app.status(f"Resumo de {mes:02d}/{ano} exportado para: {caminho}", ms=10000)

    def atualizar(self):
        self.gerar_relatorio(silencioso=True)
