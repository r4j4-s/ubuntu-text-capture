import os
import sys
import subprocess
import tempfile
import platform
import traceback
import pytesseract
from PIL import Image, ImageTk
import pyperclip
import tkinter as tk
from tkinter import ttk, messagebox

# Optional sv_ttk import with fallback
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

# Global variables for theme management
current_theme = "light"
all_labels = []

def update_colors(theme):
    """Update colors for all widgets according to theme"""
    if theme == "dark":
        # Dark theme colors
        root.configure(bg="#1e1e2e")
        for widget in [text_card, image_card]:
            widget.configure(bg="#2d2d3d")
        text_widget.configure(bg="#2d2d3d", fg="#d9e0ee", insertbackground="#96cdfb")
        canvas.configure(bg="#1e1e2e")
        
        # Update other UI elements
        title_frame.configure(bg="#313244")
        text_header.configure(bg="#313244")
        img_header.configure(bg="#313244")
        theme_frame.configure(bg="#313244")
        
        # Update all labels
        for label in all_labels:
            label.configure(bg="#313244", fg="#d9e0ee")
        
        img_info_label.configure(bg="#313244", fg="#d9e0ee")
    else:
        # Light theme colors
        root.configure(bg="#f1f3f4")
        for widget in [text_card, image_card]:
            widget.configure(bg="#ffffff")
        text_widget.configure(bg="white", fg="#202124", insertbackground="#1a73e8")
        canvas.configure(bg="white")
        
        # Update other UI elements
        title_frame.configure(bg="#e8e8ef")
        text_header.configure(bg="#e8e8ef")
        img_header.configure(bg="#e8e8ef")
        theme_frame.configure(bg="#e8e8ef")
        
        # Update all labels
        for label in all_labels:
            label.configure(bg="#e8e8ef", fg="#202124")
        
        img_info_label.configure(bg="#e8e8ef", fg="#202124")

def toggle_theme():
    """Toggle between light and dark themes"""
    global current_theme, theme_toggle
    
    # Toggle theme state
    if current_theme == "light":
        current_theme = "dark"
        if HAS_SV_TTK:
            sv_ttk.set_theme("dark")
        theme_toggle.config(text="☀️ Light")
    else:
        current_theme = "light"
        if HAS_SV_TTK:
            sv_ttk.set_theme("light")
        theme_toggle.config(text="🌙 Dark")
    
    # Update colors
    update_colors(current_theme)

def capture_screenshot():
    temp_dir = tempfile.gettempdir()
    screenshot_path = os.path.join(temp_dir, "screenshot.png")
    system = platform.system()

    try:
        if system == "Linux":
            tools = [
                ["gnome-screenshot", "-a", "-f", screenshot_path],
                ["maim", "-s", screenshot_path],
                ["import", screenshot_path],
                ["scrot", "-s", screenshot_path]
            ]
            for tool in tools:
                try:
                    subprocess.run(tool, check=True)
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            else:
                messagebox.showerror("Error", "No supported screenshot tool found.")
                return

        elif system == "Windows":
            from PIL import ImageGrab
            screen = ImageGrab.grab()
            screen.save(screenshot_path)

        elif system == "Darwin":
            subprocess.run(["screencapture", "-i", screenshot_path], check=True)
        else:
            messagebox.showerror("Error", f"Unsupported operating system: {system}")
            return

        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            messagebox.showerror("Error", "Screenshot was not captured.")
            return

        process_screenshot(screenshot_path)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to capture screenshot:\n{str(e)}")
        traceback.print_exc()

def process_screenshot(screenshot_path):
    try:
        screenshot = Image.open(screenshot_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open screenshot: {str(e)}")
        return

    try:
        text = pytesseract.image_to_string(screenshot, lang='eng').strip()
        pyperclip.copy(text)
        show_gui(screenshot, text)

    except pytesseract.TesseractNotFoundError:
        messagebox.showerror("Error", "Tesseract OCR not found.")
    except Exception as e:
        messagebox.showerror("Error", f"OCR processing error:\n{str(e)}")
        traceback.print_exc()
    finally:
        try:
            os.remove(screenshot_path)
        except:
            pass

def show_gui(original_image, text):
    global root, text_widget, canvas, text_card, image_card
    global title_frame, text_header, img_header, img_info_label, theme_frame, theme_toggle

    root = tk.Tk()
    root.title("Screenshot OCR")
    root.geometry("1200x700")
    root.minsize(700, 400)

    if HAS_SV_TTK:
        sv_ttk.set_theme("light")  # Start with light theme

    # Configure button styles
    style = ttk.Style()
    style.configure("Custom.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=10
    )
    style.map("Custom.TButton",
        background=[("active", "#d0e2ff"), ("!active", "#f1f5ff")],
        foreground=[("active", "#000000"), ("!active", "#1a73e8")]
    )

    # Configure toggle button style
    style.configure("Toggle.TButton", 
        font=("Segoe UI", 10),
        padding=5
    )
    style.map("Toggle.TButton",
        background=[("active", "#d0e2ff"), ("!active", "#e8e8ef")],
        foreground=[("active", "#000000"), ("!active", "#1a73e8")]
    )

    main_frame = ttk.Frame(root, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)

    title_frame = tk.Frame(main_frame, bg="#e8e8ef")
    title_frame.pack(fill=tk.X, pady=(0, 10))

    app_title = tk.Label(
        title_frame, text="📸 Screenshot OCR",
        font=("Segoe UI", 16, "bold"), bg="#e8e8ef"
    )
    app_title.pack(side=tk.LEFT)
    
    # Initialize all_labels list
    global all_labels
    all_labels = [app_title]

    # Theme toggle frame
    theme_frame = tk.Frame(title_frame, bg="#e8e8ef")
    theme_frame.pack(side=tk.RIGHT, padx=5)
    
    theme_label = tk.Label(theme_frame, text="Theme:", bg="#e8e8ef", font=("Segoe UI", 10))
    theme_label.pack(side=tk.LEFT, padx=(0, 5))
    all_labels.append(theme_label)
    
    # Theme toggle button
    theme_toggle = ttk.Button(
        theme_frame,
        text="🌙 Dark",  # Start with option to go dark
        style="Toggle.TButton",
        command=toggle_theme
    )
    theme_toggle.pack(side=tk.LEFT)

    # New screenshot button
    ttk.Button(
        title_frame,
        text="📷 New Screenshot",
        style="Custom.TButton",
        command=lambda: (root.destroy(), capture_screenshot())
    ).pack(side=tk.RIGHT, padx=10)

    # Main content area
    paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)

    # Text panel
    text_card = tk.Frame(paned, bg="#ffffff", bd=1, relief="solid", highlightbackground="#c2c2cc")
    paned.add(text_card, weight=1)

    text_header = tk.Frame(text_card, bg="#e8e8ef")
    text_header.pack(fill=tk.X)

    text_title = tk.Label(text_header, text="📝 Extracted Text", font=("Segoe UI", 12, "bold"), bg="#e8e8ef")
    text_title.pack(side=tk.LEFT)
    all_labels.append(text_title)

    ttk.Button(
        text_header,
        text="Copy to Clipboard",
        style="Custom.TButton",
        command=lambda: pyperclip.copy(text_widget.get("1.0", tk.END).strip())
    ).pack(side=tk.RIGHT)

    text_container = ttk.Frame(text_card, padding=(10, 5, 10, 10))
    text_container.pack(fill=tk.BOTH, expand=True)
    text_container.grid_rowconfigure(0, weight=1)
    text_container.grid_columnconfigure(0, weight=1)

    text_widget = tk.Text(
        text_container, wrap="word", font=("Segoe UI", 11),
        bg="white", fg="#202124", insertbackground="#1a73e8",
        relief="flat", borderwidth=0
    )
    text_widget.grid(row=0, column=0, sticky="nsew")
    text_widget.insert("1.0", text)

    scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_widget.config(yscrollcommand=scrollbar.set)

    # Image panel
    image_card = tk.Frame(paned, bg="#ffffff", bd=1, relief="solid", highlightbackground="#c2c2cc")
    paned.add(image_card, weight=1)

    img_header = tk.Frame(image_card, bg="#e8e8ef")
    img_header.pack(fill=tk.X)

    img_info_label = tk.Label(img_header, text="", font=("Segoe UI", 9), bg="#e8e8ef")
    img_info_label.pack(side=tk.RIGHT)

    img_title = tk.Label(img_header, text="🖼️ Screenshot", font=("Segoe UI", 12, "bold"), bg="#e8e8ef")
    img_title.pack(side=tk.LEFT)
    all_labels.append(img_title)

    canvas_frame = ttk.Frame(image_card, padding=(10, 5, 10, 10))
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    state = {"original_image": original_image, "tk_img": None}

    def resize_image(event=None):
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        resized = state["original_image"].copy()
        img_ratio = resized.width / resized.height
        canvas_ratio = w / h

        if img_ratio > canvas_ratio:
            new_w = w
            new_h = int(w / img_ratio)
        else:
            new_h = h
            new_w = int(h * img_ratio)

        try:
            resized = resized.resize((new_w, new_h), Image.Resampling.LANCZOS)
        except AttributeError:
            resized = resized.resize((new_w, new_h), Image.LANCZOS)

        state["tk_img"] = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        canvas.create_image(x, y, anchor="nw", image=state["tk_img"])
        img_info_label.config(text=f"{original_image.width} × {original_image.height} px")

    canvas.bind("<Configure>", resize_image)
    root.update()
    root.after(100, resize_image)

    root.mainloop()

if __name__ == "__main__":
    capture_screenshot()
