"""Janela principal: cabeçalho, barra de status e coordenação das abas."""

import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from ..database import DatabaseManager
from . import tema
from .aba_categorias import AbaCategorias
from .aba_home import AbaHome
from .aba_lancamentos import AbaLancamentos
from .aba_orcamento import AbaOrcamento
from .aba_resumo import AbaResumo
from .aba_seguranca import AbaSeguranca


class AppSistemaFinanceiro(tk.Tk):
    def __init__(self, db=None):
        super().__init__()

        self.title("Sistema Financeiro Familiar | e-ST Software")
        self.geometry("1000x740")
        self.minsize(900, 660)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.configure(bg=tema.COR_FUNDO_CLARO)

        self.db = db or DatabaseManager()
        self._status_job = None

        self.criar_header()
        self.criar_statusbar()
        self.criar_tabs()
        self.atualizar_tudo()

    # ------------------------------------------------------------ infraestrutura

    def report_callback_exception(self, exc, val, tb):
        """Evita falhas silenciosas: mostra o erro e registra o traceback no console."""
        traceback.print_exception(exc, val, tb)
        messagebox.showerror("Erro inesperado", f"Ocorreu um erro inesperado:\n{val}")

    def status(self, mensagem, ms=5000):
        """Mensagem discreta na barra inferior (substitui pop-ups de sucesso)."""
        self.var_status.set(mensagem)
        if self._status_job is not None:
            self.after_cancel(self._status_job)
        self._status_job = self.after(ms, lambda: self.var_status.set(""))

    # ------------------------------------------------------------------ layout

    def criar_header(self):
        header = tk.Frame(self, bg=tema.COR_FUNDO_ESCURO, height=70)
        header.pack(fill=tk.X, side=tk.TOP)

        tk.Label(header, text="e-ST Software", font=("Helvetica", 20, "bold"),
                 fg=tema.COR_MARCA, bg=tema.COR_FUNDO_ESCURO).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(header, text="Sistema Financeiro Familiar", font=("Helvetica", 14),
                 fg=tema.COR_BRANCO, bg=tema.COR_FUNDO_ESCURO).pack(side=tk.LEFT, pady=10)
        tk.Label(header, text="Modo Livre (Sem Autenticação Exigida)",
                 font=("Helvetica", 9, "italic"), fg="#BDC3C7",
                 bg=tema.COR_FUNDO_ESCURO).pack(side=tk.RIGHT, padx=20, pady=10)

    def criar_statusbar(self):
        self.var_status = tk.StringVar(value="")
        tk.Label(self, textvariable=self.var_status, anchor="w", bg=tema.COR_FUNDO_CLARO,
                 fg=tema.COR_TEXTO_SUAVE, padx=12, pady=4).pack(side=tk.BOTTOM, fill=tk.X)

    def criar_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.aba_home = AbaHome(self.notebook, self)
        self.aba_lancamentos = AbaLancamentos(self.notebook, self)
        self.aba_categorias = AbaCategorias(self.notebook, self)
        self.aba_orcamento = AbaOrcamento(self.notebook, self)
        self.aba_resumo = AbaResumo(self.notebook, self)
        self.aba_seguranca = AbaSeguranca(self.notebook, self)

        # Para criar uma nova aba: crie a classe em ui/aba_xxx.py (herdando de AbaBase)
        # e acrescente-a nesta lista. A ordem aqui é a ordem das abas na tela.
        self.abas = [self.aba_home, self.aba_lancamentos, self.aba_categorias,
                     self.aba_orcamento, self.aba_resumo, self.aba_seguranca]
        for aba in self.abas:
            self.notebook.add(aba, text=aba.titulo)

    # ------------------------------------------------------------ coordenação

    def atualizar_tudo(self):
        """Reflete qualquer alteração de dados em TODAS as abas."""
        for aba in self.abas:
            aba.atualizar()

    def ao_categorias_alteradas(self):
        """Categoria criada/excluída: atualiza a lista e o combo do formulário."""
        self.aba_categorias.atualizar()
        self.aba_lancamentos.recarregar_categorias_form()
