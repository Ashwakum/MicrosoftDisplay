# ui/components/input_panel.py

import tkinter as tk
import time
from config.settings import (
    BG_PRIMARY, BG_SECONDARY, ACCENT_COLOR,
    TEXT_COLOR, TEXT_MUTED, FONT_MAIN, FONT_TITLE,
    BTN_LISTENING_ON, BTN_LISTENING_OFF,
    BTN_MIC_ON, BTN_MIC_OFF
)


class InputPanel:

    def __init__(self, parent,
                 on_ask_callback   = None,
                 on_mic_callback   = None,
                 on_pause_callback = None,
                 on_settings       = None):
        self._on_ask       = on_ask_callback
        self._on_mic       = on_mic_callback
        self._on_pause     = on_pause_callback
        self._on_settings  = on_settings
        self._start_time   = None
        self._is_listening = False
        self._is_mic       = False
        self._is_paused    = False
        self._build(parent)

    def _build(self, parent):
        frame = tk.Frame(parent, bg=BG_PRIMARY)
        frame.pack(fill="x", padx=20, pady=(20, 10))

        # ── Row 1: Title + Gear ───────────────────────────────────────
        top_row = tk.Frame(frame, bg=BG_PRIMARY)
        top_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            top_row,
            text = "Ask AI Assistant",
            font = FONT_TITLE,
            bg   = BG_PRIMARY,
            fg   = ACCENT_COLOR
        ).pack(side="left")

        self._btn_gear = tk.Button(
            top_row,
            text             = "⚙️",
            font             = ("Segoe UI", 14),
            bg               = BG_PRIMARY,
            fg               = TEXT_COLOR,
            relief           = "flat",
            cursor           = "hand2",
            bd               = 0,
            activebackground = BG_SECONDARY,
            command          = self._show_settings_menu
        )
        self._btn_gear.pack(side="right")

        # ── Row 2: Input + Audio Buttons ──────────────────────────────
        input_row = tk.Frame(frame, bg=BG_PRIMARY)
        input_row.pack(fill="x")

        self._txt_input = tk.Entry(
            input_row,
            font   = FONT_MAIN,
            bg     = BG_SECONDARY,
            fg     = TEXT_COLOR,
            relief = "flat",
            bd     = 8
        )
        self._txt_input.pack(
            side="left", fill="x", expand=True, ipady=6
        )
        self._txt_input.bind(
            "<Return>", lambda e: self._trigger_ask()
        )

        # System Audio
        self._btn_ask = tk.Button(
            input_row,
            text    = "🔊 System Audio",
            font    = FONT_MAIN,
            bg      = BTN_LISTENING_OFF,
            fg      = TEXT_COLOR,
            relief  = "flat",
            padx    = 10,
            pady    = 6,
            cursor  = "hand2",
            width   = 13,
            command = self._trigger_ask
        )
        self._btn_ask.pack(side="left", padx=(10, 0))

        # Pause
        self._btn_pause = tk.Button(
            input_row,
            text    = "⏸ Pause",
            font    = FONT_MAIN,
            bg      = "#6b7280",
            fg      = TEXT_COLOR,
            relief  = "flat",
            padx    = 10,
            pady    = 6,
            cursor  = "hand2",
            width   = 8,
            state   = "disabled",
            command = self._trigger_pause
        )
        self._btn_pause.pack(side="left", padx=(6, 0))

        # Mic
        self._btn_mic = tk.Button(
            input_row,
            text    = "🎤 Mic",
            font    = FONT_MAIN,
            bg      = BTN_MIC_OFF,
            fg      = TEXT_COLOR,
            relief  = "flat",
            padx    = 10,
            pady    = 6,
            cursor  = "hand2",
            width   = 8,
            command = self._trigger_mic
        )
        self._btn_mic.pack(side="left", padx=(6, 0))

        # Reset
        self._btn_reset = tk.Button(
            input_row,
            text    = "🔄 Reset",
            font    = FONT_MAIN,
            bg      = "#dc2626",
            fg      = "#ffffff",
            relief  = "flat",
            padx    = 10,
            pady    = 6,
            cursor  = "hand2",
            width   = 8,
            command = self._trigger_reset
        )
        self._btn_reset.pack(side="left", padx=(6, 0))

        # ── Row 3: Status + Response Time ─────────────────────────────
        info_row = tk.Frame(frame, bg=BG_PRIMARY)
        info_row.pack(fill="x", pady=(6, 0))

        self._lbl_status = tk.Label(
            info_row,
            text   = "Status: Ready",
            font   = ("Segoe UI", 9),
            bg     = BG_PRIMARY,
            fg     = TEXT_MUTED,
            anchor = "w"
        )
        self._lbl_status.pack(side="left")

        self._lbl_response_time = tk.Label(
            info_row,
            text   = "",
            font   = ("Segoe UI", 9, "bold"),
            bg     = BG_PRIMARY,
            fg     = "#a8ff78",
            anchor = "e"
        )
        self._lbl_response_time.pack(side="right")

        # ── Row 4: Partial Speech ─────────────────────────────────────
        self._lbl_partial = tk.Label(
            frame,
            text       = "",
            font       = ("Segoe UI", 9, "italic"),
            bg         = BG_PRIMARY,
            fg         = "#b0a8ff",
            anchor     = "w",
            wraplength = 700
        )
        self._lbl_partial.pack(fill="x", pady=(4, 0))

        # ── Row 5: Screenshot Row ─────────────────────────────────────
        cap_row = tk.Frame(frame, bg=BG_PRIMARY)
        cap_row.pack(fill="x", pady=(12, 0))

        # ✅ 📷 Capture icon button with count badge
        self._ss_count    = 0
        self._btn_capture = tk.Button(
            cap_row,
            text    = "📷  0",
            font    = ("Segoe UI", 11, "bold"),
            bg      = "#1e3a5f",
            fg      = "#ffffff",
            relief  = "flat",
            padx    = 14,
            pady    = 6,
            cursor  = "hand2",
            width   = 6,
            command = lambda: self._trigger_capture("take")
        )
        self._btn_capture.pack(side="left", padx=(0, 8))

        # ✅ Send button
        self._btn_send_ss = tk.Button(
            cap_row,
            text    = "📤 Send",
            font    = ("Segoe UI", 10, "bold"),
            bg      = "#7c6af7",
            fg      = "#ffffff",
            relief  = "flat",
            padx    = 14,
            pady    = 6,
            cursor  = "hand2",
            width   = 8,
            command = lambda: self._trigger_capture("send")
        )
        self._btn_send_ss.pack(side="left", padx=(0, 8))

        # ✅ Flush button
        self._btn_flush = tk.Button(
            cap_row,
            text    = "🗑 Flush",
            font    = ("Segoe UI", 10),
            bg      = "#374151",
            fg      = "#ffffff",
            relief  = "flat",
            padx    = 14,
            pady    = 6,
            cursor  = "hand2",
            width   = 8,
            command = lambda: self._trigger_capture("flush")
        )
        self._btn_flush.pack(side="left", padx=(0, 8))

    # ── Triggers ──────────────────────────────────────────────────────
    def _trigger_ask(self):
        self._start_time = time.time()
        if self._on_ask:
            self._on_ask(self.get_text().strip())

    def _trigger_mic(self):
        self._start_time = time.time()
        if self._on_mic:
            self._on_mic()

    def _trigger_pause(self):
        if self._on_pause:
            self._on_pause()

    def _trigger_reset(self):
        if self._on_settings:
            self._on_settings("reset")

    def _trigger_capture(self, action: str):
        if self._on_settings:
            self._on_settings(f"screenshot_{action}")

    # ── Screenshot Count Badge ────────────────────────────────────────
    def update_screenshot_count(self, count: int):
        """Update 📷 button to show current count 0-3"""
        self._ss_count = count

        # ✅ Color changes by count
        colors = {
            0: "#1e3a5f",    # dark blue  — empty
            1: "#3b82f6",    # blue       — 1 taken
            2: "#f59e0b",    # amber      — 2 taken
            3: "#dc2626",    # red        — max (3)
        }
        bg = colors.get(count, "#dc2626")

        self._btn_capture.config(
            text = f"📷  {count}",
            bg   = bg
        )

    # ── Button States ─────────────────────────────────────────────────
    def set_listening_state(self, is_listening: bool):
        self._is_listening = is_listening
        if is_listening:
            self._btn_ask.config(
                text  = "🔴 System ON",
                bg    = BTN_LISTENING_ON,
                fg    = "#ffffff"
            )
            self._btn_pause.config(
                state = "normal",
                bg    = "#f59e0b",
                text  = "⏸ Pause"
            )
        else:
            self._btn_ask.config(
                text  = "🔊 System Audio",
                bg    = BTN_LISTENING_OFF,
                fg    = TEXT_COLOR
            )
            self._btn_pause.config(
                state = "disabled",
                bg    = "#6b7280",
                text  = "⏸ Pause"
            )
            self._is_paused = False

    def set_mic_state(self, is_listening: bool):
        self._is_mic = is_listening
        if is_listening:
            self._btn_mic.config(
                text  = "🔴 Mic ON",
                bg    = BTN_MIC_ON,
                fg    = "#ffffff"
            )
            self._btn_pause.config(
                state = "normal",
                bg    = "#f59e0b",
                text  = "⏸ Pause"
            )
        else:
            self._btn_mic.config(
                text  = "🎤 Mic",
                bg    = BTN_MIC_OFF,
                fg    = TEXT_COLOR
            )
            self._btn_pause.config(
                state = "disabled",
                bg    = "#6b7280",
                text  = "⏸ Pause"
            )
            self._is_paused = False

    def set_pause_state(self, is_paused: bool):
        self._is_paused = is_paused
        if is_paused:
            self._btn_pause.config(
                text = "▶ Resume",
                bg   = "#22c55e",
                fg   = "#ffffff"
            )
        else:
            self._btn_pause.config(
                text = "⏸ Pause",
                bg   = "#f59e0b",
                fg   = "#ffffff"
            )

    def reset_all_buttons(self):
        self._btn_ask.config(
            text  = "🔊 System Audio",
            bg    = BTN_LISTENING_OFF,
            fg    = TEXT_COLOR,
            state = "normal"
        )
        self._btn_pause.config(
            text  = "⏸ Pause",
            bg    = "#6b7280",
            fg    = TEXT_COLOR,
            state = "disabled"
        )
        self._btn_mic.config(
            text  = "🎤 Mic",
            bg    = BTN_MIC_OFF,
            fg    = TEXT_COLOR,
            state = "normal"
        )
        self._btn_reset.config(state="normal")
        self._txt_input.config(state="normal")
        self._is_listening = False
        self._is_mic       = False
        self._is_paused    = False
        self.update_screenshot_count(0)
        self.clear_input()
        self.clear_partial_text()
        self._lbl_response_time.config(text="")
        self.set_status("🔄 Reset complete — ready.")

    # ── Settings Menu ─────────────────────────────────────────────────
    def _show_settings_menu(self):
        menu = tk.Menu(
            self._btn_gear,
            tearoff          = 0,
            bg               = "#2e2e3e",
            fg               = "#ffffff",
            activebackground = ACCENT_COLOR,
            activeforeground = "#ffffff",
            font             = ("Segoe UI", 10),
            bd               = 0,
            relief           = "flat"
        )
        menu.add_command(
            label   = "🔑  API Settings",
            command = self._open_api_settings_dialog
        )
        menu.add_command(
            label   = "🔊  Audio Devices",
            command = self._open_audio_dialog
        )
        menu.add_command(
            label   = "📝  Clear Output",
            command = lambda: self._on_settings("clear_output")
                      if self._on_settings else None
        )
        menu.add_separator()
        menu.add_command(
            label   = "🔒  Toggle Opacity",
            command = lambda: self._on_settings("toggle_opacity")
                      if self._on_settings else None
        )
        menu.add_command(
            label   = "📌  Always on Top",
            command = lambda: self._on_settings("always_on_top")
                      if self._on_settings else None
        )
        menu.add_separator()
        menu.add_command(
            label   = "❌  Exit",
            command = lambda: self._on_settings("exit")
                      if self._on_settings else None
        )
        x = self._btn_gear.winfo_rootx()
        y = (
            self._btn_gear.winfo_rooty()
            + self._btn_gear.winfo_height()
        )
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _open_api_settings_dialog(self):
        dialog = tk.Toplevel()
        dialog.title("API Settings")
        dialog.geometry("420x280")
        dialog.configure(bg="#1e1e2e")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        tk.Label(
            dialog,
            text = "API Settings",
            font = ("Segoe UI", 13, "bold"),
            bg   = "#1e1e2e",
            fg   = ACCENT_COLOR
        ).pack(pady=(20, 10))

        tk.Label(
            dialog, text="OpenAI API Key:",
            font=("Segoe UI", 10),
            bg="#1e1e2e", fg="#ffffff"
        ).pack(anchor="w", padx=20)

        tk.Entry(
            dialog,
            font=("Segoe UI", 10),
            bg="#2e2e3e", fg="#ffffff",
            relief="flat", bd=6,
            show="*", width=45
        ).pack(padx=20, pady=(0, 10), ipady=4)

        tk.Label(
            dialog, text="Azure Speech Key:",
            font=("Segoe UI", 10),
            bg="#1e1e2e", fg="#ffffff"
        ).pack(anchor="w", padx=20)

        tk.Entry(
            dialog,
            font=("Segoe UI", 10),
            bg="#2e2e3e", fg="#ffffff",
            relief="flat", bd=6,
            show="*", width=45
        ).pack(padx=20, pady=(0, 10), ipady=4)

        tk.Button(
            dialog,
            text="💾 Save",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_COLOR, fg="#ffffff",
            relief="flat", padx=20, pady=6,
            cursor="hand2",
            command=dialog.destroy
        ).pack(pady=10)

    def _open_audio_dialog(self):
        import sounddevice as sd
        from tkinter.scrolledtext import ScrolledText

        dialog = tk.Toplevel()
        dialog.title("Audio Devices")
        dialog.geometry("460x320")
        dialog.configure(bg="#1e1e2e")
        dialog.attributes("-topmost", True)

        tk.Label(
            dialog,
            text = "Available Audio Devices",
            font = ("Segoe UI", 13, "bold"),
            bg   = "#1e1e2e",
            fg   = ACCENT_COLOR
        ).pack(pady=(15, 10))

        txt = ScrolledText(
            dialog,
            font=("Consolas", 9),
            bg="#2e2e3e", fg="#ffffff",
            relief="flat", height=12
        )
        txt.pack(
            fill="both", expand=True,
            padx=15, pady=(0, 10)
        )
        try:
            for i, d in enumerate(sd.query_devices()):
                txt.insert(
                    tk.END,
                    f"[{i}] {d['name']} "
                    f"(in:{d['max_input_channels']} "
                    f"out:{d['max_output_channels']})\n"
                )
        except Exception as ex:
            txt.insert(tk.END, f"Error: {ex}")
        txt.config(state="disabled")

        tk.Button(
            dialog, text="Close",
            font=("Segoe UI", 10),
            bg=ACCENT_COLOR, fg="#ffffff",
            relief="flat", padx=16, pady=4,
            cursor="hand2",
            command=dialog.destroy
        ).pack(pady=(0, 10))

    # ── Public Methods ─────────────────────────────────────────────────
    def get_text(self) -> str:
        return self._txt_input.get().strip()

    def set_text(self, text: str):
        self._txt_input.delete(0, tk.END)
        self._txt_input.insert(0, text)

    def clear_input(self):
        self._txt_input.delete(0, tk.END)

    def set_status(self, message: str):
        self._lbl_status.config(text=f"Status: {message}")

    def set_partial_text(self, text: str):
        self._lbl_partial.config(
            text = f"{text}..." if text else ""
        )

    def clear_partial_text(self):
        self._lbl_partial.config(text="")

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._btn_ask.config(state=state)
        self._btn_mic.config(state=state)
        self._txt_input.config(state=state)

    def show_response_time(self):
        if self._start_time is not None:
            elapsed = time.time() - self._start_time
            self._lbl_response_time.config(
                text = f"⚡ {elapsed:.2f}s"
            )
            self._start_time = None