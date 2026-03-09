# main.py

import tkinter as tk
from ui.app_window import AppWindow

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app  = AppWindow(root)
        root.mainloop()
    except KeyboardInterrupt:
        # ✅ Ctrl+C in terminal — clean exit, not an error
        print("👋 App closed.")
    except Exception as ex:
        print(f"⚠️ Unexpected error: {ex}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass