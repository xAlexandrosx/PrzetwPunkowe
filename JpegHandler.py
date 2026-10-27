from PIL import Image
from tkinter import filedialog, messagebox
import tkinter as tk

class JpegHandlerDialog:
    """Klasa pomocnicza do obsługi niestandardowego okna dialogowego jakości JPEG (zapobiega zawieszaniu na macOS)."""
    def __init__(self, root, image_data):
        self.root = root
        self.image_data = image_data
        
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Kompresja JPEG")
        self.dialog.geometry("300x130")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Podaj stopień kompresji (1-95):", font=("Arial", 12)).pack(pady=(15, 5))

        self.quality_entry = tk.Entry(self.dialog, width=10, justify="center", font=("Arial", 12))
        self.quality_entry.insert(0, "85")
        self.quality_entry.pack(pady=5)
        self.quality_entry.focus_set()
        self.quality_entry.select_range(0, tk.END)

        btn_confirm = tk.Button(self.dialog, text="Zapisz", command=self.on_confirm, width=10)
        btn_confirm.pack(pady=10)

        self.dialog.bind("<Return>", lambda e: self.on_confirm())

    def on_confirm(self):
        try:
            quality = int(self.quality_entry.get())
            if not (1 <= quality <= 95):
                raise ValueError
            self.dialog.destroy()
            self.root.after(50, lambda: self.execute_save(quality))
        except ValueError:
            messagebox.showerror("Błąd", "Wartość musi być liczbą całkowitą z zakresu od 1 do 95.", parent=self.dialog)

    def execute_save(self, quality):
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("Plik JPEG", "*.jpg *.jpeg")])
        if not file_path:
            return

        try:
            self.image_data.save(file_path, "JPEG", quality=quality)
            messagebox.showinfo("Sukces", f"Zapisano plik pomyślnie:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać pliku:\n{str(e)}")


class JpegHandler:
    @staticmethod
    def load_jpeg(file_path):
        """Wczytuje plik JPEG i zwraca obiekt obrazu PIL w formacie RGB oraz jego wymiary."""
        image_data = Image.open(file_path).convert("RGB")
        width, height = image_data.size
        return image_data, width, height

    @staticmethod
    def save_jpeg(root, image_data):
        """Obsługuje okno dialogowe wyboru jakości (1-95), ścieżki zapisu i zapisuje plik JPEG."""
        if image_data is None:
            messagebox.showwarning("Uwaga", "Brak wczytanego obrazu do zapisu!")
            return
        
        JpegHandlerDialog(root, image_data)