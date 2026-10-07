# Sistema Financeiro Familiar | e-ST Software

Controle de contas a pagar/receber, categorias, orçamento mensal e relatórios (Python + Tkinter + SQLite, sem dependências externas).

## Como executar

```
python main.py            # ou: python -m sistema_financeiro
```

O banco `financeiro_familiar.db` fica nesta pasta. Para usar outro local, defina a variável de
ambiente `SISTEMA_FINANCEIRO_DB` com o caminho completo do arquivo.
Ao abrir um banco da versão antiga, a migração é automática (**faça uma cópia do `.db` antes**).

## Exportar o resumo para CSV

Aba **Resumo & Relatórios** → escolha mês/ano → **Exportar CSV**.

Formato "longo", fácil de filtrar/pivotar no Excel (separador `;`, decimal `,`, UTF-8 com BOM, sem `R$`):

```
Ano;Mês;Seção;Item;Valor;Percentual
2026;10;Resumo;Total de Entradas;5000,00;
2026;10;Saídas por categoria;Alimentação;1234,56;96,86
2026;10;Orçamento;Total Gasto;1274,56;127,46     <- % do limite utilizado
```

## Estrutura

```
main.py                      atalho para iniciar
sistema_financeiro/
  config.py                  constantes (tipos, limites, caminho do banco)
  database.py                conexão, esquema e migrações (PRAGMA user_version)
  exportacao.py              exportação do resumo para CSV
  utils/
    validacao.py             parse_valor, parse_data, intervalo_mes, validar_mes_ano
    formatacao.py            formatar_brl, formatar_numero, iso_para_br
    seguranca.py             hash/verificação de senha (PBKDF2)
  models/                    regras de negócio e consultas (NÃO importam tkinter)
    usuario.py  categoria.py  lancamento.py  orcamento.py
    resumo.py                dados consolidados do mês + relatório em texto
  ui/
    app.py                   janela principal (cabeçalho, status, coordena as abas)
    base.py                  AbaBase (contrato: titulo + atualizar())
    aba_home.py  aba_lancamentos.py  aba_categorias.py
    aba_orcamento.py  aba_resumo.py  aba_seguranca.py
    tema.py  widgets.py      cores e auxiliares
tests/                       testes automatizados (não exigem tkinter)
```

Camadas: `ui` → `models` → `database`/`utils` → `config`. Nada abaixo da UI importa tkinter.

## Testes

```
python -m unittest discover -s tests -t .
```

## Como estender

- **Nova aba:** crie `ui/aba_xxx.py` com uma classe que herda de `AbaBase` (defina `titulo` e `atualizar()`)
  e acrescente-a na lista `self.abas` em `ui/app.py`. Depois de qualquer alteração de dados, chame
  `self.app.atualizar_tudo()`.
- **Nova regra/consulta:** coloque no modelo correspondente em `models/` e teste em `tests/`.
- **Mudança no banco:** altere `_criar_tabelas`, crie `_migrar_para_vN` em `database.py` e aumente
  `SCHEMA_VERSION` em `config.py`.
- **Novo item no CSV:** edite `linhas_resumo()` em `exportacao.py` (e o atributo correspondente em `models/resumo.py`).

## Criado por ericodesenvolvimentodesistemas@gmail.com
