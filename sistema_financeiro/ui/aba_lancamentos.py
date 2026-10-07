"""Aba 2: lançamentos (contas a pagar / a receber) com edição e filtros."""

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from ..config import ANO_MAX, ANO_MIN, TIPOS
from ..models import Categoria, Lancamento
from ..utils.formatacao import formatar_brl, iso_para_br
from ..utils.validacao import parse_data, parse_valor
from . import tema
from .base import AbaBase
from .widgets import set_entry


class AbaLancamentos(AbaBase):
    titulo = "  Lançamentos  "

    def __init__(self, master, app):
        super().__init__(master, app)
        self.lanc_id_edicao = None      # None = novo lançamento
        self.categorias_form = []       # [(id|None, nome)] do combo de categorias
        self._montar_formulario()
        self._montar_filtros()
        self._montar_tabela()
        self.carregar_categorias_combo()
        self._atualizar_modo_form()

    # ------------------------------------------------------------------ layout

    def _montar_formulario(self):
        form_frame = tk.LabelFrame(self, text=" Novo / Editar Lançamento ", padx=15, pady=10)
        form_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(form_frame, text="Descrição:").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_descricao = ttk.Entry(form_frame, width=30)
        self.ent_descricao.grid(row=0, column=1, pady=4, padx=5)

        tk.Label(form_frame, text="Valor (R$):").grid(row=0, column=2, sticky="w", pady=4)
        self.ent_valor = ttk.Entry(form_frame, width=15)
        self.ent_valor.grid(row=0, column=3, pady=4, padx=5, sticky="w")

        tk.Label(form_frame, text="Data (DD/MM/AAAA):").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_data = ttk.Entry(form_frame, width=15)
        self.ent_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_data.grid(row=1, column=1, sticky="w", pady=4, padx=5)

        tk.Label(form_frame, text="Tipo:").grid(row=1, column=2, sticky="w", pady=4)
        self.combo_tipo = ttk.Combobox(form_frame, values=list(TIPOS), state="readonly", width=12)
        self.combo_tipo.set("PAGAR")
        self.combo_tipo.grid(row=1, column=3, sticky="w", pady=4, padx=5)
        self.combo_tipo.bind("<<ComboboxSelected>>", self.ao_mudar_tipo_form)

        tk.Label(form_frame, text="Categoria:").grid(row=2, column=0, sticky="w", pady=4)
        self.combo_categoria = ttk.Combobox(form_frame, state="readonly", width=27)
        self.combo_categoria.grid(row=2, column=1, pady=4, padx=5)

        tk.Label(form_frame, text="Observação:").grid(row=2, column=2, sticky="w", pady=4)
        self.ent_obs = ttk.Entry(form_frame, width=30)
        self.ent_obs.grid(row=2, column=3, pady=4, padx=5)

        self.lbl_modo = tk.Label(form_frame, text="", font=("Helvetica", 9, "italic"),
                                 fg=tema.COR_DESTAQUE)
        self.lbl_modo.grid(row=3, column=0, columnspan=4, sticky="w")

        btn_box = tk.Frame(form_frame)
        btn_box.grid(row=4, column=0, columnspan=4, pady=8)
        self.btn_salvar = tk.Button(btn_box, text="Salvar Lançamento", bg=tema.COR_VERDE,
                                    fg=tema.COR_BRANCO, font=("Helvetica", 9, "bold"),
                                    command=self.salvar_lancamento)
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_box, text="Limpar / Novo", bg=tema.COR_CINZA, fg=tema.COR_BRANCO,
                  command=self.limpar_form_lancamento).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_box, text="Excluir Selecionado", bg=tema.COR_VERMELHO, fg=tema.COR_BRANCO,
                  command=self.excluir_lancamento).pack(side=tk.LEFT, padx=5)

    def _montar_filtros(self):
        filtro_frame = tk.LabelFrame(self, text=" Filtros ", padx=10, pady=6)
        filtro_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(filtro_frame, text="Mês:").pack(side=tk.LEFT, padx=(0, 3))
        self.combo_f_mes = ttk.Combobox(filtro_frame, state="readonly", width=7,
                                        values=["Todos"] + [f"{m:02d}" for m in range(1, 13)])
        self.combo_f_mes.set("Todos")
        self.combo_f_mes.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(filtro_frame, text="Ano:").pack(side=tk.LEFT, padx=(0, 3))
        self.combo_f_ano = ttk.Combobox(filtro_frame, state="readonly", width=7,
                                        values=["Todos"] + [str(a) for a in range(ANO_MIN, ANO_MAX + 1)])
        self.combo_f_ano.set("Todos")
        self.combo_f_ano.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(filtro_frame, text="Tipo:").pack(side=tk.LEFT, padx=(0, 3))
        self.combo_f_tipo = ttk.Combobox(filtro_frame, state="readonly", width=10,
                                         values=["Todos"] + list(TIPOS))
        self.combo_f_tipo.set("Todos")
        self.combo_f_tipo.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(filtro_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 3))
        self.ent_busca = ttk.Entry(filtro_frame, width=22)
        self.ent_busca.pack(side=tk.LEFT, padx=(0, 10))

        for combo in (self.combo_f_mes, self.combo_f_ano, self.combo_f_tipo):
            combo.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())
        self.ent_busca.bind("<Return>", lambda _e: self.atualizar())

        tk.Button(filtro_frame, text="Filtrar", command=self.atualizar).pack(side=tk.LEFT, padx=3)
        tk.Button(filtro_frame, text="Limpar filtros",
                  command=self.limpar_filtros).pack(side=tk.LEFT, padx=3)

    def _montar_tabela(self):
        # Rodapé empacotado ANTES da tabela para continuar visível ao redimensionar.
        self.lbl_totais_lanc = tk.Label(self, text="", anchor="w",
                                        font=("Helvetica", 10, "bold"), fg=tema.COR_TEXTO)
        self.lbl_totais_lanc.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 6))

        table_frame = tk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "descricao", "valor", "data", "tipo", "categoria", "observacao")
        self.tree_lancamentos = ttk.Treeview(table_frame, columns=columns, show="headings",
                                             selectmode="browse")
        titulos = {"id": "ID", "descricao": "Descrição", "valor": "Valor (R$)", "data": "Data",
                   "tipo": "Tipo", "categoria": "Categoria", "observacao": "Observação"}
        for col in columns:
            self.tree_lancamentos.heading(col, text=titulos[col])

        self.tree_lancamentos.column("id", width=40, anchor="center")
        self.tree_lancamentos.column("descricao", width=180)
        self.tree_lancamentos.column("valor", width=110, anchor="e")
        self.tree_lancamentos.column("data", width=100, anchor="center")
        self.tree_lancamentos.column("tipo", width=90, anchor="center")
        self.tree_lancamentos.column("categoria", width=130)
        self.tree_lancamentos.column("observacao", width=180)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                  command=self.tree_lancamentos.yview)
        self.tree_lancamentos.configure(yscrollcommand=scrollbar.set)
        self.tree_lancamentos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_lancamentos.bind("<<TreeviewSelect>>", self.ao_selecionar_lancamento)

    # ------------------------------------------------- categorias no formulário

    def carregar_categorias_combo(self, selecionar_id=None):
        """Carrega só as categorias do tipo escolhido (+ 'Sem categoria')."""
        tipo = self.combo_tipo.get()
        self.categorias_form = [(None, "(Sem categoria)")]
        self.categorias_form += [(c[0], c[1]) for c in Categoria.listar_todas(self.db, tipo)]

        # Lançamento antigo cuja categoria é de outro tipo: mantém a categoria visível
        # para que salvar a edição não a apague sem querer.
        if selecionar_id is not None and all(cid != selecionar_id for cid, _ in self.categorias_form):
            for cid, nome, tipo_cat in Categoria.listar_todas(self.db):
                if cid == selecionar_id:
                    self.categorias_form.append((cid, f"{nome} [{tipo_cat}]"))
                    break

        self.combo_categoria["values"] = [nome for _, nome in self.categorias_form]

        indice = 1 if len(self.categorias_form) > 1 else 0   # padrão: 1ª categoria real
        if selecionar_id is None and self.lanc_id_edicao is not None:
            indice = 0                                       # editando e sem categoria
        if selecionar_id is not None:
            for i, (cid, _) in enumerate(self.categorias_form):
                if cid == selecionar_id:
                    indice = i
                    break
        self.combo_categoria.current(indice)

    def recarregar_categorias_form(self):
        """Recarrega o combo preservando a categoria atualmente escolhida."""
        indice = self.combo_categoria.current()
        atual = self.categorias_form[indice][0] if 0 <= indice < len(self.categorias_form) else None
        self.carregar_categorias_combo(selecionar_id=atual)

    def ao_mudar_tipo_form(self, _event=None):
        self.carregar_categorias_combo()

    def _categoria_selecionada_id(self):
        indice = self.combo_categoria.current()
        if 0 <= indice < len(self.categorias_form):
            return self.categorias_form[indice][0]
        return None

    # --------------------------------------------------------- novo / edição

    def _atualizar_modo_form(self):
        if self.lanc_id_edicao is None:
            self.lbl_modo.config(text="Novo lançamento")
            self.btn_salvar.config(text="Salvar Lançamento")
        else:
            self.lbl_modo.config(
                text=f"Editando o lançamento ID {self.lanc_id_edicao} "
                     f"(use 'Limpar / Novo' para cancelar)")
            self.btn_salvar.config(text="Salvar Alterações")

    def ao_selecionar_lancamento(self, _event=None):
        """Selecionar uma linha da tabela carrega o lançamento no formulário."""
        selecao = self.tree_lancamentos.selection()
        if not selecao:
            return
        lanc = Lancamento.buscar(self.db, int(selecao[0]))
        if lanc is None:
            self.atualizar()
            return

        self.lanc_id_edicao = lanc.id
        set_entry(self.ent_descricao, lanc.descricao)
        set_entry(self.ent_valor, f"{lanc.valor:.2f}".replace(".", ","))
        set_entry(self.ent_data, iso_para_br(lanc.data))
        set_entry(self.ent_obs, lanc.observacao or "")
        self.combo_tipo.set(lanc.tipo)
        self.carregar_categorias_combo(selecionar_id=lanc.categoria_id)
        self._atualizar_modo_form()

    # ----------------------------------------------------------------- ações

    def salvar_lancamento(self):
        try:
            descricao = self.ent_descricao.get().strip()
            if not descricao:
                raise ValueError("A descrição do lançamento é obrigatória.")
            valor = parse_valor(self.ent_valor.get())
            data = parse_data(self.ent_data.get())
        except ValueError as erro:
            messagebox.showwarning("Verifique os dados", str(erro))
            return

        try:
            usuario_id = 1
            if self.lanc_id_edicao is not None:
                original = Lancamento.buscar(self.db, self.lanc_id_edicao)
                if original is not None and original.usuario_id is not None:
                    usuario_id = original.usuario_id

            lanc = Lancamento(
                lanc_id=self.lanc_id_edicao, descricao=descricao, valor=valor,
                data=data.isoformat(), tipo=self.combo_tipo.get(),
                categoria_id=self._categoria_selecionada_id(), usuario_id=usuario_id,
                observacao=self.ent_obs.get().strip(),
            )
            editando = self.lanc_id_edicao is not None
            lanc.salvar(self.db)
        except (ValueError, sqlite3.Error) as erro:
            messagebox.showerror("Erro ao salvar", str(erro))
            return

        self.limpar_form_lancamento()
        self.app.atualizar_tudo()
        self.app.status("Lançamento atualizado com sucesso." if editando
                        else "Lançamento salvo com sucesso.")

    def limpar_form_lancamento(self):
        """Limpa o formulário e volta ao modo 'novo lançamento'."""
        self.lanc_id_edicao = None
        for entry in (self.ent_descricao, self.ent_valor, self.ent_obs):
            entry.delete(0, tk.END)
        set_entry(self.ent_data, datetime.now().strftime("%d/%m/%Y"))
        selecao = self.tree_lancamentos.selection()
        if selecao:
            self.tree_lancamentos.selection_remove(*selecao)
        self.carregar_categorias_combo()
        self._atualizar_modo_form()

    def excluir_lancamento(self):
        selecao = self.tree_lancamentos.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um lançamento para excluir.")
            return

        lanc_id = int(selecao[0])
        if not messagebox.askyesno("Confirmar Exclusão",
                                   f"Deseja realmente excluir o lançamento ID {lanc_id}?"):
            return
        try:
            Lancamento(lanc_id=lanc_id).excluir(self.db)
        except sqlite3.Error as erro:
            messagebox.showerror("Erro ao excluir", str(erro))
            return

        if self.lanc_id_edicao == lanc_id:
            self.limpar_form_lancamento()
        self.app.atualizar_tudo()
        self.app.status("Lançamento excluído com sucesso.")

    # ----------------------------------------------------------------- filtros

    def limpar_filtros(self):
        self.combo_f_mes.set("Todos")
        self.combo_f_ano.set("Todos")
        self.combo_f_tipo.set("Todos")
        self.ent_busca.delete(0, tk.END)
        self.atualizar()

    def ler_filtros(self):
        mes = self.combo_f_mes.get()
        ano = self.combo_f_ano.get()
        tipo = self.combo_f_tipo.get()
        return (
            int(mes) if mes != "Todos" else None,
            int(ano) if ano != "Todos" else None,
            tipo if tipo != "Todos" else None,
            self.ent_busca.get().strip(),
        )

    def atualizar(self):
        """Recarrega a tabela respeitando os filtros (não mexe no formulário)."""
        mes, ano, tipo, busca = self.ler_filtros()
        try:
            rows = Lancamento.listar(self.db, mes=mes, ano=ano, tipo=tipo, busca=busca)
        except (ValueError, sqlite3.Error) as erro:
            messagebox.showerror("Erro", f"Não foi possível carregar os lançamentos:\n{erro}")
            return

        for item in self.tree_lancamentos.get_children():
            self.tree_lancamentos.delete(item)

        entradas = saidas = 0.0
        for lid, descricao, valor, data, tipo_l, categoria, obs in rows:
            self.tree_lancamentos.insert(
                "", tk.END, iid=str(lid),
                values=(lid, descricao, formatar_brl(valor), iso_para_br(data), tipo_l,
                        categoria or "Sem Categoria", obs or ""))
            if tipo_l == "RECEBER":
                entradas += valor
            else:
                saidas += valor

        entradas, saidas = round(entradas, 2), round(saidas, 2)
        self.lbl_totais_lanc.config(
            text=f"{len(rows)} lançamento(s)  |  Entradas: {formatar_brl(entradas)}  |  "
                 f"Saídas: {formatar_brl(saidas)}  |  Saldo: {formatar_brl(round(entradas - saidas, 2))}")
