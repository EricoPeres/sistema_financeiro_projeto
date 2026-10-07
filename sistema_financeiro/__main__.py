"""Ponto de entrada: python -m sistema_financeiro"""

from .ui.app import AppSistemaFinanceiro


def main():
    app = AppSistemaFinanceiro()
    app.mainloop()


if __name__ == "__main__":
    main()
