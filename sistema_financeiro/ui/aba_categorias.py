"""Aba 3: cadastro de categorias."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from ..config import TIPOS
from ..models import Categoria
from . import tema
from .base import AbaBase


class AbaCategorias(AbaBase):
    titulo = "  Categorias  "

    def __init__(self, master, app):
        super().__init__(master, app)
        frame = tk.Frame(self, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        form = tk.LabelFrame(frame, text=" Nova Categoria ", padx=10, pady=10)
        form.pack(fill=tk.X, pady=5)

        tk.Label(form, text="Nome da Categoria:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_cat_nome = ttk.Entry(form, width=25)
        self.ent_cat_nome.grid(row=0, column=1, padx=5, pady=5)
        self.ent_cat_nome.bind("<Return>", lambda _e: self.adicionar_categoria())

        tk.Label(form, text="Tipo:").grid(row=0, column=2, padx=5, pady=5)
        self.combo_cat_tipo = ttk.Combobox(form, values=list(TIPOS), state="readonly", width=12)
        self.combo_cat_tipo.set("PAGAR")
        self.combo_cat_tipo.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(form, text="Adicionar Categoria", bg=tema.COR_VERDE, fg=tema.COR_BRANCO,
                  command=self.adicionar_categoria).grid(row=0, column=4, padx=10, pady=5)
        tk.Button(form, text="Excluir Selecionada", bg=tema.COR_VERMELHO, fg=tema.COR_BRANCO,
                  command=self.excluir_categoria).grid(row=0, column=5, padx=5, pady=5)

        self.tree_cat = ttk.Treeview(frame, columns=("id", "nome", "tipo"), show="headings",
                                     selectmode="browse")
        self.tree_cat.heading("id", text="ID")
        self.tree_cat.heading("nome", text="Nome da Categoria")
        self.tree_cat.heading("tipo", text="Tipo")
        self.tree_cat.column("id", width=50, anchor="center")
        self.tree_cat.column("nome", width=300)
        self.tree_cat.column("tipo", width=150, anchor="center")
        self.tree_cat.pack(fill=tk.BOTH, expand=True, pady=10)

    def adicionar_categoria(self):
        try:
            Categoria(nome=self.ent_cat_nome.get(), tipo=self.combo_cat_tipo.get()).criar(self.db)
        except (ValueError, sqlite3.Error) as erro:
            messagebox.showwarning("Aviso", str(erro))
            return
        self.ent_cat_nome.delete(0, tk.END)
        self.app.ao_categorias_alteradas()
        self.app.status("Categoria cadastrada com sucesso.")

    def excluir_categoria(self):
        selecao = self.tree_cat.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma categoria para excluir.")
            return
        cat_id = int(selecao[0])
        nome = self.tree_cat.item(selecao[0])["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Excluir a categoria '{nome}'?"):
            return
        try:
            Categoria(cat_id=cat_id).excluir(self.db)
        except (ValueError, sqlite3.Error) as erro:
            messagebox.showwarning("Não foi possível excluir", str(erro))
            return
        self.app.ao_categorias_alteradas()
        self.app.status("Categoria excluída com sucesso.")

    def atualizar(self):
        for item in self.tree_cat.get_children():
            self.tree_cat.delete(item)
        for cid, nome, tipo in Categoria.listar_todas(self.db):
            self.tree_cat.insert("", tk.END, iid=str(cid), values=(cid, nome, tipo))
