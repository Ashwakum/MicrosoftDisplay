# ui/components/output_panel.py
import tkinter as tk

try:
    from tkinterweb import HtmlFrame
    USE_TKINTERWEB = True
except ImportError:
    USE_TKINTERWEB = False

class OutputPanel:

    def __init__(self, parent):
        self._build(parent)

    def _build(self, parent):
        frame = tk.Frame(parent, bg="#1e1e2e")
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if USE_TKINTERWEB:
            self._view = HtmlFrame(frame, horizontal_scrollbar="auto")
            self._view.pack(fill="both", expand=True)
        else:
            from tkinter.scrolledtext import ScrolledText
            self._view = ScrolledText(
                frame, font=("Segoe UI", 11),
                bg="#c6c6c6", fg="#e0e0e0",
                relief="flat", state="disabled"
            )
            self._view.pack(fill="both", expand=True)

    def display_html(self, html: str):
        if USE_TKINTERWEB:
            self._view.load_html(html)
        else:
            import re
            plain = re.sub(r"<[^>]+>", "", html)
            self._view.config(state="normal")
            self._view.delete("1.0", tk.END)
            self._view.insert(tk.END, plain)
            self._view.config(state="disabled")