import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import colorsys

class NewImageDialog:
    """Rozbudowane okno dialogowe do tworzenia nowego obrazu z wyborem koloru tła (RGB/CMYK) i wykresem kolorów."""
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback

        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Nowy obraz")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()

        self.color_mode = tk.StringVar(value="RGB")
        
        self.r_var = tk.IntVar(value=255)
        self.g_var = tk.IntVar(value=255)
        self.b_var = tk.IntVar(value=255)

        self.c_var = tk.IntVar(value=0)
        self.m_var = tk.IntVar(value=0)
        self.y_var = tk.IntVar(value=0)
        self.k_var = tk.IntVar(value=0)

        self.hue_val = 0.0
        self.sat_val = 0.0
        self.val_val = 1.0

        self.updating_widgets = False

        self._build_ui()
        
        self.dialog.bind("<Return>", lambda e: self.on_confirm())
        self.width_entry.focus_set()
        self.width_entry.select_range(0, tk.END)

    def _build_ui(self):
        main_frame = tk.Frame(self.dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        dim_frame = tk.LabelFrame(main_frame, text=" Wymiary obrazu ", padx=10, pady=10)
        dim_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(dim_frame, text="Szerokość (px):").grid(row=0, column=0, sticky="w", pady=2)
        self.width_entry = tk.Entry(dim_frame, width=10, justify="center")
        self.width_entry.insert(0, "800")
        self.width_entry.grid(row=0, column=1, padx=(10, 0), pady=2)

        tk.Label(dim_frame, text="Wysokość (px):").grid(row=1, column=0, sticky="w", pady=2)
        self.height_entry = tk.Entry(dim_frame, width=10, justify="center")
        self.height_entry.insert(0, "600")
        self.height_entry.grid(row=1, column=1, padx=(10, 0), pady=2)

        color_frame = tk.LabelFrame(main_frame, text=" Kolor tła ", padx=10, pady=10)
        color_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        mode_frame = tk.Frame(color_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(mode_frame, text="RGB", variable=self.color_mode, value="RGB", 
                       command=self._on_mode_change).pack(side=tk.LEFT, padx=(0, 15))
        tk.Radiobutton(mode_frame, text="CMYK", variable=self.color_mode, value="CMYK", 
                       command=self._on_mode_change).pack(side=tk.LEFT)

        picker_container = tk.Frame(color_frame)
        picker_container.pack(fill=tk.BOTH, expand=True)

        chart_frame = tk.Frame(picker_container)
        chart_frame.pack(side=tk.LEFT, padx=(0, 15))

        self.canvas_2d = tk.Canvas(chart_frame, width=150, height=150, relief=tk.SUNKEN, bd=1)
        self.canvas_2d.pack(side=tk.LEFT)
        self.canvas_2d.bind("<Button-1>", self._on_2d_click)
        self.canvas_2d.bind("<B1-Motion>", self._on_2d_click)

        self.canvas_hue = tk.Canvas(chart_frame, width=20, height=150, relief=tk.SUNKEN, bd=1)
        self.canvas_hue.pack(side=tk.LEFT, padx=(5, 0))
        self.canvas_hue.bind("<Button-1>", self._on_hue_click)
        self.canvas_hue.bind("<B1-Motion>", self._on_hue_click)

        self.controls_frame = tk.Frame(picker_container)
        self.controls_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        preview_frame = tk.Frame(color_frame, pady=5)
        preview_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(preview_frame, text="Podgląd:").pack(side=tk.LEFT, padx=(0, 5))
        self.color_preview = tk.Label(preview_frame, bg="#FFFFFF", width=15, height=1, relief=tk.SOLID, bd=1)
        self.color_preview.pack(side=tk.LEFT)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        btn_confirm = tk.Button(btn_frame, text="Utwórz", command=self.on_confirm, width=12)
        btn_confirm.pack(side=tk.RIGHT)

        self._draw_hue_bar()
        self._redraw_2d_canvas()
        self._rebuild_controls()
        self._update_ui_from_values()

    def _draw_hue_bar(self):
        img = Image.new("RGB", (20, 150))
        draw = ImageDraw.Draw(img)
        for y in range(150):
            h = y / 150.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
            draw.line([(0, y), (20, y)], fill=(r, g, b))
        self.hue_img = ImageTk.PhotoImage(img)
        self.canvas_hue.create_image(0, 0, anchor=tk.NW, image=self.hue_img)

    def _redraw_2d_canvas(self):
        img = Image.new("RGB", (150, 150))
        draw = ImageDraw.Draw(img)
        for y in range(150):
            v = 1.0 - (y / 150.0) 
            for x in range(150):
                s = x / 150.0     
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(self.hue_val, s, v)]
                draw.point((x, y), fill=(r, g, b))
        self.img_2d = ImageTk.PhotoImage(img)
        self.canvas_2d.create_image(0, 0, anchor=tk.NW, image=self.img_2d)
        
        px = int(self.sat_val * 150)
        py = int((1.0 - self.val_val) * 150)
        self.canvas_2d.create_oval(px - 4, py - 4, px + 4, py + 4, outline="white", width=2)
        self.canvas_2d.create_oval(px - 3, py - 3, px + 3, py + 3, outline="black", width=1)

    def _on_hue_click(self, event):
        y = max(0, min(150, event.y))
        self.hue_val = y / 150.0
        self._redraw_2d_canvas()
        self._calculate_color_from_hsv()

    def _on_2d_click(self, event):
        x = max(0, min(150, event.x))
        y = max(0, min(150, event.y))
        self.sat_val = x / 150.0
        self.val_val = 1.0 - (y / 150.0)
        self._redraw_2d_canvas()
        self._calculate_color_from_hsv()

    def _calculate_color_from_hsv(self):
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(self.hue_val, self.sat_val, self.val_val)]
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)

        c, m, y_col, k = self._rgb_to_cmyk(r, g, b)
        self.c_var.set(c)
        self.m_var.set(m)
        self.y_var.set(y_col)
        self.k_var.set(k)

        self._update_ui_from_values(update_entries_only=True)

    def _rebuild_controls(self):
        for w in self.controls_frame.winfo_children():
            w.destroy()

        mode = self.color_mode.get()
        if mode == "RGB":
            self._add_entry_row("R (0-255):", self.r_var, self._on_rgb_change)
            self._add_entry_row("G (0-255):", self.g_var, self._on_rgb_change)
            self._add_entry_row("B (0-255):", self.b_var, self._on_rgb_change)
        else:
            self._add_entry_row("C (%):", self.c_var, self._on_cmyk_change)
            self._add_entry_row("M (%):", self.m_var, self._on_cmyk_change)
            self._add_entry_row("Y (%):", self.y_var, self._on_cmyk_change)
            self._add_entry_row("K (%):", self.k_var, self._on_cmyk_change)

    def _add_entry_row(self, label_text, variable, callback):
        row = tk.Frame(self.controls_frame)
        row.pack(fill=tk.X, pady=4)

        tk.Label(row, text=label_text, width=9, anchor="w").pack(side=tk.LEFT)
        entry = tk.Entry(row, textvariable=variable, width=8, justify="center")
        entry.pack(side=tk.LEFT)
        entry.bind("<KeyRelease>", lambda e: callback())

    def _on_mode_change(self):
        self._rebuild_controls()
        self._update_ui_from_values()

    def _on_rgb_change(self):
        if self.updating_widgets: return
        try:
            r = max(0, min(255, self.r_var.get()))
            g = max(0, min(255, self.g_var.get()))
            b = max(0, min(255, self.b_var.get()))
        except tk.TclError:
            return

        c, m, y, k = self._rgb_to_cmyk(r, g, b)
        self.c_var.set(c)
        self.m_var.set(m)
        self.y_var.set(y)
        self.k_var.set(k)

        self._sync_hsv_from_rgb(r, g, b)
        self._redraw_2d_canvas()
        self._update_preview()

    def _on_cmyk_change(self):
        if self.updating_widgets: return
        try:
            c = max(0, min(100, self.c_var.get()))
            m = max(0, min(100, self.m_var.get()))
            y = max(0, min(100, self.y_var.get()))
            k = max(0, min(100, self.k_var.get()))
        except tk.TclError:
            return

        r, g, b = self._cmyk_to_rgb(c, m, y, k)
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)

        self._sync_hsv_from_rgb(r, g, b)
        self._redraw_2d_canvas()
        self._update_preview()

    def _sync_hsv_from_rgb(self, r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self.hue_val = h
        self.sat_val = s
        self.val_val = v

    def _update_ui_from_values(self, update_entries_only=False):
        self.updating_widgets = True
        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        if not update_entries_only:
            self._sync_hsv_from_rgb(r, g, b)
            self._redraw_2d_canvas()
        self._update_preview()
        self.updating_widgets = False

    def _update_preview(self):
        hex_color = f"#{self.r_var.get():02x}{self.g_var.get():02x}{self.b_var.get():02x}"
        self.color_preview.config(bg=hex_color)

    @staticmethod
    def _rgb_to_cmyk(r, g, b):
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100
        c = 1 - (r / 255.0)
        m = 1 - (g / 255.0)
        y = 1 - (b / 255.0)
        k = min(c, m, y)
        if k == 1.0:
            return 0, 0, 0, 100
        c = (c - k) / (1 - k)
        m = (m - k) / (1 - k)
        y = (y - k) / (1 - k)
        return int(round(c * 100)), int(round(m * 100)), int(round(y * 100)), int(round(k * 100))

    @staticmethod
    def _cmyk_to_rgb(c, m, y, k):
        c_f, m_f, y_f, k_f = c / 100.0, m / 100.0, y / 100.0, k / 100.0
        r = int(round(255 * (1 - c_f) * (1 - k_f)))
        g = int(round(255 * (1 - m_f) * (1 - k_f)))
        b = int(round(255 * (1 - y_f) * (1 - k_f)))
        return r, g, b

    def on_confirm(self):
        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
            if w <= 0 or h <= 0:
                raise ValueError
            
            mode = self.color_mode.get()
            if mode == "RGB":
                color_tuple = (self.r_var.get(), self.g_var.get(), self.b_var.get())
            else:
                c_b = int(round((self.c_var.get() / 100.0) * 255))
                m_b = int(round((self.m_var.get() / 100.0) * 255))
                y_b = int(round((self.y_var.get() / 100.0) * 255))
                k_b = int(round((self.k_var.get() / 100.0) * 255))
                color_tuple = (c_b, m_b, y_b, k_b)

            self.dialog.destroy()
            self.callback(w, h, mode, color_tuple)
        except ValueError:
            messagebox.showerror("Błąd", "Wymiary oraz wartości kolorów muszą być poprawnymi liczbami.", parent=self.dialog)


class PointOperationDialog:
    """Uniwersalne okno dialogowe do obsługi operacji punktowych (dodawanie, odejmowanie, mnożenie, dzielenie, jasność)."""

    def __init__(self, root, operation_name, callback):
        self.root = root
        self.operation_name = operation_name
        self.callback = callback

        self.dialog = tk.Toplevel(self.root)
        self.dialog.title(f"Operacja punktowa: {operation_name}")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()

        self.val1 = tk.DoubleVar(value=0.0 if operation_name != 'mul' and operation_name != 'div' else 1.0)
        self.val2 = tk.DoubleVar(value=0.0 if operation_name != 'mul' and operation_name != 'div' else 1.0)
        self.val3 = tk.DoubleVar(value=0.0 if operation_name != 'mul' and operation_name != 'div' else 1.0)
        self.val4 = tk.DoubleVar(value=0.0 if operation_name != 'mul' and operation_name != 'div' else 1.0)

        self._build_ui()
        self.dialog.bind("<Return>", lambda e: self.on_confirm())

    def _build_ui(self):
        main_frame = tk.Frame(self.dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text=f"Wprowadź wartości dla operacji: {self.operation_name}",
                 font=("Arial", 10, "bold")).pack(pady=(0, 10))

        form_frame = tk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=5)

        if self.operation_name == "Jasność":
            tk.Label(form_frame, text="Zmiana poziomu (-255 do 255):").grid(row=0, column=0, sticky="w", pady=2)
            tk.Entry(form_frame, textvariable=self.val1, width=10, justify="center").grid(row=0, column=1, padx=5)
        else:
            labels = ["Kanał 1 (R/C):", "Kanał 2 (G/M):", "Kanał 3 (B/Y):", "Kanał 4 (K):"]
            variables = [self.val1, self.val2, self.val3, self.val4]
            for i, (lbl, var) in enumerate(zip(labels, variables)):
                tk.Label(form_frame, text=lbl).grid(row=i, column=0, sticky="w", pady=2)
                tk.Entry(form_frame, textvariable=var, width=10, justify="center").grid(row=i, column=1, padx=5, pady=2)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Button(btn_frame, text="Anuluj", command=self.dialog.destroy, width=10).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Zastosuj", command=self.on_confirm, width=10).pack(side=tk.RIGHT)

    def on_confirm(self):
        try:
            if self.operation_name == "Jasność":
                vals = (int(self.val1.get()),)
            else:
                vals = (
                    float(self.val1.get()),
                    float(self.val2.get()),
                    float(self.val3.get()),
                    float(self.val4.get())
                )
            self.dialog.destroy()
            self.callback(vals)
        except ValueError:
            messagebox.showerror("Błąd", "Wprowadzone wartości muszą być poprawnymi liczbami.", parent=self.dialog)

    class GaussianBlurDialog:
        """Okno dialogowe do wyboru wartości sigma dla rozmycia gaussowskiego."""

        def __init__(self, root, callback):
            self.root = root
            self.callback = callback

            self.dialog = tk.Toplevel(self.root)
            self.dialog.title("Rozmycie gaussowskie")
            self.dialog.resizable(False, False)
            self.dialog.grab_set()

            self.sigma_var = tk.DoubleVar(value=1.0)
            self._build_ui()
            self.dialog.bind("<Return>", lambda e: self.on_confirm())

        def _build_ui(self):
            main_frame = tk.Frame(self.dialog, padx=15, pady=15)
            main_frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(main_frame, text="Wprowadź wartość Sigma (np. 1.0 - 5.0):").pack(anchor="w", pady=(0, 5))
            self.entry = tk.Entry(main_frame, textvariable=self.sigma_var, width=15, justify="center")
            self.entry.pack(fill=tk.X, pady=(0, 15))
            self.entry.focus_set()
            self.entry.select_range(0, tk.END)

            btn_frame = tk.Frame(main_frame)
            btn_frame.pack(fill=tk.X)
            tk.Button(btn_frame, text="Anuluj", command=self.dialog.destroy, width=10).pack(side=tk.LEFT)
            tk.Button(btn_frame, text="Zastosuj", command=self.on_confirm, width=10).pack(side=tk.RIGHT)

        def on_confirm(self):
            try:
                val = float(self.sigma_var.get())
                if val <= 0:
                    raise ValueError
                self.dialog.destroy()
                self.callback(val)
            except ValueError:
                messagebox.showerror("Błąd", "Wartość sigma musi być dodatnią liczbą.", parent=self.dialog)

    class CustomKernelDialog:
        """Okno dialogowe do wprowadzania własnej macierzi splotu o dowolnym rozmiarze."""

        def __init__(self, root, callback):
            self.root = root
            self.callback = callback

            self.dialog = tk.Toplevel(self.root)
            self.dialog.title("Splot maski (niestandardowa)")
            self.dialog.resizable(False, False)
            self.dialog.grab_set()

            self.size_var = tk.IntVar(value=3)
            self.entries = []

            self._build_ui()
            self.dialog.bind("<Return>", lambda e: self.on_confirm())

        def _build_ui(self):
            self.main_frame = tk.Frame(self.dialog, padx=15, pady=15)
            self.main_frame.pack(fill=tk.BOTH, expand=True)

            top_f = tk.Frame(self.main_frame)
            top_f.pack(fill=tk.X, pady=(0, 10))
            tk.Label(top_f, text="Rozmiar maski (nieparzysty, np. 3, 5):").pack(side=tk.LEFT)
            self.size_entry = tk.Entry(top_f, textvariable=self.size_var, width=5, justify="center")
            self.size_entry.pack(side=tk.LEFT, padx=5)
            tk.Button(top_f, text="Generuj siatkę", command=self._rebuild_grid).pack(side=tk.LEFT, padx=5)

            self.grid_frame = tk.Frame(self.main_frame)
            self.grid_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            self._rebuild_grid()

            btn_frame = tk.Frame(self.main_frame)
            btn_frame.pack(fill=tk.X, pady=(10, 0))
            tk.Button(btn_frame, text="Anuluj", command=self.dialog.destroy, width=10).pack(side=tk.LEFT)
            tk.Button(btn_frame, text="Zastosuj", command=self.on_confirm, width=10).pack(side=tk.RIGHT)

        def _rebuild_grid(self):
            for w in self.grid_frame.winfo_children():
                w.destroy()
            self.entries = []

            try:
                size = int(self.size_var.get())
                if size < 1 or size % 2 == 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Błąd", "Rozmiar musi być nieparzystą liczbą całkowitą >= 1.", parent=self.dialog)
                return

            for r in range(size):
                row_list = []
                row_f = tk.Frame(self.grid_frame)
                row_f.pack()
                for c in range(size):
                    ent = tk.Entry(row_f, width=6, justify="center")
                    ent.insert(0, "1" if r == size // 2 and c == size // 2 else "0")
                    ent.pack(side=tk.LEFT, padx=2, pady=2)
                    row_list.append(ent)
                self.entries.append(row_list)
            self.dialog.update_idletasks()

        def on_confirm(self):
            try:
                kernel = []
                for row in self.entries:
                    kernel_row = [float(e.get()) for e in row]
                    kernel.append(kernel_row)
                self.dialog.destroy()
                self.callback(kernel)
            except ValueError:
                messagebox.showerror("Błąd", "Wszystkie elementy maski muszą być poprawnymi liczbami.",
                                     parent=self.dialog)