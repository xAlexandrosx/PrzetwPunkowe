import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class RGBCubeWindow:
    """Okno dialogowe wyświetlające kostkę RGB 3D oraz jej przekrój."""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("RGB Cube 3D & Przekrój")
        self.window.geometry("950x650")
        self.window.minsize(800, 550)

        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = plt.Figure(figsize=(9, 6), dpi=100)

        self.ax3d = self.fig.add_subplot(121, projection='3d')
        self.ax3d.set_title("Kostka RGB 3D")
        self.ax3d.set_xlabel("Red")
        self.ax3d.set_ylabel("Green")
        self.ax3d.set_zlabel("Blue")

        self.ax2d = self.fig.add_subplot(122)
        self.im_plot = None

        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Oś przekroju:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(5, 2))
        self.axis_var = tk.StringVar(value="Red")
        self.axis_dropdown = ttk.Combobox(
            control_frame, 
            textvariable=self.axis_var, 
            values=["Red", "Green", "Blue"], 
            state="readonly", 
            width=8
        )
        self.axis_dropdown.pack(side=tk.LEFT, padx=(0, 15))
        self.axis_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_slice(self.slice_slider.get()))

        self.slider_label = ttk.Label(control_frame, text="Wartość Red (0-255):", font=("Arial", 10))
        self.slider_label.pack(side=tk.LEFT, padx=5)
        
        self.slice_slider = ttk.Scale(control_frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.slice_slider.set(128)
        self.slice_slider.config(command=self.update_slice)
        self.slice_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self.draw_cube()

    def draw_cube(self):
        """Rysuje siatkę punktów reprezentującą przestrzeń barw RGB."""
        size = 27
        r = np.linspace(0, 255, size)
        g = np.linspace(0, 255, size)
        b = np.linspace(0, 255, size)
        R, G, B = np.meshgrid(r, g, b)

        colors = np.stack([R.ravel()/255.0, G.ravel()/255.0, B.ravel()/255.0], axis=-1)

        self.ax3d.scatter(R.ravel(), G.ravel(), B.ravel(), c=colors, marker='s', s=15)
        self.ax3d.set_xlim([0, 255])
        self.ax3d.set_ylim([0, 255])
        self.ax3d.set_zlim([0, 255])
        
        self.ax3d.set_box_aspect([1, 1, 1])

        self.update_slice(128)

    def update_slice(self, val):
        """Generuje i wyświetla przekrój 2D dla wybranej osi oraz wartości."""

        val_int = int(float(val))
        axis = self.axis_var.get()

        self.slider_label.config(text=f"Wartość {axis} (0-255):")
        
        steps = 50
        
        if axis == "Red":
            self.ax2d.set_title(f"Przekrój 2D (Red = {val_int})")
            self.ax2d.set_xlabel("Green")
            self.ax2d.set_ylabel("Blue")

            g = np.linspace(0, 255, steps)
            b = np.linspace(0, 255, steps)
            G, B = np.meshgrid(g, b)
            R = np.full_like(G, val_int)

        elif axis == "Green":
            self.ax2d.set_title(f"Przekrój 2D (Green = {val_int})")
            self.ax2d.set_xlabel("Red")
            self.ax2d.set_ylabel("Blue")

            r = np.linspace(0, 255, steps)
            b = np.linspace(0, 255, steps)
            R, B = np.meshgrid(r, b)
            G = np.full_like(R, val_int)

        elif axis == "Blue":
            self.ax2d.set_title(f"Przekrój 2D (Blue = {val_int})")
            self.ax2d.set_xlabel("Red")
            self.ax2d.set_ylabel("Green")

            r = np.linspace(0, 255, steps)
            g = np.linspace(0, 255, steps)
            R, G = np.meshgrid(r, g)
            B = np.full_like(R, val_int)

        color_grid = np.stack([R/255.0, G/255.0, B/255.0], axis=-1)

        if self.im_plot is None:
            self.im_plot = self.ax2d.imshow(color_grid, extent=[0, 255, 0, 255], origin='lower')
        else:
            self.im_plot.set_data(color_grid)

        self.canvas.draw_idle()