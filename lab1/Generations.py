import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
from PIL import Image, ImageTk



PRESET_RULES = {
    "Іскри":    "2/2/25",
    "Комахи":   "23/2/8",
    "Полум'я":  "235678/3468/9",
}

GRID_SIZE = 200
DISPLAY_SIZE = 640
DEFAULT_RULE = "23/2/8"



class GenerationsAutomaton:
    def __init__(self, height: int, width: int, rule_str: str = DEFAULT_RULE):
        self.height = height
        self.width = width
        self.grid = np.zeros((height, width), dtype=np.int32)
        self.initial_grid = self.grid.copy()
        self.iteration = 0
        self.set_rule(rule_str)

    @staticmethod
    def parse_rule(rule_str: str):
        rule_str = rule_str.strip()
        parts = rule_str.split("/")
        if len(parts) != 3:
            raise ValueError("Правило має бути у форматі S/B/C, наприклад 23/2/8")
        s_part, b_part, c_part = (p.strip() for p in parts)
        if not c_part.isdigit():
            raise ValueError("C має бути цілим невід'ємним числом")
        S = set(int(ch) for ch in s_part if ch.isdigit())
        B = set(int(ch) for ch in b_part if ch.isdigit())
        C = int(c_part)
        if C < 2:
            raise ValueError("C має бути не менше 2 (мінімум: живий/мертвий стан)")
        for v in S | B:
            if not (0 <= v <= 8):
                raise ValueError("Цифри у S та B мають бути в діапазоні 0-8")
        return S, B, C

    def set_rule(self, rule_str: str):
        S, B, C = self.parse_rule(rule_str)
        self.S, self.B, self.C = S, B, C
        self.rule_str = rule_str
        self.grid = np.clip(self.grid, 0, C - 1)
        self.initial_grid = np.clip(self.initial_grid, 0, C - 1)

    @staticmethod
    def _count_alive_neighbors(alive: np.ndarray) -> np.ndarray:
        h, w = alive.shape
        padded = np.pad(alive.astype(np.int16), 1, mode="constant")
        total = (
            padded[0:h, 0:w] + padded[0:h, 1:w + 1] + padded[0:h, 2:w + 2]
            + padded[1:h + 1, 0:w] + padded[1:h + 1, 2:w + 2]
            + padded[2:h + 2, 0:w] + padded[2:h + 2, 1:w + 1] + padded[2:h + 2, 2:w + 2]
        )
        return total

    def step(self):
        grid = self.grid
        S, B, C = self.S, self.B, self.C

        alive_mask = grid == 1
        dead_mask = grid == 0
        dying_mask = grid >= 2

        neighbor_count = self._count_alive_neighbors(alive_mask)

        new_grid = np.zeros_like(grid)

        born_mask = dead_mask & np.isin(neighbor_count, list(B)) if B else np.zeros_like(dead_mask)
        new_grid[born_mask] = 1

        survive_mask = alive_mask & (np.isin(neighbor_count, list(S)) if S else np.zeros_like(alive_mask))
        new_grid[survive_mask] = 1
        start_dying_mask = alive_mask & ~survive_mask
        if C <= 2:
            new_grid[start_dying_mask] = 0
        else:
            new_grid[start_dying_mask] = 2

        next_state = grid + 1
        disappear_mask = dying_mask & (next_state >= C)
        continue_dying_mask = dying_mask & ~disappear_mask
        new_grid[continue_dying_mask] = next_state[continue_dying_mask]
        new_grid[disappear_mask] = 0

        self.grid = new_grid
        self.iteration += 1
    
    def clear(self):
        self.grid = np.zeros((self.height, self.width), dtype=np.int32)
        self.iteration = 0
        self.initial_grid = self.grid.copy()

    def randomize(self, density: float = 0.2):
        self.grid = (np.random.random((self.height, self.width)) < density).astype(np.int32)
        self.iteration = 0
        self.initial_grid = self.grid.copy()

    def center_cross(self, arm_len: int = 20):
        self.grid = np.zeros((self.height, self.width), dtype=np.int32)
        cy, cx = self.height // 2, self.width // 2
        y0, y1 = max(0, cy - arm_len), min(self.height, cy + arm_len + 1)
        x0, x1 = max(0, cx - arm_len), min(self.width, cx + arm_len + 1)
        self.grid[y0:y1, cx] = 1
        self.grid[cy, x0:x1] = 1
        self.iteration = 0
        self.initial_grid = self.grid.copy()

    def reset_to_start(self):
        self.grid = self.initial_grid.copy()
        self.iteration = 0

    def snapshot_as_initial(self):
        self.initial_grid = self.grid.copy()
        self.iteration = 0

    def set_cell_block(self, cy: int, cx: int, size: int, value: int):
        half = size // 2
        y0, y1 = max(0, cy - half), min(self.height, cy + half + 1)
        x0, x1 = max(0, cx - half), min(self.width, cx + half + 1)
        self.grid[y0:y1, x0:x1] = value

    def build_palette(self) -> np.ndarray:
        palette = np.zeros((self.C, 3), dtype=np.uint8)
        palette[0] = (10, 10, 15)
        if self.C > 1:
            palette[1] = (255, 255, 255)
        for s in range(2, self.C):
            t = (s - 1) / max(self.C - 1, 1)
            r = int(255 * (1 - t) + 40 * t)
            g = int(140 * (1 - t) + 10 * t)
            b = int(20 * (1 - t) + 15 * t)
            palette[s] = (r, g, b)
        return palette

    def render_rgb_array(self) -> np.ndarray:
        palette = self.build_palette()
        return palette[self.grid]



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Клітинний автомат "Покоління"')
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)

        self.automaton = GenerationsAutomaton(GRID_SIZE, GRID_SIZE, DEFAULT_RULE)
        self.automaton.center_cross()

        self.running = False
        self.brush_size = 1
        self.speed = tk.IntVar(value=8)

        self._build_ui()
        self._render()

    def _build_ui(self):
        main = tk.Frame(self, bg="#1e1e1e")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = tk.Frame(main, bg="#1e1e1e")
        left.pack(side="left", padx=(0, 10))

        self.canvas = tk.Canvas(
            left, width=DISPLAY_SIZE, height=DISPLAY_SIZE,
            bg="black", highlightthickness=1, highlightbackground="#444"
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", lambda e: self._paint(e, 1))
        self.canvas.bind("<B1-Motion>", lambda e: self._paint(e, 1))
        self.canvas.bind("<Button-3>", lambda e: self._paint(e, 0))
        self.canvas.bind("<B3-Motion>", lambda e: self._paint(e, 0))

        right = tk.Frame(main, bg="#1e1e1e", width=330)
        right.pack(side="left", fill="y")

        style_title = {"bg": "#1e1e1e", "fg": "white", "font": ("Segoe UI", 16, "bold")}
        style_label = {"bg": "#1e1e1e", "fg": "#cccccc", "font": ("Segoe UI", 9)}
        style_group = {"bg": "#1e1e1e", "fg": "white", "font": ("Segoe UI", 10, "bold")}

        tk.Label(right, text="Покоління", **style_title).pack(anchor="w")
        tk.Label(right, text=f"{GRID_SIZE} × {GRID_SIZE} клітин", **style_label).pack(anchor="w")
        tk.Label(right, text="Околиця Мура: 8 сусідів", **style_label).pack(anchor="w", pady=(0, 8))

        rule_frame = tk.LabelFrame(right, text="Правило (S/B/C)", bg="#1e1e1e", fg="white",
                                    font=("Segoe UI", 10, "bold"))
        rule_frame.pack(fill="x", pady=(0, 10))

        row = tk.Frame(rule_frame, bg="#1e1e1e")
        row.pack(fill="x", padx=6, pady=6)
        tk.Label(row, text="Правило:", **style_label).pack(side="left")
        self.rule_entry = tk.Entry(row, width=16)
        self.rule_entry.insert(0, DEFAULT_RULE)
        self.rule_entry.pack(side="left", padx=6)
        tk.Button(row, text="Застосувати", command=self._apply_rule_from_entry).pack(side="left")

        preset_row = tk.Frame(rule_frame, bg="#1e1e1e")
        preset_row.pack(fill="x", padx=6, pady=(0, 6))
        for name, rule in PRESET_RULES.items():
            tk.Button(
                preset_row, text=f"{name} ({rule})",
                command=lambda r=rule: self._apply_rule(r)
            ).pack(side="left", padx=2, expand=True, fill="x")

        self.rule_info_label = tk.Label(rule_frame, text="", **style_label, justify="left")
        self.rule_info_label.pack(anchor="w", padx=6, pady=(0, 6))

        init_frame = tk.LabelFrame(right, text="Початковий стан", bg="#1e1e1e", fg="white",
                                    font=("Segoe UI", 10, "bold"))
        init_frame.pack(fill="x", pady=(0, 10))
        tk.Label(init_frame, text="ЛКМ — додати клітинки\nПКМ — стерти клітинки",
                 **style_label, justify="left").pack(anchor="w", padx=6, pady=(6, 0))

        brush_row = tk.Frame(init_frame, bg="#1e1e1e")
        brush_row.pack(fill="x", padx=6, pady=6)
        tk.Label(brush_row, text="Пензель:", **style_label).pack(side="left")
        self.brush_buttons = {}
        for size in (1, 3, 5):
            b = tk.Button(brush_row, text=f"{size}×{size}", width=4,
                          command=lambda s=size: self._set_brush(s))
            b.pack(side="left", padx=2)
            self.brush_buttons[size] = b
        self._set_brush(1)

        tk.Button(init_frame, text="Очистити", command=self._on_clear).pack(fill="x", padx=6, pady=2)
        tk.Button(init_frame, text="Центральний хрест", command=self._on_cross).pack(fill="x", padx=6, pady=2)
        tk.Button(init_frame, text="Випадкове поле", command=self._on_random).pack(fill="x", padx=6, pady=(2, 6))
        
        evo_frame = tk.LabelFrame(right, text="Еволюція", bg="#1e1e1e", fg="white",
                                   font=("Segoe UI", 10, "bold"))
        evo_frame.pack(fill="x", pady=(0, 10))

        self.status_label = tk.Label(evo_frame, text="", **style_label)
        self.status_label.pack(anchor="w", padx=6, pady=(6, 0))

        btn_row = tk.Frame(evo_frame, bg="#1e1e1e")
        btn_row.pack(fill="x", padx=6, pady=6)
        self.start_btn = tk.Button(btn_row, text="▶ Старт", command=self._toggle_run)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(btn_row, text="Крок", command=self._on_step).pack(side="left", expand=True, fill="x", padx=2)

        tk.Button(evo_frame, text="Скинути до 0", command=self._on_reset).pack(fill="x", padx=6, pady=(0, 6))

        speed_row = tk.Frame(evo_frame, bg="#1e1e1e")
        speed_row.pack(fill="x", padx=6, pady=(0, 6))
        self.speed_label = tk.Label(speed_row, text="", **style_label)
        self.speed_label.pack(anchor="w")
        tk.Scale(evo_frame, from_=1, to=30, orient="horizontal", variable=self.speed,
                 bg="#1e1e1e", fg="white", troughcolor="#444", highlightthickness=0,
                 command=lambda _v: self._update_speed_label()).pack(fill="x", padx=6, pady=(0, 6))
        self._update_speed_label()

        export_frame = tk.LabelFrame(right, text="Експорт", bg="#1e1e1e", fg="white",
                                      font=("Segoe UI", 10, "bold"))
        export_frame.pack(fill="x", pady=(0, 10))
        tk.Button(export_frame, text="Зберегти поточну ітерацію у .BMP",
                  command=self._on_save_bmp).pack(fill="x", padx=6, pady=6)
        tk.Label(export_frame,
                 text=f"Зберігається стан поточної ітерації\nу розмірі {GRID_SIZE}×{GRID_SIZE} пікселів.",
                 **style_label, justify="left").pack(anchor="w", padx=6, pady=(0, 6))

        tk.Label(right, text="Гарячі клавіші:\nSpace — старт/стоп\n→ — наступна ітерація",
                 **style_label, justify="left").pack(anchor="w", pady=(4, 0))

        self.bind("<space>", lambda e: self._toggle_run())
        self.bind("<Right>", lambda e: self._on_step())

        self._update_status()

    def _set_brush(self, size):
        self.brush_size = size
        for s, btn in self.brush_buttons.items():
            btn.config(relief="sunken" if s == size else "raised")

    def _update_speed_label(self):
        self.speed_label.config(text=f"Швидкість: {self.speed.get()} ітерацій/сек")

    def _update_status(self):
        self.status_label.config(
            text=f"Ітерація: {self.automaton.iteration}    Правило: {self.automaton.rule_str}"
        )
        S = ",".join(str(x) for x in sorted(self.automaton.S)) or "-"
        B = ",".join(str(x) for x in sorted(self.automaton.B)) or "-"
        self.rule_info_label.config(
            text=f"S={{{S}}}  B={{{B}}}  C={self.automaton.C}  (всього станів: {self.automaton.C})"
        )

    def _canvas_to_grid(self, event):
        scale = GRID_SIZE / DISPLAY_SIZE
        gx = int(event.x * scale)
        gy = int(event.y * scale)
        gx = max(0, min(GRID_SIZE - 1, gx))
        gy = max(0, min(GRID_SIZE - 1, gy))
        return gy, gx

    def _paint(self, event, value):
        gy, gx = self._canvas_to_grid(event)
        self.automaton.set_cell_block(gy, gx, self.brush_size, value)
        if self.automaton.iteration == 0:
            self.automaton.initial_grid = self.automaton.grid.copy()
        self._render()

    def _apply_rule(self, rule_str):
        try:
            self.automaton.set_rule(rule_str)
        except ValueError as e:
            messagebox.showerror("Помилка правила", str(e))
            return
        self.rule_entry.delete(0, tk.END)
        self.rule_entry.insert(0, rule_str)
        self._update_status()
        self._render()

    def _apply_rule_from_entry(self):
        self._apply_rule(self.rule_entry.get())

    def _on_clear(self):
        self.automaton.clear()
        self._update_status()
        self._render()

    def _on_cross(self):
        self.automaton.center_cross()
        self._update_status()
        self._render()

    def _on_random(self):
        self.automaton.randomize()
        self._update_status()
        self._render()

    def _on_step(self):
        self.automaton.step()
        self._update_status()
        self._render()

    def _on_reset(self):
        self.automaton.reset_to_start()
        self._update_status()
        self._render()

    def _toggle_run(self):
        self.running = not self.running
        self.start_btn.config(text="■ Стоп" if self.running else "▶ Старт")
        if self.running:
            self._tick()

    def _tick(self):
        if not self.running:
            return
        self.automaton.step()
        self._update_status()
        self._render()
        delay_ms = max(1, int(1000 / max(1, self.speed.get())))
        self.after(delay_ms, self._tick)

    def _on_save_bmp(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".bmp",
            filetypes=[("Bitmap image", "*.bmp")],
            initialfile=f"generations_iter_{self.automaton.iteration}.bmp",
            title="Зберегти поточну ітерацію"
        )
        if not path:
            return
        rgb = self.automaton.render_rgb_array()
        img = Image.fromarray(rgb.astype("uint8"), mode="RGB")
        img.save(path, format="BMP")
        messagebox.showinfo("Збережено", f"Ітерацію {self.automaton.iteration} збережено у:\n{path}")

    def _render(self):
        rgb = self.automaton.render_rgb_array()
        img = Image.fromarray(rgb.astype("uint8"), mode="RGB")
        img = img.resize((DISPLAY_SIZE, DISPLAY_SIZE), resample=Image.NEAREST)
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self._tk_img)


if __name__ == "__main__":
    app = App()
    app.mainloop()