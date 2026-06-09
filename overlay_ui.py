import queue
import random
import threading
import tkinter as tk
from tkinter import Button, Canvas, Frame, Label, scrolledtext

from config import LOGGER


class OverlayUI:
    def __init__(self, settings_manager=None):
        self.settings = settings_manager
        self.root = tk.Tk()
        self.root.title("Parakeet")
        self.is_hidden = False
        self.is_recording = False
        self._ui_queue = queue.Queue()
        self.compact_mode = settings_manager.get("compact_mode", False) if settings_manager else False

        if self.compact_mode:
            self._create_compact_ui()
        else:
            self._create_full_ui()

        if settings_manager:
            self.root.attributes("-alpha", settings_manager.get("window_opacity", 0.95))
            self.root.attributes("-topmost", settings_manager.get("always_on_top", True))

        # Drain queued UI work on the Tk main thread so worker threads never
        # touch widgets directly.
        self.root.after(50, self._process_ui_queue)

    def _dispatch(self, action):
        if threading.current_thread() is threading.main_thread():
            action()
        else:
            self._ui_queue.put(action)

    def _process_ui_queue(self):
        try:
            while True:
                action = self._ui_queue.get_nowait()
                try:
                    action()
                except Exception as exc:
                    LOGGER.debug("Queued UI action failed: %s", exc)
        except queue.Empty:
            pass

        try:
            if self.root.winfo_exists():
                self.root.after(50, self._process_ui_queue)
        except tk.TclError:
            return

    def _create_full_ui(self):
        self.root.geometry("600x500")
        self.root.configure(bg="#0a0e27")

        header = tk.Frame(self.root, bg="#0a0e27", height=80)
        header.pack(fill=tk.X, padx=10, pady=10)

        self.rec_canvas = Canvas(header, width=60, height=60, bg="#0a0e27", highlightthickness=0)
        self.rec_canvas.pack(side=tk.LEFT, padx=10)
        self.rec_circle = self.rec_canvas.create_oval(10, 10, 50, 50, fill="#1e2a4a", outline="")
        self.rec_pulse = self.rec_canvas.create_oval(5, 5, 55, 55, outline="#ff4444", width=0)

        self.status_label = tk.Label(
            header,
            text="Ready to listen",
            bg="#0a0e27",
            fg="#8b9dc3",
            font=("Segoe UI", 12),
            anchor="w",
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        settings_btn = Button(
            header,
            text="Settings",
            bg="#1e2a4a",
            fg="#8b9dc3",
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_settings,
        )
        settings_btn.pack(side=tk.RIGHT, padx=5)

        self.viz_canvas = Canvas(self.root, height=40, bg="#0a0e27", highlightthickness=0)
        self.viz_canvas.pack(fill=tk.X, padx=10)
        self.viz_bars = []
        for i in range(30):
            x = i * 20
            bar = self.viz_canvas.create_rectangle(x, 20, x + 15, 20, fill="#1e2a4a", outline="")
            self.viz_bars.append(bar)

        text_frame = tk.Frame(self.root, bg="#0f1429")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg="#0f1429",
            fg="#dce1ec",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.text_area.tag_config("user", foreground="#61afef", font=("Segoe UI", 10, "bold"))
        self.text_area.tag_config("chrome", foreground="#98c379", spacing3=5)
        self.text_area.tag_config("error", foreground="#e06c75")

        info_bar = tk.Label(
            self.root,
            text="Press Ctrl+Shift+Space to talk. Right-click tray for settings.",
            bg="#1e2a4a",
            fg="#6b7a99",
            font=("Segoe UI", 9),
            pady=8,
        )
        info_bar.pack(fill=tk.X)

    def _create_compact_ui(self):
        self.root.geometry("300x100")
        self.root.configure(bg="#0a0e27")
        self.root.overrideredirect(True)

        self.status_label = tk.Label(
            self.root,
            text="Ready",
            bg="#0a0e27",
            fg="#8b9dc3",
            font=("Segoe UI", 11),
        )
        self.status_label.pack(expand=True)

        self.text_area = None
        self.rec_canvas = None
        self.viz_canvas = None
        self.rec_circle = None
        self.rec_pulse = None
        self.viz_bars = []

    def open_settings(self):
        def _open():
            settings_win = tk.Toplevel(self.root)
            settings_win.title("Settings")
            settings_win.geometry("400x500")
            settings_win.configure(bg="#0a0e27")

            frame = Frame(settings_win, bg="#0a0e27", padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)

            Label(frame, text="Parakeet Settings", bg="#0a0e27", fg="#ffffff", font=("Segoe UI", 14, "bold")).pack(
                pady=10
            )

            Label(frame, text="AI Provider:", bg="#0a0e27", fg="#8b9dc3", font=("Segoe UI", 10)).pack(
                anchor="w", pady=5
            )

            provider_var = tk.StringVar(value=self.settings.get("ai_provider", "groq") if self.settings else "groq")
            for provider in ["groq", "google", "openai", "anthropic"]:
                tk.Radiobutton(
                    frame,
                    text=provider.title(),
                    variable=provider_var,
                    value=provider,
                    bg="#0a0e27",
                    fg="#dce1ec",
                    selectcolor="#1e2a4a",
                    activebackground="#0a0e27",
                    font=("Segoe UI", 9),
                ).pack(anchor="w", padx=20)

            tk.Label(
                frame,
                text="Groq: fast and free",
                bg="#0a0e27",
                fg="#98c379",
                font=("Segoe UI", 8),
            ).pack(anchor="w", padx=40, pady=2)

            Label(frame, text="\nWindow Mode:", bg="#0a0e27", fg="#8b9dc3", font=("Segoe UI", 10)).pack(
                anchor="w", pady=5
            )

            compact_var = tk.BooleanVar(value=self.compact_mode)
            tk.Checkbutton(
                frame,
                text="Compact Mode",
                variable=compact_var,
                bg="#0a0e27",
                fg="#dce1ec",
                selectcolor="#1e2a4a",
                activebackground="#0a0e27",
                font=("Segoe UI", 9),
            ).pack(anchor="w", padx=20)

            def save_settings():
                if self.settings:
                    self.settings.set("ai_provider", provider_var.get())
                    self.settings.set("compact_mode", compact_var.get())
                settings_win.destroy()

            Button(
                frame,
                text="Save Settings",
                command=save_settings,
                bg="#61afef",
                fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                pady=10,
            ).pack(pady=20)

        self._dispatch(_open)

    def toggle_visibility(self):
        def _toggle():
            if self.is_hidden:
                self.root.deiconify()
                self.root.attributes("-topmost", True)
            else:
                self.root.withdraw()
            self.is_hidden = not self.is_hidden

        self._dispatch(_toggle)

    def hide_from_capture(self):
        self._dispatch(lambda: self.root.geometry("600x500+-5000+-5000"))

    def show_normal(self):
        self._dispatch(lambda: self.root.geometry("600x500+100+100"))

    def append_text(self, text, tag="normal"):
        def _append():
            if self.text_area:
                self.text_area.insert(tk.END, text, tag)
                self.text_area.see(tk.END)

        self._dispatch(_append)

    def set_status(self, status):
        def _set():
            if "Listening" in status or "🎤" in status:
                self.status_label.config(fg="#ff4444", text=status)
                if not self.compact_mode:
                    self.start_recording_animation()
            elif "Transcribing" in status or "⏳" in status:
                self.status_label.config(fg="#ffa500", text=status)
                if not self.compact_mode:
                    self.stop_recording_animation()
            elif "Searching" in status or "🔍" in status or "💡" in status:
                self.status_label.config(fg="#61afef", text=status)
            elif "Ready" in status or "✅" in status:
                self.status_label.config(fg="#98c379", text=status)
                if not self.compact_mode:
                    self.stop_recording_animation()
            elif "No speech" in status or "⚠️" in status:
                self.status_label.config(fg="#e5c07b", text=status)
            else:
                self.status_label.config(fg="#8b9dc3", text=status)

        self._dispatch(_set)

    def start_recording_animation(self):
        def _start():
            if not self.rec_canvas:
                return
            self.is_recording = True
            self.rec_canvas.itemconfig(self.rec_circle, fill="#ff4444")
            self._animate_recording()
            self._animate_visualizer()

        self._dispatch(_start)

    def stop_recording_animation(self):
        def _stop():
            if not self.rec_canvas:
                return
            self.is_recording = False
            self.rec_canvas.itemconfig(self.rec_circle, fill="#1e2a4a")
            self.rec_canvas.itemconfig(self.rec_pulse, width=0)
            if self.viz_bars:
                for bar in self.viz_bars:
                    coords = self.viz_canvas.coords(bar)
                    self.viz_canvas.coords(bar, coords[0], 20, coords[2], 20)

        self._dispatch(_stop)

    def _animate_recording(self, size=0):
        if not self.is_recording or not self.rec_canvas:
            return
        size = (size + 1) % 20
        offset = size / 2
        self.rec_canvas.itemconfig(self.rec_pulse, width=2 if size > 0 else 0)
        self.rec_canvas.coords(self.rec_pulse, 10 - offset, 10 - offset, 50 + offset, 50 + offset)
        self.root.after(50, lambda: self._animate_recording(size))

    def _animate_visualizer(self):
        if not self.is_recording or not self.viz_canvas or not self.viz_bars:
            return
        for i, bar in enumerate(self.viz_bars):
            coords = self.viz_canvas.coords(bar)
            height = random.randint(5, 30)
            self.viz_canvas.coords(bar, coords[0], 20 - height, coords[2], 20 + height)
            color = f"#{40 + i * 2:02x}{60 + i * 3:02x}{100 + i * 2:02x}"
            self.viz_canvas.itemconfig(bar, fill=color)
        self.root.after(100, self._animate_visualizer)

    def clear(self):
        self._dispatch(lambda: self.text_area.delete(1.0, tk.END) if self.text_area else None)

    def run(self):
        self.root.mainloop()
