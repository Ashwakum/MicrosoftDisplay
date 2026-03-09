# logic/screen_capture.py

import io
import time
import base64
import ctypes
import threading
import tkinter as tk
from PIL import ImageGrab, Image

WDA_EXCLUDEFROMCAPTURE = 0x00000011
MAX_SCREENSHOTS        = 3


def _get_hwnd(win) -> int:
    try:
        return (
            ctypes.windll.user32.GetParent(win.winfo_id())
            or win.winfo_id()
        )
    except Exception:
        return 0


def _hide_from_capture(hwnd: int):
    try:
        ctypes.windll.user32.SetWindowDisplayAffinity(
            hwnd, WDA_EXCLUDEFROMCAPTURE
        )
    except Exception:
        pass


class ScreenCapture:

    def __init__(self, root: tk.Tk, on_captured,
                 on_status, on_count_changed):
        self._root             = root
        self._on_captured      = on_captured
        self._on_status        = on_status
        self._on_count_changed = on_count_changed
        self._screenshots      = []
        self._lock             = threading.Lock()

    # ── Take Screenshot ───────────────────────────────────────────────
    def take_screenshot(self):
        with self._lock:
            count = len(self._screenshots)

        if count >= MAX_SCREENSHOTS:
            self._on_status(
                f"⚠️ Max {MAX_SCREENSHOTS} reached. "
                f"Click 📤 Send or 🗑 Flush first."
            )
            return

        # ✅ Just minimize — window_manager already hides from capture
        self._root.iconify()
        self._root.after(400, self._do_screenshot)

    def _do_screenshot(self):
        try:
            time.sleep(0.2)

            # ✅ Full screen capture
            img = ImageGrab.grab()

            with self._lock:
                self._screenshots.append(img)
                count = len(self._screenshots)

            # ✅ Restore app — stays hidden from screen share
            # because window_manager applied WDA_EXCLUDEFROMCAPTURE
            self._restore_app()
            self._on_status(
                f"📸 Screenshot {count}/{MAX_SCREENSHOTS} stored."
            )
            self._root.after(
                0, lambda: self._on_count_changed(count)
            )

        except Exception as ex:
            self._restore_app()
            self._on_status(f"⚠️ Error: {str(ex)}")

    # ── Restore app after screenshot ──────────────────────────────────
    def _restore_app(self):
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()

            # ✅ Re-apply hide after restore
            # deiconify can reset affinity on some Windows versions
            self._root.after(200, self._reapply_hide)
        except Exception:
            pass

    def _reapply_hide(self):
        """
        Re-apply WDA_EXCLUDEFROMCAPTURE after deiconify.
        Some Windows versions reset affinity on restore.
        """
        try:
            hwnd = _get_hwnd(self._root)
            if hwnd:
                _hide_from_capture(hwnd)
        except Exception:
            pass

    # ── Send to OpenAI ────────────────────────────────────────────────
    def send_to_ai(self):
        with self._lock:
            count = len(self._screenshots)

        if count == 0:
            self._on_status(
                "⚠️ No screenshots. Click 📷 first."
            )
            return

        self._on_status(
            f"⏳ Sending {count} screenshot(s) to AI..."
        )
        threading.Thread(
            target = self._process_and_send,
            daemon = True
        ).start()

    def _process_and_send(self):
        try:
            with self._lock:
                images = list(self._screenshots)

            base64_images = [
                self._to_base64(img) for img in images
            ]

            self.flush()

            self._root.after(
                0,
                lambda: self._on_captured(base64_images)
            )

        except Exception as ex:
            self._on_status(f"⚠️ Send error: {str(ex)}")

    def _to_base64(self, img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    # ── Flush ─────────────────────────────────────────────────────────
    def flush(self):
        with self._lock:
            self._screenshots.clear()
        self._root.after(
            0, lambda: self._on_count_changed(0)
        )
        self._on_status("🗑 Flushed — screenshots cleared.")

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._screenshots)
