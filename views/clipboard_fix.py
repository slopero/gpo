"""Ctrl+V/C/X на русской раскладке + меню «Вставить» по правому клику.

Compat-фикс: на русской раскладке Windows шлёт с Ctrl символ «с», «ы», «ч»,
а не «v», «c», «x», поэтому стандартная вставка в tk.Entry не срабатывает.
Биндим кириллические алиасы на каждый Entry/Combobox и рисуем контекстное
меню по ПКМ (в tkinter его в принципе нет).
"""

import tkinter as tk
from tkinter import ttk

_EVENTS_BY_ACTION: dict[str, tuple[str, ...]] = {
    "<<Paste>>": ("<Control-Cyrillic_es>", "<Control-Cyrillic_ES>"),
    "<<Copy>>": ("<Control-Cyrillic_yeru>", "<Control-Cyrillic_YERU>"),
    "<<Cut>>": ("<Control-Cyrillic_che>", "<Control-Cyrillic_CHE>"),
}

# Не рисуем меню-привязки на уже пропатченных виджетах.
_PASTE_FIX_FLAG = "_gpo_paste_fix_installed"


def install_paste_fix(widget: tk.Misc) -> None:
    """Пройти по дереву виджетов и включить вставку/копирование/вырезание.

    Один вызов после построения окна (MainWindow, ValuationWindow).
    """

    def _generate(event: tk.Event, action: str) -> str:
        try:
            event.widget.event_generate(action)
        except tk.TclError:
            pass
        return "break"

    def _safe(w: tk.Misc, action: str) -> None:
        try:
            w.event_generate(action)
        except tk.TclError:
            pass

    def _popup_menu(event: tk.Event) -> None:
        w = event.widget
        menu = tk.Menu(w, tearoff=0)
        readonly = isinstance(w, ttk.Combobox) and "readonly" in str(w.cget("state"))
        if not readonly:
            menu.add_command(label="Вставить", command=lambda: w.event_generate("<<Paste>>"))
        menu.add_command(label="Копировать", command=lambda: _safe(w, "<<Copy>>"))
        if not readonly:
            menu.add_command(label="Вырезать", command=lambda: _safe(w, "<<Cut>>"))
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    for child in widget.winfo_children():
        install_paste_fix(child)

    if widget.winfo_class() not in ("Entry", "TEntry", "TCombobox"):
        return
    if getattr(widget, _PASTE_FIX_FLAG, False):
        return

    for action, aliases in _EVENTS_BY_ACTION.items():
        for alias in aliases:
            widget.bind(alias, lambda e, a=action: _generate(e, a))

    widget.bind("<Button-3>", _popup_menu)
    setattr(widget, _PASTE_FIX_FLAG, True)
