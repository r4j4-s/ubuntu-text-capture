import os
import sys
import subprocess
import tempfile
import platform
import traceback
import easyocr
import pytesseract
from PIL import Image, ImageTk
import pyperclip
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import torch

# Optional sv_ttk import with fallback
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

# Optional LatexOCR import with fallback
try:
    from pix2tex.cli import LatexOCR
    HAS_LATEX_OCR = True
except ImportError:
    HAS_LATEX_OCR = False

# Global variables for theme management
current_theme = "light"
all_labels = []
reader = None  # Will be initialized when needed
latex_ocr = None  # Will be initialized when needed
current_ocr_engine = "easyocr"  # Default OCR engine


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
        ocr_engine_frame.configure(bg="#313244")
        
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
        ocr_engine_frame.configure(bg="#e8e8ef")
        
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

def initialize_ocr(engine=None):
    """Initialize the OCR reader if not already done"""
    global reader, latex_ocr, current_ocr_engine
    
    if engine:
        current_ocr_engine = engine
    
    try:
        # Show a busy cursor during OCR initialization
        root.config(cursor="watch")
        root.update()
        
        if current_ocr_engine == "easyocr" and reader is None:
            reader = easyocr.Reader(['de'], gpu=False)
        elif current_ocr_engine == "pytesseract":
            # Check if pytesseract is installed and configured
            try:
                pytesseract.get_tesseract_version()
            except Exception as e:
                messagebox.showerror("Error", "Pytesseract not properly installed or configured.\n"
                                    "Please make sure Tesseract OCR is installed on your system.")
                root.config(cursor="")
                return False
        elif current_ocr_engine == "latexocr" and latex_ocr is None:
            if not HAS_LATEX_OCR:
                messagebox.showerror("Error", "LatexOCR is not installed.\n"
                                    "Please install it with 'pip install pix2tex'.")
                root.config(cursor="")
                return False
            latex_ocr = LatexOCR()

        
        # Restore cursor
        root.config(cursor="")
        return True
    except Exception as e:
        root.config(cursor="")
        messagebox.showerror("Error", f"Failed to initialize OCR engine:\n{str(e)}")
        return False

def change_ocr_engine(event):
    """Handle changing the OCR engine"""
    global current_ocr_engine, ocr_engine_combo
    
    new_engine = ocr_engine_combo.get().lower().replace(' ', '')
    
    # Don't reinitialize if it's the same engine
    if new_engine == current_ocr_engine:
        return
    
    # Initialize the new engine
    current_ocr_engine = new_engine
    
    # Show information about the engine
    engine_info = {
        "easyocr": "EasyOCR: General purpose OCR with good language support",
        "pytesseract": "Pytesseract: Fast OCR based on Google's Tesseract engine",
        "latexocr": "LatexOCR: Specialized for mathematical equations and LaTeX",
    }
    
    status_message = f"Changed to {engine_info.get(current_ocr_engine, '')}"
    img_info_label.config(text=status_message)
    
    # Initialize the engine if needed
    threading.Thread(target=initialize_ocr, args=(current_ocr_engine,), daemon=True).start()

def capture_screenshot():
    # Check if OCR is initialized before taking a screenshot
    if not initialize_ocr():
        return
        
    # Minimize the main window while taking screenshots
    root.iconify()
    root.update()
    
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
            success = False
            for tool in tools:
                try:
                    subprocess.run(tool, check=True)
                    success = True
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
                
            if not success:
                root.deiconify()  # Restore window
                messagebox.showerror("Error", "No supported screenshot tool found.")
                return False

        elif system == "Windows":
            # Use a better Windows screenshot approach
            try:
                from PIL import ImageGrab
                import win32gui
                import win32con
                import win32api
                
                # Create a simple instruction window
                instruct = tk.Toplevel()
                instruct.attributes('-topmost', True)
                instruct.geometry("300x100")
                instruct.title("Screenshot")
                tk.Label(instruct, text="Click and drag to select screenshot area.\nPress ESC to cancel.", 
                         padx=20, pady=20).pack(fill=tk.BOTH, expand=True)
                
                def on_click_release(event):
                    instruct.destroy()
                    # Get screen size
                    screen_width = win32api.GetSystemMetrics(0)
                    screen_height = win32api.GetSystemMetrics(1)
                    
                    # Create full screen transparent window
                    overlay = tk.Toplevel()
                    overlay.attributes('-alpha', 0.3)
                    overlay.attributes('-fullscreen', True)
                    overlay.attributes('-topmost', True)
                    canvas = tk.Canvas(overlay, cursor="cross", bg="gray")
                    canvas.pack(fill=tk.BOTH, expand=True)
                    
                    # Variables to store rectangle coordinates
                    start_x = tk.IntVar()
                    start_y = tk.IntVar()
                    end_x = tk.IntVar()
                    end_y = tk.IntVar()
                    drawing = tk.BooleanVar(value=False)
                    rect_id = tk.IntVar(value=None)
                    
                    def on_mouse_down(event):
                        drawing.set(True)
                        start_x.set(event.x)
                        start_y.set(event.y)
                        if rect_id.get():
                            canvas.delete(rect_id.get())
                        rect_id.set(canvas.create_rectangle(
                            event.x, event.y, event.x, event.y, 
                            outline="red", width=2
                        ))
                    
                    def on_mouse_move(event):
                        if drawing.get():
                            end_x.set(event.x)
                            end_y.set(event.y)
                            canvas.coords(rect_id.get(), start_x.get(), start_y.get(), end_x.get(), end_y.get())
                    
                    def on_mouse_up(event):
                        if drawing.get():
                            drawing.set(False)
                            end_x.set(event.x)
                            end_y.set(event.y)
                            overlay.destroy()
                            
                            # Ensure coordinates are in correct order
                            x1 = min(start_x.get(), end_x.get())
                            y1 = min(start_y.get(), end_y.get())
                            x2 = max(start_x.get(), end_x.get())
                            y2 = max(start_y.get(), end_y.get())
                            
                            # Make sure area is valid
                            if x2 - x1 > 10 and y2 - y1 > 10:
                                # Capture the screenshot of selected area
                                screen = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                                screen.save(screenshot_path)
                                root.deiconify()  # Restore window before processing
                                process_screenshot(screenshot_path)
                            else:
                                root.deiconify()  # Restore window
                                messagebox.showerror("Error", "Selected area is too small")
                    
                    def on_escape(event):
                        overlay.destroy()
                        root.deiconify()  # Restore window
                    
                    canvas.bind("<ButtonPress-1>", on_mouse_down)
                    canvas.bind("<B1-Motion>", on_mouse_move)
                    canvas.bind("<ButtonRelease-1>", on_mouse_up)
                    overlay.bind("<Escape>", on_escape)
                    
                instruct.bind("<ButtonRelease-1>", on_click_release)
                return  # Return early as we'll call process_screenshot later
                
            except ImportError:
                # Fallback to simple screenshot if modules aren't available
                screen = ImageGrab.grab()
                screen.save(screenshot_path)

        elif system == "Darwin":  # macOS
            subprocess.run(["screencapture", "-i", screenshot_path], check=True)
        else:
            root.deiconify()  # Restore window
            messagebox.showerror("Error", f"Unsupported operating system: {system}")
            return False

        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            root.deiconify()  # Restore window
            messagebox.showerror("Error", "Screenshot was not captured.")
            return False

        root.deiconify()  # Restore window before processing
        messagebox.showinfo("Success", f"Screenshot captured")
        process_screenshot(screenshot_path)
        return True

    except Exception as e:
        root.deiconify()  # Ensure window is restored
        messagebox.showerror("Error", f"Failed to capture screenshot:\n{str(e)}")
        traceback.print_exc()
        return False

def open_image():
    """Open an image file instead of taking a screenshot"""
    # Check if OCR is initialized before opening an image
    if not initialize_ocr():
        return
        
    # Modern file dialog appearance
    try:
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("TIFF files", "*.tiff *.tif"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~/Pictures") if os.path.exists(os.path.expanduser("~/Pictures")) else os.path.expanduser("~")
        )
        
        if file_path:
            process_screenshot(file_path)
        # If no file is selected, just return to the main interface
        # Don't close the application
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open file dialog: {str(e)}")
        traceback.print_exc()

def process_screenshot(screenshot_path):
    # Show busy cursor
    root.config(cursor="watch")
    root.update()
    
    try:
        screenshot = Image.open(screenshot_path).convert("RGB")
    except Exception as e:
        root.config(cursor="")  # Restore cursor
        messagebox.showerror("Error", f"Failed to open image: {str(e)}")
        return
        
    global copied_to_clipboard
    if screenshot is None:
        messagebox.showerror("Error", "No screenshot available.")
        return
    
    # After taking the screenshot but before processing it, restore the window
    root.deiconify()
    root.lift()
    root.attributes('-topmost', True)
    root.focus_force()
    root.after(500, lambda: root.attributes('-topmost', False))

    try:
        # Process based on selected OCR engine
        if current_ocr_engine == "easyocr":
            # Use direct path for EasyOCR if file exists on disk
            if os.path.exists(screenshot_path):
                results = reader.readtext(screenshot_path)
            else:
                # Save temporarily as EasyOCR sometimes works better with path
                temp_path = os.path.join(tempfile.gettempdir(), "easyocr_temp_image.png")
                screenshot.save(temp_path)
                results = reader.readtext(temp_path)
                try:
                    os.remove(temp_path)
                except:
                    pass
            # Combine all text blocks into one string
            text = "\n".join([line[1] for line in results]).strip()
            
        elif current_ocr_engine == "pytesseract":
            # Use pytesseract for OCR
            text = pytesseract.image_to_string(screenshot)
            
        elif current_ocr_engine == "latexocr":
            # Use LatexOCR for math equation recognition
            if HAS_LATEX_OCR and latex_ocr:
                # Process the image and get LaTeX code
                text = latex_ocr(screenshot)
            else:
                text = "LatexOCR not properly initialized. Please install pix2tex package."
        else:
            text = "Unknown OCR engine selected."

        # Copy to clipboard automatically
        pyperclip.copy(text)
        
        # Update the existing GUI
        update_gui(screenshot, text)
        
    except Exception as e:
        root.config(cursor="")  # Restore cursor
        messagebox.showerror("Error", f"OCR processing error:\n{str(e)}")
        traceback.print_exc()
    finally:
        # Only remove if it's a temporary file
        if screenshot_path.startswith(tempfile.gettempdir()):
            try:
                os.remove(screenshot_path)
            except:
                pass
        
        # Restore cursor
        root.config(cursor="")

def update_gui(image, text):
    """Update the existing GUI with new image and text"""
    global state
    
    # Update text
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", text if text else "")
    
    # Update image
    state["original_image"] = image
    
    # Update image info
    if image and hasattr(image, 'width') and hasattr(image, 'height'):
        img_info_label.config(text=f"{image.width} × {image.height} px")
    
    # Add save image button if not already there
    # Save or update Save Image button
    global save_image_button

    if 'save_image_button' not in globals():
        save_image_button = ttk.Button(
            img_header,
            text="💾 Save Image",
            style="Custom.TButton",
        )
        save_image_button.pack(side=tk.RIGHT, padx=5)

    # Always update the command to the latest image
    save_image_button.configure(command=lambda: save_image(image))

    
    # Force a redraw of the image
    force_redraw_image()

def force_redraw_image():
    """Force a redraw of the image on the canvas"""
    # Get current canvas dimensions
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    
    if w <= 1 or h <= 1:
        # Canvas not ready yet, schedule another attempt
        root.after(100, force_redraw_image)
        return
        
    # Get the image from state
    image = state["original_image"]
    
    if not image:
        return
        
    # Calculate new dimensions
    img_ratio = image.width / image.height
    canvas_ratio = w / h

    if img_ratio > canvas_ratio:
        new_w = w
        new_h = int(w / img_ratio)
    else:
        new_h = h
        new_w = int(h * img_ratio)

    # Resize image
    try:
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    except AttributeError:
        # Fallback for older PIL versions
        resized = image.resize((new_w, new_h), Image.LANCZOS)

    # Create new PhotoImage and update canvas
    state["tk_img"] = ImageTk.PhotoImage(resized)
    canvas.delete("all")
    x = (w - new_w) // 2
    y = (h - new_h) // 2
    canvas.create_image(x, y, anchor="nw", image=state["tk_img"])

def save_image(img):
    """Save the current image to a file"""
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~/Pictures") if os.path.exists(os.path.expanduser("~/Pictures")) else os.path.expanduser("~")
        )
        if file_path:
            img.save(file_path)
            messagebox.showinfo("Success", f"Image saved to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save image: {str(e)}")

def show_gui(original_image=None, text=None):
    global root, text_widget, canvas, text_card, image_card
    global title_frame, text_header, img_header, img_info_label, theme_frame, theme_toggle
    global state, ocr_engine_combo, ocr_engine_frame

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
    
    # Configure combo box style
    style.configure("TCombobox", 
        padding=5
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

    # OCR Engine Selection
    ocr_engine_frame = tk.Frame(title_frame, bg="#e8e8ef")
    ocr_engine_frame.pack(side=tk.LEFT, padx=20)
    
    ocr_engine_label = tk.Label(ocr_engine_frame, text="OCR Engine:", bg="#e8e8ef", font=("Segoe UI", 10))
    ocr_engine_label.pack(side=tk.LEFT, padx=(0, 5))
    all_labels.append(ocr_engine_label)
    
    # OCR Engine Combobox
    ocr_engine_combo = ttk.Combobox(
        ocr_engine_frame,
        values=["EasyOCR", "PyTesseract", "LatexOCR"],
        width=15,
        state="readonly"
    )
    ocr_engine_combo.current(0)  # Set default to EasyOCR
    ocr_engine_combo.pack(side=tk.LEFT)
    ocr_engine_combo.bind("<<ComboboxSelected>>", change_ocr_engine)

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

    # Action buttons
    button_frame = tk.Frame(title_frame, bg="#e8e8ef")
    button_frame.pack(side=tk.RIGHT, padx=10)
    
    # New screenshot button
    ttk.Button(
        button_frame,
        text="📷 New Screenshot",
        style="Custom.TButton",
        command=capture_screenshot
    ).pack(side=tk.RIGHT, padx=5)
    
    # Open image button
    ttk.Button(
        button_frame,
        text="📁 Open Image",
        style="Custom.TButton",
        command=open_image
    ).pack(side=tk.RIGHT, padx=5)

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
    text_widget.insert("1.0", text if text else "")

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

    # Add save image button if there's an image
    if original_image:
        ttk.Button(
            img_header,
            text="💾 Save Image",
            style="Custom.TButton",
            command=lambda: save_image(original_image)
        ).pack(side=tk.RIGHT, padx=5)

    canvas_frame = ttk.Frame(image_card, padding=(10, 5, 10, 10))
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    blank_image = Image.new("RGB", (1, 1), color="white")

    state = {
        "original_image": original_image if original_image is not None else blank_image,
        "tk_img": None  # tk_img will be set later in resize_image
    }

    def resize_image(event=None):
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        resized = state["original_image"].copy()
        
        # Display image dimensions if available
        if hasattr(state["original_image"], 'width') and hasattr(state["original_image"], 'height'):
            img_info_label.config(text=f"{state['original_image'].width} × {state['original_image'].height} px")
        
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
            # Fallback for older PIL versions
            resized = resized.resize((new_w, new_h), Image.LANCZOS)

        state["tk_img"] = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        canvas.create_image(x, y, anchor="nw", image=state["tk_img"])

    canvas.bind("<Configure>", resize_image)
    root.update()
    root.after(100, resize_image)

    # Make sure Windows properly closes the app
    def on_closing():
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    show_gui()
