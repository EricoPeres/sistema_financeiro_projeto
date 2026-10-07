"""Pequenos auxiliares de widgets compartilhados pelas abas."""

import tkinter as tk


def set_entry(entry, texto):
    """Substitui o conteúdo de um Entry."""
    entry.delete(0, tk.END)
    entry.insert(0, texto)
