# ui/app_window.py

import tkinter as tk
from ui.components.input_panel  import InputPanel
from ui.components.output_panel import OutputPanel
from logic.openai_service        import OpenAIService
from logic.html_builder          import HtmlBuilder
from logic.language_validator    import LanguageValidator
from logic.audio_listener        import AudioListener, MicListener
from logic.window_manager        import WindowManager
from logic.screen_capture        import ScreenCapture
from config.settings             import (
    APP_TITLE, APP_WIDTH, APP_HEIGHT, BG_PRIMARY
)


class AppWindow:

    MOVE_STEP     = 20
    SOURCE_NONE   = "none"
    SOURCE_SYSTEM = "system"
    SOURCE_MIC    = "mic"

    def __init__(self, root: tk.Tk):
        self._root          = root
        self._service       = OpenAIService()
        self._validator     = LanguageValidator()
        self._wm            = WindowManager(root)
        self._active_source = self.SOURCE_NONE
        self._is_paused     = False

        self._listener = AudioListener(
            on_recognized  = self._on_speech_recognized,
            on_recognizing = self._on_speech_recognizing,
            on_status      = self._on_listener_status
        )

        self._mic = MicListener(
            on_recognized  = self._on_mic_recognized,
            on_recognizing = self._on_mic_recognizing,
            on_status      = self._on_listener_status
        )

        self._screen = ScreenCapture(
            root             = root,
            on_captured      = self._on_screen_captured,
            on_status        = self._on_listener_status,
            on_count_changed = self._on_screenshot_count_changed
        )

        self._setup_window()
        self._setup_shortcuts()
        self._build_ui()
        self._show_welcome()
        self._wm.apply()

    # ── Window Setup ──────────────────────────────────────────────────
    def _setup_window(self):
        self._root.title(APP_TITLE)
        self._root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self._root.configure(bg=BG_PRIMARY)
        self._root.resizable(True, True)
        self._root.minsize(600, 400)
        self._root.attributes("-topmost",    True)
        self._root.attributes("-alpha",      0.7)
        self._root.attributes("-toolwindow", True)

    # ── Keyboard Shortcuts ────────────────────────────────────────────
    def _setup_shortcuts(self):
        self._root.bind("<Control-Down>",  self._move_down)
        self._root.bind("<Control-Up>",    self._move_up)
        self._root.bind("<Control-Right>", self._move_right)
        self._root.bind("<Control-Left>",  self._move_left)

    def _get_position(self):
        self._root.update_idletasks()
        x = self._root.winfo_x()
        y = self._root.winfo_y()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        return x, y, w, h

    def _move_down(self, event=None):
        x, y, w, h = self._get_position()
        self._root.geometry(f"{w}x{h}+{x}+{y + self.MOVE_STEP}")

    def _move_up(self, event=None):
        x, y, w, h = self._get_position()
        self._root.geometry(f"{w}x{h}+{x}+{y - self.MOVE_STEP}")

    def _move_right(self, event=None):
        x, y, w, h = self._get_position()
        self._root.geometry(
            f"{w}x{h}+{x + self.MOVE_STEP}+{y}"
        )

    def _move_left(self, event=None):
        x, y, w, h = self._get_position()
        self._root.geometry(
            f"{w}x{h}+{x - self.MOVE_STEP}+{y}"
        )

    # ── Build UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        self._input = InputPanel(
            parent            = self._root,
            on_ask_callback   = self._on_ask_toggle,
            on_mic_callback   = self._on_mic_toggle,
            on_pause_callback = self._on_pause_toggle,
            on_settings       = self._on_settings_action
        )
        self._output = OutputPanel(parent=self._root)

    def _show_welcome(self):
        self._output.display_html(HtmlBuilder.build_empty())

    # ── Screenshot Count Callback ─────────────────────────────────────
    def _on_screenshot_count_changed(self, count: int):
        """Called when screenshot is taken or flushed"""
        self._input.update_screenshot_count(count)

    # ── System Audio Toggle ───────────────────────────────────────────
    def _on_ask_toggle(self, question: str):
        if self._active_source != self.SOURCE_SYSTEM:
            self._active_source = self.SOURCE_SYSTEM
            self._is_paused     = False
            self._input.set_listening_state(True)
            self._input.set_pause_state(False)
            self._input.set_status("🔊 Starting system audio...")
            self._listener.start()
        else:
            self._active_source = self.SOURCE_NONE
            self._is_paused     = False
            self._input.set_listening_state(False)
            self._input.set_status("⏹️ System audio stopped.")
            self._listener.stop()
            self._input.clear_partial_text()
            captured = self._input.get_text().strip()
            if captured:
                self._send_to_openai(captured)

    # ── Mic Toggle ────────────────────────────────────────────────────
    def _on_mic_toggle(self):
        if self._active_source != self.SOURCE_MIC:
            self._active_source = self.SOURCE_MIC
            self._is_paused     = False
            self._input.set_mic_state(True)
            self._input.set_pause_state(False)
            self._input.set_status("🎤 Starting mic...")
            self._mic.start()
        else:
            self._active_source = self.SOURCE_NONE
            self._is_paused     = False
            self._input.set_mic_state(False)
            self._input.set_status("⏹️ Mic stopped.")
            self._mic.stop()
            self._input.clear_partial_text()
            captured = self._input.get_text().strip()
            if captured:
                self._send_to_openai(captured)

    # ── Pause Toggle ──────────────────────────────────────────────────
    def _on_pause_toggle(self):
        if self._active_source == self.SOURCE_NONE:
            return

        if not self._is_paused:
            self._is_paused = True
            self._input.set_pause_state(True)
            if self._active_source == self.SOURCE_SYSTEM:
                self._listener.stop()
                self._input.set_status("⏸ System audio paused.")
            elif self._active_source == self.SOURCE_MIC:
                self._mic.stop()
                self._input.set_status("⏸ Mic paused.")
        else:
            self._is_paused = False
            self._input.set_pause_state(False)
            if self._active_source == self.SOURCE_SYSTEM:
                self._listener.start()
                self._input.set_listening_state(True)
                self._input.set_status("▶ System audio resumed.")
            elif self._active_source == self.SOURCE_MIC:
                self._mic.start()
                self._input.set_mic_state(True)
                self._input.set_status("▶ Mic resumed.")

    # ── Screenshot Callback → OpenAI Vision ──────────────────────────
    def _on_screen_captured(self, base64_images: list):
        if not base64_images:
            self._input.set_status("⚠️ No screenshots to send.")
            return

        count = len(base64_images)
        self._input.set_status(
            f"🤖 Sending {count} screenshot(s) to AI..."
        )
        self._input.set_enabled(False)
        self._input.set_start_time()
        self._output.display_html(HtmlBuilder.build_loading())

        # ✅ Send images directly to OpenAI Vision
        self._service.ask_vision_async(
            base64_images = base64_images,
            on_success    = self._on_answer_received,
            on_error      = self._on_error,
            on_chunk      = self._on_stream_chunk
        )

    # ── Reset ─────────────────────────────────────────────────────────
    def _do_reset(self):
        try:
            self._input.set_status("🔄 Resetting...")
            if self._listener.is_listening:
                self._listener.stop()
            if self._mic.is_listening:
                self._mic.stop()
            self._screen.flush()
            self._active_source = self.SOURCE_NONE
            self._is_paused     = False
            self._input.reset_all_buttons()
            self._output.display_html(HtmlBuilder.build_empty())
            self._root.after(500, self._reinitialize_listeners)
        except Exception as ex:
            self._input.set_status(f"⚠️ Reset error: {str(ex)}")

    def _reinitialize_listeners(self):
        try:
            # ✅ Reset mic fully — rebuilds config + connection
            self._mic.reset()

            # ✅ Fresh system audio listener
            self._listener = AudioListener(
                on_recognized  = self._on_speech_recognized,
                on_recognizing = self._on_speech_recognizing,
                on_status      = self._on_listener_status
            )
            self._input.set_status(
                "✅ Reset done — ready to use."
            )
        except Exception as ex:
            self._input.set_status(
                f"⚠️ Reinit error: {str(ex)}"
            )

    # ── System Audio Callbacks ────────────────────────────────────────
    def _on_speech_recognized(self, text: str):
        self._root.after(
            0, lambda: self._handle_recognized(text)
        )

    def _handle_recognized(self, text: str):
        self._input.set_text(text)
        self._input.clear_partial_text()
        self._input.set_status(f"🔊 Captured: {text[:50]}...")
        self._send_to_openai(text)

    def _on_speech_recognizing(self, text: str):
        self._root.after(
            0,
            lambda: self._input.set_partial_text(f"🔊 {text}")
        )

    # ── Mic Callbacks ─────────────────────────────────────────────────
    def _on_mic_recognized(self, text: str):
        self._root.after(
            0, lambda: self._handle_mic_recognized(text)
        )

    def _handle_mic_recognized(self, text: str):
        self._input.set_text(text)
        self._input.clear_partial_text()
        self._input.set_status(f"🎤 You said: {text[:50]}...")
        self._send_to_openai(text)

    def _on_mic_recognizing(self, text: str):
        self._root.after(
            0,
            lambda: self._input.set_partial_text(f"🎤 {text}")
        )

    # ── Shared Status ─────────────────────────────────────────────────
    def _on_listener_status(self, msg: str):
        self._root.after(
            0, lambda: self._input.set_status(msg)
        )

    # ── Send Text to OpenAI ───────────────────────────────────────────
    def _send_to_openai(self, question: str):
        is_valid, error_msg = LanguageValidator.validate(question)
        if not is_valid:
            self._input.set_status(error_msg)
            self._output.display_html(
                HtmlBuilder.build_language_error(error_msg)
            )
            return

        self._input.set_enabled(False)
        self._input.set_status("⏳ Asking AI...")
        self._output.display_html(HtmlBuilder.build_loading())

        self._service.ask_async(
            question   = question,
            on_success = self._on_answer_received,
            on_error   = self._on_error,
            on_chunk   = self._on_stream_chunk
        )

    def _on_stream_chunk(self, partial_html: str):
        self._root.after(
            0, lambda: self._display_stream(partial_html)
        )

    def _display_stream(self, partial_html: str):
        self._output.display_html(
            HtmlBuilder.build_page(partial_html)
        )
        self._input.set_status("✍️ AI is typing...")

    def _on_answer_received(self, html_content: str):
        self._root.after(
            0, lambda: self._display_answer(html_content)
        )

    def _display_answer(self, html_content: str):
        self._output.display_html(
            HtmlBuilder.build_page(html_content)
        )
        self._input.set_status("✅ Answer received.")
        self._input.show_response_time()
        self._input.set_enabled(True)
        self._input.clear_input()

    def _on_error(self, error_msg: str):
        self._root.after(
            0, lambda: self._display_error(error_msg)
        )

    def _display_error(self, error_msg: str):
        self._output.display_html(
            HtmlBuilder.build_error(error_msg)
        )
        self._input.set_status(f"⚠️ {error_msg}")
        self._input.set_enabled(True)

    # ── Settings Actions ──────────────────────────────────────────────
    def _on_settings_action(self, action: str):

        if action == "clear_output":
            self._output.display_html(HtmlBuilder.build_empty())
            self._input.set_status("🗑️ Output cleared.")

        elif action == "toggle_opacity":
            current = self._root.attributes("-alpha")
            new_val = 1.0 if current < 1.0 else 0.7
            self._root.attributes("-alpha", new_val)
            self._input.set_status(
                f"🔆 Opacity: {int(new_val * 100)}%"
            )

        elif action == "always_on_top":
            current = self._root.attributes("-topmost")
            self._root.attributes("-topmost", not current)
            self._input.set_status(
                f"📌 Always on top: "
                f"{'ON' if not current else 'OFF'}"
            )

        elif action == "reset":
            self._do_reset()

        # ✅ Screenshot actions
        elif action == "screenshot_take":
            self._screen.take_screenshot()

        elif action == "screenshot_send":
            self._screen.send_to_ai()

        elif action == "screenshot_flush":
            self._screen.flush()

        elif action == "exit":
            self._root.destroy()