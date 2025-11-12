import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from fw_core.model import Layup, Geometry
from fw_core.presets import MATERIALS, PROCESSES
from fw_core import parser, geometry, layup_io, autoclave

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class FWApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Filament Winding Tool")
        self._build_widgets()

    def _build_widgets(self):
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Sequenz
        ttk.Label(top, text="Sequenz").grid(row=0, column=0, sticky="w")
        self.seq_var = tk.StringVar(value="[0/±45/90]s")
        ttk.Entry(top, textvariable=self.seq_var, width=25)\
            .grid(row=0, column=1, sticky="we")

        # Plydicke
        ttk.Label(top, text="Plydicke [mm]").grid(row=0, column=2, sticky="w")
        self.t_ply_var = tk.DoubleVar(value=0.125)
        ttk.Entry(top, textvariable=self.t_ply_var, width=8)\
            .grid(row=0, column=3, sticky="we")

        # Material
        ttk.Label(top, text="Material").grid(row=0, column=4, sticky="w")
        self.mat_var = tk.StringVar(value="M40J")
        ttk.Combobox(top, textvariable=self.mat_var,
                     values=list(MATERIALS.keys()), width=10)\
            .grid(row=0, column=5, sticky="we")

        # Geometrie
        ttk.Label(top, text="Ø unten [mm]").grid(row=1, column=0, sticky="w")
        self.d_bot_var = tk.DoubleVar(value=200)
        ttk.Entry(top, textvariable=self.d_bot_var, width=8)\
            .grid(row=1, column=1, sticky="we")

        ttk.Label(top, text="Ø oben [mm]").grid(row=1, column=2, sticky="w")
        self.d_top_var = tk.DoubleVar(value=200)
        ttk.Entry(top, textvariable=self.d_top_var, width=8)\
            .grid(row=1, column=3, sticky="we")

        ttk.Label(top, text="Höhe [mm]").grid(row=1, column=4, sticky="w")
        self.h_var = tk.DoubleVar(value=500)
        ttk.Entry(top, textvariable=self.h_var, width=8)\
            .grid(row=1, column=5, sticky="we")

        # Prozess (Geschwindigkeit)
        ttk.Label(top, text="Prozess").grid(row=2, column=0, sticky="w")
        self.proc_var = tk.StringVar(value="Towpreg")
        ttk.Combobox(top, textvariable=self.proc_var,
                     values=list(PROCESSES.keys()), width=10)\
            .grid(row=2, column=1, sticky="we")

        # Buttons
        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=3, column=0, columnspan=6, pady=5, sticky="w")
        ttk.Button(btn_frame, text="Sequenz parsen", command=self.on_parse)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Berechnen", command=self.on_calc)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Layup speichern", command=self.on_save)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Autoklav-Profil", command=self.on_plot)\
            .pack(side=tk.LEFT, padx=2)

        # Tabelle
        self.tree = ttk.Treeview(self, columns=("winkel", "dicke", "material"), show="headings")
        self.tree.heading("winkel", text="Winkel [°]")
        self.tree.heading("dicke", text="Dicke [mm]")
        self.tree.heading("material", text="Material")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Summenzeile + Plot
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.sum_lbl = ttk.Label(bottom, text="Summen: –")
        self.sum_lbl.pack(side=tk.LEFT)

        self.fig = Figure(figsize=(4, 3))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=bottom)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.layup = Layup(name="Demo")

    def on_parse(self):
        try:
            t = self.t_ply_var.get() / 1000.0  # mm → m
            material = MATERIALS[self.mat_var.get()]
            layers = parser.parse_sequence(self.seq_var.get(), t, material)
            self.layup.layers = layers

            for i in self.tree.get_children():
                self.tree.delete(i)
            for l in layers:
                self.tree.insert("", "end",
                                 values=(f"{l.angle:.1f}", f"{l.thickness*1000:.3f}", l.material.name))
        except Exception as e:
            messagebox.showerror("Fehler beim Parsen", str(e))

    def _geometry_from_inputs(self):
        return Geometry(
            d_bottom=self.d_bot_var.get()/1000.0,
            d_top=self.d_top_var.get()/1000.0,
            height=self.h_var.get()/1000.0,
            winding_angle=45.0,  # TODO Eingabefeld
            tow_width=0.005,     # TODO Eingabefeld
            tow_count=8,
            overlap=0.1,
        )

    def on_calc(self):
        try:
            self.layup.geometry = self._geometry_from_inputs()
            self.layup.process = PROCESSES[self.proc_var.get()]
            summary = geometry.layup_summary(self.layup)
            txt = (f"Umfang: {summary['umfang_m']:.3f} m | "
                   f"Pfadlänge: {summary['pfadlaenge_m']:.3f} m | "
                   f"Durchläufe: {summary['durchlaeufe']:.1f} | "
                   f"Zeit: {summary['zeit_s']/60:.1f} min | "
                   f"Masse: {summary['masse_kg']:.2f} kg")
            self.sum_lbl.config(text=txt)
        except Exception as e:
            messagebox.showerror("Fehler bei Berechnung", str(e))

    def on_save(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        layup_io.save_layup_json(self.layup, path)
        messagebox.showinfo("Gespeichert", f"Layup gespeichert unter:\n{path}")

    def on_plot(self):
        self.ax.clear()
        autoclave.plot_autoclave_profile(show=False, ax=self.ax)
        self.canvas.draw()

if __name__ == "__main__":
    app = FWApp()
    app.mainloop()
