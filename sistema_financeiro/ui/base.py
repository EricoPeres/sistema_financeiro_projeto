"""Classe base das abas.

Contrato: cada aba recebe a janela principal (`app`) e implementa `atualizar()`,
que relê os dados do banco e redesenha a aba. A janela chama `atualizar()` de
todas as abas depois de qualquer alteração (ver AppSistemaFinanceiro.atualizar_tudo).
"""

from tkinter import ttk


class AbaBase(ttk.Frame):
    titulo = ""   # texto exibido na aba

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.db = app.db

    def atualizar(self):
        """Recarrega os dados exibidos. Sobrescreva nas abas que mostram dados."""
