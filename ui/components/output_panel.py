# ui/components/output_panel.py

import tkinter as tk
from config.settings import BG_PRIMARY

try:
    from tkinterweb import HtmlFrame
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False


class OutputPanel:

    def __init__(self, parent):
       
        self._frame = tk.Frame(parent, bg=BG_PRIMARY)
        self._frame.pack(
            fill   = "both",
            expand = True,
            padx   = 20,
            pady   = (0, 20)
        )
        self._build()

    def _build(self):
        if HTML_AVAILABLE:
            # ✅ No background parameter — set after creation
            self._html = HtmlFrame(
                self._frame,
                horizontal_scrollbar = "auto"
            )
            self._html.pack(fill="both", expand=True)

            # ✅ Set background via load_html instead
            try:
                self._html.load_html(
                    "<html><body style='"
                    "background:#C6C6C6;margin:0;padding:8px;"
                    "font-family:Segoe UI,sans-serif;"
                    "color:#000000;"
                    "'></body></html>"
                )
            except Exception:
                pass

        else:
            from tkinter.scrolledtext import ScrolledText
            self._html = ScrolledText(
                self._frame,
                font   = ("Segoe UI", 11),
                bg     = "#C6C6C6",
                fg     = "#000000",
                relief = "flat"
            )
            self._html.pack(fill="both", expand=True)

    def display_html(self, html: str):
        try:
            if HTML_AVAILABLE:
                self._html.load_html(html)
            else:
                self._html.config(state="normal")
                self._html.delete("1.0", tk.END)
                self._html.insert(tk.END, html)
                self._html.config(state="disabled")
        except Exception as ex:
            print(f"⚠️ Display error: {ex}")