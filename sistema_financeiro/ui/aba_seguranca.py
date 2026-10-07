"""Aba 6: segurança e futura autenticação."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog

from ..config import SENHA_INICIAL_ADMIN, SENHA_MIN
from ..models import Usuario
from . import tema
from .base import AbaBase


class AbaSeguranca(AbaBase):
    titulo = "  Segurança (Futuro Login)  "

    def __init__(self, master, app):
        super().__init__(master, app)
        frame = tk.Frame(self, padx=25, pady=25)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Módulo de Segurança e Futura Autenticação",
                 font=("Helvetica", 14, "bold"),
                 fg=tema.COR_FUNDO_ESCURO).pack(anchor="w", pady=(0, 10))

        info = (
            "Conforme solicitado à e-ST Software, a tela inicial atual não exige login/senha.\n"
            "A estrutura de banco de dados e os métodos da classe Usuario (autenticar e alterar_senha)\n"
            "estão implementados e prontos para uso futuro. As senhas são gravadas apenas como hash.\n"
        )
        tk.Label(frame, text=info, font=("Helvetica", 10), justify="left",
                 fg=tema.COR_TEXTO_SUAVE).pack(anchor="w", pady=(0, 20))

        box_user = tk.LabelFrame(frame, text=" Cadastro de Usuários e Senhas ", padx=15, pady=15)
        box_user.pack(fill=tk.X, pady=10)

        tk.Label(box_user, text="Usuário Administrador Padrão: Administrador").pack(anchor="w", pady=2)
        tk.Label(box_user,
                 text=f"Senha inicial: {SENHA_INICIAL_ADMIN} (altere antes de ativar o login)",
                 fg=tema.COR_TEXTO_SUAVE).pack(anchor="w", pady=2)

        tk.Button(box_user, text="Alterar Senha do Administrador", bg=tema.COR_LARANJA,
                  fg=tema.COR_BRANCO, command=self.alterar_senha_admin).pack(anchor="w", pady=10)

    def alterar_senha_admin(self):
        usuario = Usuario.buscar_por_nome(self.db, "Administrador")
        if usuario is None:
            messagebox.showerror("Erro", "Usuário Administrador não encontrado.")
            return

        atual = simpledialog.askstring("Alterar Senha", "Digite a senha atual:",
                                       show="*", parent=self.app)
        if atual is None:
            return
        nova = simpledialog.askstring("Alterar Senha",
                                      f"Digite a nova senha (mínimo {SENHA_MIN} caracteres):",
                                      show="*", parent=self.app)
        if nova is None:
            return
        confirmacao = simpledialog.askstring("Alterar Senha", "Repita a nova senha:",
                                             show="*", parent=self.app)
        if confirmacao is None:
            return
        if nova != confirmacao:
            messagebox.showerror("Erro", "A confirmação não confere com a nova senha.")
            return

        try:
            usuario.alterar_senha(self.db, atual, nova)
        except (ValueError, sqlite3.Error) as erro:
            messagebox.showerror("Erro", str(erro))
            return
        self.app.status("Senha alterada com sucesso.")
