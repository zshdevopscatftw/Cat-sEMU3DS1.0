import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import random
import math

class Lime3DSEmulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Cat's 3DS EMU 0.2 - Python Edition")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#2C2C2C")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#2C2C2C')
        self.style.configure('TButton', background='#404040', foreground='white', borderwidth=1)
        self.style.map('TButton', background=[('active', '#505050')])
        self.style.configure('TLabel', background='#2C2C2C', foreground='white')

        # Main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side (Screens)
        self.screen_frame = ttk.Frame(self.main_container)
        self.screen_frame.pack(side=tk.LEFT, padx=5)

        # 3DS Top Screen (400x240 native -> scaled x1.5 = 600x360 approx, keeping simple for Tk)
        # Using 400x240 for 1:1 simulation
        self.top_screen_label = ttk.Label(self.screen_frame, text="Top Screen (3D)", font=("Arial", 8))
        self.top_screen_label.pack(anchor="w")
        self.top_screen = tk.Canvas(self.screen_frame, width=400, height=240, bg="black", highlightthickness=0)
        self.top_screen.pack(pady=(0, 10))

        # 3DS Bottom Screen (320x240)
        self.bottom_screen_label = ttk.Label(self.screen_frame, text="Touch Screen", font=("Arial", 8))
        self.bottom_screen_label.pack(anchor="w")
        self.bottom_screen = tk.Canvas(self.screen_frame, width=320, height=240, bg="black", highlightthickness=0)
        self.bottom_screen.pack(pady=(0, 5))

        # Right side (Controls & Log)
        self.control_panel = ttk.Frame(self.main_container)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Button Array
        self.btn_frame = ttk.LabelFrame(self.control_panel, text="System Actions", padding=10)
        self.btn_frame.pack(fill=tk.X, pady=5)

        self.load_btn = ttk.Button(self.btn_frame, text="📂 Load .3ds/.cia", command=self.load_rom)
        self.load_btn.pack(fill=tk.X, pady=2)
        
        self.start_btn = ttk.Button(self.btn_frame, text="▶ Start", command=self.start_emulation, state=tk.DISABLED)
        self.start_btn.pack(fill=tk.X, pady=2)
        
        self.stop_btn = ttk.Button(self.btn_frame, text="⏹ Stop", command=self.stop_emulation, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)

        # Emulation Log
        self.log_label = ttk.Label(self.control_panel, text="Backend Log:")
        self.log_label.pack(anchor="w", pady=(10,0))
        
        self.log_text = tk.Text(self.control_panel, height=15, width=30, bg="black", fg="#00FF00", 
                               font=("Consolas", 8), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=2)

        # State variables
        self.emulation_running = False
        self.rom_loaded = False
        self.current_rom_name = ""
        self.frame_count = 0
        self.objects = [] # For simulated rendering

        # Initial Render
        self.draw_splash_screen()
        self.log("Core initialized. Waiting for ROM...")

    def log(self, message):
        """Thread-safe logging to the GUI console"""
        def _log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"> {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _log)

    def draw_splash_screen(self):
        self.top_screen.delete("all")
        self.bottom_screen.delete("all")
        
        # Gradient-like background effect
        for i in range(0, 240, 4):
            c = hex(int(20 + (i/240)*40))[2:].zfill(2)
            color = f"#{c}{c}{c}"
            self.top_screen.create_line(0, i, 400, i, fill=color, width=4)

        self.top_screen.create_text(200, 100, text="Cat's 3DS EMU", fill="#00FF00", font=("Courier", 24, "bold"))
        self.top_screen.create_text(200, 140, text="Python Backend Sim", fill="white", font=("Arial", 10))

        self.bottom_screen.create_rectangle(0, 0, 320, 240, fill="#202020")
        self.bottom_screen.create_text(160, 120, text="No Cartridge Inserted", fill="gray", font=("Arial", 12))

    def load_rom(self):
        file_path = filedialog.askopenfilename(
            title="Select 3DS ROM",
            filetypes=[("3DS ROMs", "*.3ds *.cia *.cxi"), ("All files", "*.*")]
        )
        
        if file_path:
            self.current_rom_name = file_path.split("/")[-1]
            self.rom_loaded = True
            self.start_btn.config(state=tk.NORMAL)
            self.log(f"ROM Loaded: {self.current_rom_name}")
            self.log("Header parsing... OK")
            self.log("Region: FREE | Encryption: Decrypted")
            
            # Preview on bottom screen
            self.bottom_screen.delete("all")
            self.bottom_screen.create_rectangle(0,0,320,240, fill="#101010")
            self.bottom_screen.create_text(160, 120, text="Ready to Start", fill="cyan")

    def start_emulation(self):
        if not self.emulation_running and self.rom_loaded:
            self.emulation_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.log("Booting ARM11 Core 0...")
            self.log("Booting ARM11 Core 1...")
            self.log("Initializing PICA200 GPU Emulation...")
            
            # Start the emu thread
            threading.Thread(target=self.game_loop, daemon=True).start()

    def stop_emulation(self):
        self.emulation_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.load_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Emulation halted.")
        self.draw_splash_screen()

    def game_loop(self):
        """Simulates the main rendering loop"""
        self.objects = []
        # Create some fake 3D objects
        for _ in range(5):
            self.objects.append({
                "x": random.randint(50, 350),
                "y": random.randint(50, 190),
                "dx": random.choice([-2, 2]),
                "dy": random.choice([-2, 2]),
                "color": random.choice(["red", "blue", "green", "yellow", "purple"])
            })

        self.log("Entering main loop @ 60FPS")
        
        while self.emulation_running:
            start_time = time.time()
            
            # Schedule the frame update on the main UI thread
            self.root.after(0, self.render_frame)
            
            # Calculate FPS sleep (cap at ~60)
            elapsed = time.time() - start_time
            sleep_time = max(0, (1.0/60.0) - elapsed)
            time.sleep(sleep_time)
            
            self.frame_count += 1
            if self.frame_count % 120 == 0: # Log FPS every 2 seconds approx
                self.log(f"SYS: {self.frame_count} frames rendered | VIP: OK")

    def render_frame(self):
        """Updates the canvas elements to simulate a game"""
        if not self.emulation_running: return

        self.top_screen.delete("game_obj")
        self.top_screen.delete("osd")

        # Draw simulated "Game" content
        for obj in self.objects:
            # Move
            obj["x"] += obj["dx"]
            obj["y"] += obj["dy"]
            
            # Bounce
            if obj["x"] <= 0 or obj["x"] >= 400: obj["dx"] *= -1
            if obj["y"] <= 0 or obj["y"] >= 240: obj["dy"] *= -1
            
            # Draw 3D-ish fake cube (simple rect offset)
            x, y, c = obj["x"], obj["y"], obj["color"]
            self.top_screen.create_rectangle(x, y, x+30, y+30, fill=c, tags="game_obj")
            self.top_screen.create_line(x, y, x+10, y-10, fill="white", tags="game_obj")
            self.top_screen.create_line(x+30, y, x+40, y-10, fill="white", tags="game_obj")
            self.top_screen.create_line(x+30, y+30, x+40, y+20, fill="white", tags="game_obj")
            self.top_screen.create_line(x+40, y-10, x+40, y+20, fill="white", tags="game_obj")
            self.top_screen.create_line(x+10, y-10, x+40, y-10, fill="white", tags="game_obj")

        # On Screen Display
        self.top_screen.create_text(10, 10, text=f"FPS: 60.0 | {self.current_rom_name}", 
                                   fill="yellow", anchor="nw", font=("Consolas", 8), tags="osd")

        # Bottom screen interactive element
        self.bottom_screen.delete("touch_ui")
        self.bottom_screen.create_text(160, 120, text="[ Touch Screen Active ]", 
                                      fill="white", tags="touch_ui")

if __name__ == "__main__":
    root = tk.Tk()
    app = Lime3DSEmulator(root)
    root.mainloop()
