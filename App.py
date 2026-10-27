import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from PPMReader import PPMReader
from ImageProcessor import ImageProcessor
from JpegHandler import JpegHandler
from ColorConverter import ColorConverter
from Dialogs import NewImageDialog, PointOperationDialog
from RGBCube import RGBCubeWindow

class PPMJPEGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ppm jpg")
        self.root.geometry("900x700")

        self.image_data = None      
        self.color_space = "RGB"  
        self.tk_image = None       
        self.zoom_level = 1.0       
        self.offset_x = 0       
        self.offset_y = 0
        self.current_width = 0
        self.current_height = 0

        self.ppm_reader = PPMReader()

        self.create_menu()
        self.create_widgets()
        self.bind_shortcuts()
        self.update_color_menu_state()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        # Kategoria: Plik
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nowy...", command=self.new_image, accelerator="Cmd+N")
        file_menu.add_command(label="Otwórz plik...", command=self.load_file, accelerator="Cmd+O")
        file_menu.add_command(label="Zapisz jako JPEG...", command=self.save_jpeg)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjdź", command=self.root.quit)
        menubar.add_cascade(label="Plik", menu=file_menu)

        # Kategoria: Processing
        processing_menu = tk.Menu(menubar, tearoff=0)
        processing_menu.add_command(label="Skalowanie liniowe", command=self.linear_scaling)
        menubar.add_cascade(label="Processing", menu=processing_menu)

        # Kategoria: Przetwarzanie punktowe
        point_menu = tk.Menu(menubar, tearoff=0)
        point_menu.add_command(label="Dodawanie...", command=lambda: self.open_point_dialog("Dodawanie", "add"))
        point_menu.add_command(label="Odejmowanie...", command=lambda: self.open_point_dialog("Odejmowanie", "sub"))
        point_menu.add_command(label="Mnożenie...", command=lambda: self.open_point_dialog("Mnożenie", "mul"))
        point_menu.add_command(label="Dzielenie...", command=lambda: self.open_point_dialog("Dzielenie", "div"))
        point_menu.add_command(label="Zmiana jasności...", command=lambda: self.open_point_dialog("Jasność", "brightness"))
        point_menu.add_separator()
        point_menu.add_command(label="Skala szarości (Średnia)", command=lambda: self.apply_grayscale("average"))
        point_menu.add_command(label="Skala szarości (Luminancja)", command=lambda: self.apply_grayscale("luminosity"))
        menubar.add_cascade(label="Przetwarzanie punktowe", menu=point_menu)

        # NOWA KATEGORIA: Filtrowanie
        filter_menu = tk.Menu(menubar, tearoff=0)
        filter_menu.add_command(label="Filtr wygładzający (uśredniający)", command=self.apply_smoothing)
        filter_menu.add_command(label="Filtr medianowy", command=self.apply_median)
        filter_menu.add_command(label="Filtr wykrywania krawędzi (Sobel)", command=self.apply_sobel)
        filter_menu.add_command(label="Filtr górnoprzepustowy wyostrzający", command=self.apply_sharpening)
        filter_menu.add_command(label="Rozmycie gaussowskie (sigma)...", command=self.open_gaussian_dialog)
        filter_menu.add_command(label="Splot maski (niestandardowa)...", command=self.open_custom_kernel_dialog)
        menubar.add_cascade(label="Filtrowanie", menu=filter_menu)

        # Kategoria: Color
        self.color_menu = tk.Menu(menubar, tearoff=0)
        self.color_menu.add_command(label="Switch to RGB", command=self.switch_to_rgb)
        self.color_menu.add_command(label="Switch to CMYK", command=self.switch_to_cmyk)
        menubar.add_cascade(label="Color", menu=self.color_menu)

        # Kategoria RGB Cube
        rgb_cube_menu = tk.Menu(menubar, tearoff=0)
        rgb_cube_menu.add_command(label="Otwórz kostkę RGB", command=self.open_rgb_cube)
        menubar.add_cascade(label="RGB Cube", menu=rgb_cube_menu)

        self.root.config(menu=menubar)

    def update_color_menu_state(self):
        if self.image_data is None:
            self.color_menu.entryconfig("Switch to RGB", state=tk.DISABLED)
            self.color_menu.entryconfig("Switch to CMYK", state=tk.DISABLED)
        elif self.color_space == "RGB":
            self.color_menu.entryconfig("Switch to RGB", state=tk.DISABLED)
            self.color_menu.entryconfig("Switch to CMYK", state=tk.NORMAL)
        elif self.color_space == "CMYK":
            self.color_menu.entryconfig("Switch to RGB", state=tk.NORMAL)
            self.color_menu.entryconfig("Switch to CMYK", state=tk.DISABLED)

    def switch_to_rgb(self):
        if self.image_data is None or self.color_space == "RGB":
            return
        self.image_data = ColorConverter.convert_image_to_rgb(self.image_data)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Przełączono przestrzeń barwną na RGB")

    def switch_to_cmyk(self):
        if self.image_data is None or self.color_space == "CMYK":
            return
        self.image_data = ColorConverter.convert_image_to_cmyk(self.image_data)
        self.color_space = "CMYK"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Przełączono przestrzeń barwną na CMYK")

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root, bg="gray", cursor="cross", highlightthickness=0, bd=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas.bind("<B1-Motion>", self.pan_image)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<MouseWheel>", self.zoom_image) 
        self.canvas.bind("<Button-4>", self.zoom_image)   
        self.canvas.bind("<Button-5>", self.zoom_image)   
        self.canvas.bind("<Motion>", self.show_pixel_info)
        self.canvas.bind("<Configure>", lambda e: self.display_image())

        self.status_var = tk.StringVar()
        self.status_var.set("Otwórz plik PPM lub JPEG lub utwórz Nowy.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def bind_shortcuts(self):
        for sc in ["<Control-plus>", "<Control-equal>", "<Command-plus>", "<Command-equal>"]:
            self.root.bind(sc, lambda e: self.zoom_image_keyboard(direction="in"))
        for sc in ["<Control-minus>", "<Command-minus>"]:
            self.root.bind(sc, lambda e: self.zoom_image_keyboard(direction="out"))

    def new_image(self):
        NewImageDialog(self.root, self._create_blank_image)

    def _create_blank_image(self, width, height, mode="RGB", bg_color=(255, 255, 255)):
        self.current_width = width
        self.current_height = height
        
        self.image_data = Image.new(mode, (width, height), bg_color)
        self.color_space = mode
        
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.center_image()
        self.update_color_menu_state()
        self.display_image()
        
        if mode == "RGB":
            color_desc = f"RGB{bg_color}"
        else:
            c, m, y, k = [int(round((v / 255.0) * 100)) for v in bg_color]
            color_desc = f"CMYK({c}%, {m}%, {y}%, {k}%)"
            
        self.status_var.set(f"Utworzono nowy obraz: {width}x{height} px | Przestrzeń: {mode} | Tło: {color_desc}")

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Wszystkie obsługiwane", "*.ppm *.jpg *.jpeg"), ("Format PPM", "*.ppm"), ("Format JPEG", "*.jpg *.jpeg")]
        )
        if not file_path:
            return

        try:
            if file_path.lower().endswith(".ppm"):
                self.load_ppm(file_path)
            elif file_path.lower().endswith((".jpg", ".jpeg")):
                self.load_jpeg(file_path)
            else:
                raise ValueError("Nieobsługiwany format pliku")
            
            self.color_space = "RGB"  
            self.zoom_level = 1.0
            self.offset_x = 0
            self.offset_y = 0
            self.center_image()
            self.update_color_menu_state()
            self.display_image()
            self.status_var.set(f"Wczytano plik: {file_path}")
        except Exception as e:
            messagebox.showerror("Błąd wczytywania", f"Wystąpił błąd podczas parsowania pliku:\n{str(e)}")

    def open_rgb_cube(self):
        RGBCubeWindow(self.root)

    def center_image(self):
        if self.image_data is None:
            return
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10: canvas_w = 900
        if canvas_h < 10: canvas_h = 600

        zoom_w = canvas_w / self.current_width
        zoom_h = canvas_h / self.current_height
        self.zoom_level = min(1.0, zoom_w, zoom_h)
        if self.zoom_level < 0.1: 
            self.zoom_level = 0.1

        self.offset_x = (canvas_w - self.current_width * self.zoom_level) / 2
        self.offset_y = (canvas_h - self.current_height * self.zoom_level) / 2

    def load_ppm(self, file_path):
        ppm_data = self.ppm_reader.read_ppm(file_path)  
        self.current_width = ppm_data["width"]
        self.current_height = ppm_data["height"]
        pixel_bytes = bytes(ppm_data["pixels"])
        self.image_data = Image.frombytes("RGB", (self.current_width, self.current_height), pixel_bytes)    

    def load_jpeg(self, file_path):
        self.image_data, self.current_width, self.current_height = JpegHandler.load_jpeg(file_path)

    def save_jpeg(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Brak wczytanego obrazu do zapisu!")
            return
        export_img = self.image_data
        if self.color_space == "CMYK":
            export_img = ColorConverter.convert_image_to_rgb(self.image_data)
        JpegHandler.save_jpeg(self.root, export_img)

    def linear_scaling(self):
        if self.image_data is None:
            messagebox.showwarning("Error", "Load file first.")
            return
        if self.color_space == "CMYK":
            self.image_data = ColorConverter.convert_image_to_rgb(self.image_data)
            self.color_space = "RGB"
            self.update_color_menu_state()

        self.image_data = ImageProcessor.linear_scaling(self.image_data, self.current_width, self.current_height)
        self.display_image()
        messagebox.showinfo("Sukces", "Wykonano skalowanie liniowe")

    def display_image(self):
        if self.image_data is None:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 10 or canvas_height < 10:
            return

        image_x1 = max(0, int(-self.offset_x / self.zoom_level))
        image_y1 = max(0, int(-self.offset_y / self.zoom_level))
        image_x2 = min(self.current_width, int((canvas_width - self.offset_x) / self.zoom_level) + 1)
        image_y2 = min(self.current_height, int((canvas_height - self.offset_y) / self.zoom_level) + 1)

        if image_x1 >= image_x2 or image_y1 >= image_y2:
            self.canvas.delete("all")
            return

        cropped_image = self.image_data.crop((image_x1, image_y1, image_x2, image_y2))
        cropped_display = ColorConverter.convert_image_to_rgb(cropped_image) if self.color_space == "CMYK" else cropped_image

        destination_width = int((image_x2 - image_x1) * self.zoom_level)
        destination_height = int((image_y2 - image_y1) * self.zoom_level)

        if destination_width > 0 and destination_height > 0:
            resample_method = Image.Resampling.NEAREST if self.zoom_level > 4.0 else Image.Resampling.BILINEAR
            resized_image = cropped_display.resize((destination_width, destination_height), resample_method)
            
            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.canvas.delete("all")
            
            draw_x = self.offset_x + image_x1 * self.zoom_level
            draw_y = self.offset_y + image_y1 * self.zoom_level
            self.canvas.create_image(draw_x, draw_y, anchor=tk.NW, image=self.tk_image)

    def start_pan(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def pan_image(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.offset_x += dx
        self.offset_y += dy
        self.start_x = event.x
        self.start_y = event.y
        self.display_image()

    def zoom_image(self, event):
        zoom_factor = 1.15
        if hasattr(event, 'delta') and event.delta != 0:
            factor = zoom_factor if event.delta > 0 else (1 / zoom_factor)
        elif hasattr(event, 'num'):
            factor = zoom_factor if event.num == 4 else (1 / zoom_factor)
        else:
            return
        self.apply_zoom_at(factor, event.x, event.y)

    def zoom_image_keyboard(self, direction):
        zoom_factor = 1.15
        factor = zoom_factor if direction == "in" else (1 / zoom_factor)
        canvas_w = self.canvas.winfo_width() / 2
        canvas_h = self.canvas.winfo_height() / 2
        self.apply_zoom_at(factor, canvas_w, canvas_h)

    def apply_zoom_at(self, factor, center_x, center_y):
        old_zoom = self.zoom_level
        new_zoom = max(0.05, min(old_zoom * factor, 50.0))
        
        self.offset_x = center_x - (center_x - self.offset_x) * (new_zoom / old_zoom)
        self.offset_y = center_y - (center_y - self.offset_y) * (new_zoom / old_zoom)
        self.zoom_level = new_zoom
        self.display_image()

    def show_pixel_info(self, event):
        global info_str
        if self.image_data is None:
            return

        img_x = int((event.x - self.offset_x) / self.zoom_level)
        img_y = int((event.y - self.offset_y) / self.zoom_level)

        if 0 <= img_x < self.current_width and 0 <= img_y < self.current_height:
            pixel_val = self.image_data.getpixel((img_x, img_y))

            if self.color_space == "RGB":
                r, g, b = pixel_val[:3]
                info_str = f"X: {img_x}, Y: {img_y} | R: {r}, G: {g}, B: {b}"
            elif self.color_space == "CMYK":
                c_b, m_b, y_b, k_b = pixel_val
                c_pct = int(round((c_b / 255.0) * 100))
                m_pct = int(round((m_b / 255.0) * 100))
                y_pct = int(round((y_b / 255.0) * 100))
                k_pct = int(round((k_b / 255.0) * 100))
                info_str = f"X: {img_x}, Y: {img_y} | C: {c_pct}%, M: {m_pct}%, Y: {y_pct}%, K: {k_pct}%"
            
            if self.zoom_level >= 4.0:
                info_str += f" | Zoom: {self.zoom_level:.1f}x"
            
            self.status_var.set(info_str)
        else:
            self.status_var.set("Kursor poza obszarem obrazu")

    def open_point_dialog(self, title, op_type):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        PointOperationDialog(self.root, title, lambda vals: self.execute_point_operation(op_type, vals))

    def execute_point_operation(self, op_type, vals):
        self.image_data = ImageProcessor.point_operation(self.image_data, op_type, vals)
        self.display_image()
        self.status_var.set(f"Wykonano operację punktową: {op_type}")

    def apply_grayscale(self, method):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        self.image_data = ImageProcessor.convert_to_grayscale(self.image_data, method)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set(f"Przekształcono do skali szarości metodą: {method}")

    def apply_smoothing(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        self.image_data = ImageProcessor.smoothing_filter(self.image_data)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Zastosowano filtr wygładzający (uśredniający)")

    def apply_median(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        self.image_data = ImageProcessor.median_filter(self.image_data)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Zastosowano filtr medianowy")

    def apply_sobel(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        self.image_data = ImageProcessor.sobel_filter(self.image_data)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Zastosowano filtr wykrywania krawędzi (Sobel)")

    def apply_sharpening(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        self.image_data = ImageProcessor.sharpening_filter(self.image_data)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Zastosowano filtr górnoprzepustowy wyostrzający")

    def open_gaussian_dialog(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        PointOperationDialog.GaussianBlurDialog(self.root, self.execute_gaussian_blur)

    def execute_gaussian_blur(self, sigma):
        self.image_data = ImageProcessor.gaussian_blur(self.image_data, sigma)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set(f"Zastosowano rozmycie gaussowskie (sigma = {sigma})")

    def open_custom_kernel_dialog(self):
        if self.image_data is None:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj lub utwórz obraz!")
            return
        PointOperationDialog.CustomKernelDialog(self.root, self.execute_custom_convolution)

    def execute_custom_convolution(self, kernel):
        self.image_data = ImageProcessor.custom_convolution(self.image_data, kernel)
        self.color_space = "RGB"
        self.update_color_menu_state()
        self.display_image()
        self.status_var.set("Zastosowano splot niestandardowej maski")