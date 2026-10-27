# main.py
import tkinter as tk
from App import PPMJPEGApp

def main():
    root = tk.Tk()
    app = PPMJPEGApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()