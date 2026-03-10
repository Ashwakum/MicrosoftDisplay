# logic/window_manager.py

import ctypes
import ctypes.wintypes

WDA_EXCLUDEFROMCAPTURE = 0x00000011


class WindowManager:

    def __init__(self, root):
        self._root = root
        self._hwnd = None

    def apply(self):
        self._root.after(500, self._setup)

    def _setup(self):
        self._hwnd = self._get_hwnd()
        if self._hwnd:
            self._set_always_on_top()
            self._hide_from_capture_permanently()

    def _get_hwnd(self):
        try:
            # ✅ Most reliable way to get hwnd
            self._root.update()
            return ctypes.windll.user32.GetParent(
                self._root.winfo_id()
            ) or self._root.winfo_id()
        except Exception as ex:
            print(f"HWND error: {ex}")
            return None

    def _set_always_on_top(self):
        try:
            HWND_TOPMOST = -1
            SWP_NOMOVE   = 0x0002
            SWP_NOSIZE   = 0x0001
            ctypes.windll.user32.SetWindowPos(
                self._hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE
            )
            print("✅ Always on top applied.")
        except Exception as ex:
            print(f"Always on top error: {ex}")

    def _hide_from_capture_permanently(self):
        """
        Permanently hide from ALL screen capture tools:
        - Windows Game Bar
        - Teams / Zoom / Meet screen share
        - OBS / Snipping Tool
        This stays active for entire app lifetime.
        """
        try:
            result = ctypes.windll.user32.SetWindowDisplayAffinity(
                self._hwnd,
                WDA_EXCLUDEFROMCAPTURE
            )
            if result:
                print("✅ Window permanently hidden from screen capture.")
            else:
                error = ctypes.GetLastError()
                print(f"⚠️ SetWindowDisplayAffinity failed: {error}")
                # ✅ Retry once after 1 second
                self._root.after(
                    1000,
                    self._retry_hide
                )
        except Exception as ex:
            print(f"⚠️ Hide from capture error: {ex}")

    def _retry_hide(self):
        """Retry hiding if first attempt failed"""
        try:
            # ✅ Re-fetch hwnd and retry
            self._hwnd = self._get_hwnd()
            if self._hwnd:
                result = ctypes.windll.user32.SetWindowDisplayAffinity(
                    self._hwnd,
                    WDA_EXCLUDEFROMCAPTURE
                )
                if result:
                    print("✅ Retry hide succeeded.")
                else:
                    print("⚠️ Retry hide failed — Windows version may not support it.")
        except Exception as ex:
            print(f"⚠️ Retry error: {ex}")