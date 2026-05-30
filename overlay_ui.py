import tkinter as tk
from tkinter import scrolledtext
import threading
from config import LOGGER

class OverlayUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant")
        self.root.geometry("400x300")
        self.root.attributes('-topmost', True)
        self.is_hidden = False
        
        self.text_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = tk.Label(
            self.root, 
            text="Ready", 
            bg="#007acc", 
            fg="white",
            font=("Arial", 9)
        )
        self.status_label.pack(fill=tk.X)
        
    def toggle_visibility(self):
        if self.is_hidden:
            self.root.deiconify()
            self.root.attributes('-topmost', True)
        else:
            self.root.withdraw()
        self.is_hidden = not self.is_hidden
    
    def hide_from_capture(self):
        self.root.geometry(f"400x300+{-5000}+{-5000}")
    
    def show_normal(self):
        self.root.geometry("400x300+100+100")
    
    def append_text(self, text, tag="normal"):
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.root.update()
    
    def set_status(self, status):
        self.status_label.config(text=status)
        self.root.update()
    
    def clear(self):
        self.text_area.delete(1.0, tk.END)
    
    def run(self):
        self.root.mainloop()
