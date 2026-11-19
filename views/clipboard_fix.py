"""Ctrl+V/C/X на русской раскладке + меню «Вставить» по правому клику.

На русской раскладке Windows шлёт с Ctrl не «v», а «м» (физическая клавиша V),
поэтому стандартная вставка в tk.Entry не срабатывает. Биндим кириллические
клавиши (Cyrillic_em/es/che) и страхуемся фолбэком по keycode физической
клавиши, если Tk сообщает нестандартные keysym. Плюс Shift+Insert.
"""

import tkinter as tk
from tkinter import ttk

# Кириллические keysym: V -> «м», C -> «с», X -> «ч» (раскладка ЙЦУКЕН).
_EVENTS_BY_ACTION: dict[str, tuple[str, ...]] = {
    "<<Paste>>": ("<Control-Cyrillic_em>", "<Control-Cyrillic_EM>"),
    "<<Copy>>": ("<Control-Cyrillic_es>", "<Control-Cyrillic_ES>"),
    "<<Cut>>": ("<Control-Cyrillic_che>", "<Control-Cyrillic_CHE>"),
}

_CYRILLIC_KEYSYMS: dict[str, str] = {
    "cyrillic_em": "<<Paste>>",
    "cyrillic_es": "<<Copy>>",
    "cyrillic_che": "<<Cut>>",
}

# Фолбэк: физические клавиши V/C/X (Windows virtual-key codes).
_CTRL_KEYCODES: dict[int, str] = {
    86: "<<Paste>>",  # V
    67: "<<Copy>>",   # C
    88: "<<Cut>>",    # X
}

# Не рисуем меню-привязки на уже пропатченных виджетах.
_PASTE_FIX_FLAG = "_gpo_paste_fix_installed"


def install_paste_fix(widget: tk.Misc) -> None:
    """Пройти по дереву виджетов и включить вставку/копирование/вырезание.

    Один вызов после построения окна (MainWindow, ValuationWindow, диалоги).
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

    def _on_ctrl_keypress(event: tk.Event) -> str | None:
        keysym = str(getattr(event, "keysym", "")).lower()
        # Латинские v/c/x Tk обрабатывает сам — не мешаем и не дублируем.
        if keysym in ("v", "c", "x"):
            return None
        action = _CYRILLIC_KEYSYMS.get(keysym)
        if action is None:
            action = _CTRL_KEYCODES.get(getattr(event, "keycode", None))
        if action is None:
            return None
        try:
            event.widget.event_generate(action)
        except tk.TclError:
            return None
        return "break"

    def _popup_menu(event: tk.Event) -> str:
        w = event.widget
        menu = tk.Menu(w, tearoff=0)
        readonly = isinstance(w, ttk.Combobox) and "readonly" in str(w.cget("state"))
        if not readonly:
            menu.add_command(label="Вставить", command=lambda: _safe(w, "<<Paste>>"))
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

    widget.bind("<Control-KeyPress>", _on_ctrl_keypress)
    widget.bind("<Shift-Insert>", lambda e: _generate(e, "<<Paste>>"))
    widget.bind("<Button-3>", _popup_menu)
    setattr(widget, _PASTE_FIX_FLAG, True)
