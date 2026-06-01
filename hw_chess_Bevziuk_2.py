import re
import tkinter as tk
from tkinter import ttk, messagebox


# ──────────────────────────────────────────────────────────────────────────────
#  Вкладка 1: Шахові фігури (тура / слон / ферзь)
# ──────────────────────────────────────────────────────────────────────────────
class ChessTab:
    """Вкладка для розміщення та видалення шахових фігур (тура, слон, ферзь)."""

    BOARD_SIZE = 8
    CELL_SIZE = 62
    BOARD_PIXELS = BOARD_SIZE * CELL_SIZE

    LIGHT_SQUARE = "#F0D9B5"
    DARK_SQUARE = "#B58863"
    ATTACKED_SQUARE = "#F6B3B3"
    OCCUPIED_SQUARE = "#7FA8D6"
    OCCUPIED_ATTACKED = "#6E9FD1"
    BORDER_COLOR = "#000000"
    TEXT_COLOR = "#1f1f1f"

    PIECE_NAMES = {"queen": "Ферзь", "rook": "Тура", "bishop": "Слон"}
    PIECE_SYMBOLS = {"queen": "♕", "rook": "♖", "bishop": "♗"}

    def __init__(self, parent_notebook: ttk.Notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="♟  Шахові фігури")

        self.current_piece = tk.StringVar(value="queen")
        self.show_hints = tk.BooleanVar(value=False)
        self.place_input = tk.StringVar()
        self.remove_input = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Оберіть фігуру, введіть клітинку та натисніть «Поставити» або «Видалити»."
        )
        self.history_no = 0
        self.placed = {"queen": [], "rook": [], "bishop": []}

        self._build_ui()
        self.draw_board()

    def _build_ui(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        piece_box = ttk.LabelFrame(left, text="Вибір фігури", padding=8)
        piece_box.pack(fill="x")
        self.piece_buttons = {}
        for key in ("queen", "bishop", "rook"):
            btn = tk.Button(
                piece_box,
                text=self.PIECE_NAMES[key],
                width=14,
                relief="raised",
                bd=2,
                command=lambda p=key: self.set_piece(p),
            )
            btn.pack(side="left", padx=4, pady=2)
            self.piece_buttons[key] = btn

        place_box = ttk.LabelFrame(left, text="Поставити фігуру", padding=8)
        place_box.pack(fill="x", pady=(10, 0))
        place_row = ttk.Frame(place_box)
        place_row.pack(fill="x")
        ttk.Label(place_row, text="Клітинка (a1-h8):").pack(side="left")
        e1 = ttk.Entry(place_row, textvariable=self.place_input, width=10)
        e1.pack(side="left", padx=6)
        e1.bind("<Return>", lambda _: self.check_and_place())
        ttk.Button(place_row, text="⬆  Поставити", command=self.check_and_place).pack(side="left")

        remove_box = ttk.LabelFrame(left, text="Видалити фігуру", padding=8)
        remove_box.pack(fill="x", pady=(8, 0))
        remove_row = ttk.Frame(remove_box)
        remove_row.pack(fill="x")
        ttk.Label(remove_row, text="Клітинка (a1-h8):").pack(side="left")
        e2 = ttk.Entry(remove_row, textvariable=self.remove_input, width=10)
        e2.pack(side="left", padx=6)
        e2.bind("<Return>", lambda _: self.remove_piece())
        ttk.Button(remove_row, text="⬇  Видалити", command=self.remove_piece).pack(side="left")

        ttk.Label(left, textvariable=self.status_var,
                  foreground="#1f4e79", wraplength=340).pack(fill="x", pady=(10, 0))

        history_box = ttk.LabelFrame(left, text="Історія запитів", padding=8)
        history_box.pack(fill="both", expand=True, pady=(10, 0))
        columns = ("no", "cell", "action", "result")
        self.tree = ttk.Treeview(history_box, columns=columns, show="headings", height=12)
        self.tree.heading("no", text="№")
        self.tree.heading("cell", text="Клітинка")
        self.tree.heading("action", text="Дія")
        self.tree.heading("result", text="Результат")
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("cell", width=80, anchor="center")
        self.tree.column("action", width=80, anchor="center")
        self.tree.column("result", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y")
        board_frame = ttk.LabelFrame(right, text="Шахова дошка", padding=8)
        board_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            board_frame,
            width=self.BOARD_PIXELS, height=self.BOARD_PIXELS,
            highlightthickness=1, highlightbackground="#8a8a8a", bg="#fff",
        )
        self.canvas.pack()
        hint_row = ttk.Frame(board_frame)
        hint_row.pack(fill="x", pady=(8, 0))
        ttk.Checkbutton(
            hint_row, text="Показувати атаковані клітинки",
            variable=self.show_hints, command=self.draw_board,
        ).pack(anchor="w")

        self._refresh_piece_buttons()

    def set_piece(self, piece: str):
        self.current_piece.set(piece)
        self._clear_state()
        self._refresh_piece_buttons()
        self.status_var.set(f"Обрано фігуру: {self.PIECE_NAMES[piece]}. Стан очищено.")
        self.draw_board()

    def _clear_state(self):
        self.place_input.set("")
        self.remove_input.set("")
        self.history_no = 0
        for key in self.placed:
            self.placed[key].clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _refresh_piece_buttons(self):
        for key, btn in self.piece_buttons.items():
            if self.current_piece.get() == key:
                btn.configure(relief="sunken", bg="#dbeafe")
            else:
                btn.configure(relief="raised", bg="#f0f0f0")

    def parse_cell(self, text: str):
        n = text.strip().lower()
        if not re.fullmatch(r"[a-h][1-8]", n):
            return None
        col = ord(n[0]) - ord("a")
        row = int(n[1]) - 1
        return col, row, n

    def occupied_all(self):
        return {(c, r) for positions in self.placed.values() for (c, r) in positions}

    def can_place_rook(self, pos):
        col, row = pos
        for oc, orow in self.placed["rook"]:
            if oc == col or orow == row:
                return False, f"Тура на {chr(oc + ord('a'))}{orow + 1} вже б'є цю клітинку."
        return True, ""

    def can_place_bishop(self, pos):
        col, row = pos
        for oc, orow in self.placed["bishop"]:
            if abs(oc - col) == abs(orow - row):
                return False, f"Слон на {chr(oc + ord('a'))}{orow + 1} вже б'є цю клітинку."
        return True, ""

    def can_place_queen(self, pos):
        col, row = pos
        for oc, orow in self.placed["queen"]:
            if oc == col or orow == row or abs(oc - col) == abs(orow - row):
                return False, f"Ферзь на {chr(oc + ord('a'))}{orow + 1} вже б'є цю клітинку."
        return True, ""

    def can_place(self, piece: str, pos):
        if pos in self.occupied_all():
            return False, "Ця клітинка вже зайнята іншою фігурою."
        if piece == "rook":   return self.can_place_rook(pos)
        if piece == "bishop": return self.can_place_bishop(pos)
        if piece == "queen":  return self.can_place_queen(pos)
        return False, "Невідома фігура."

    def check_and_place(self):
        parsed = self.parse_cell(self.place_input.get())
        if not parsed:
            messagebox.showerror("Некоректний ввід", "Введіть клітинку у форматі a1–h8.")
            return
        col, row, cell_name = parsed
        piece = self.current_piece.get()
        ok, reason = self.can_place(piece, (col, row))
        self.history_no += 1
        self.tree.insert("", "end",
                         values=(self.history_no, cell_name, "Поставити", "✅ Вдалось" if ok else "❌ Не вдалось"))
        if ok:
            self.placed[piece].append((col, row))
            self.place_input.set("")
            self.status_var.set(f"{self.PIECE_NAMES[piece]} розміщено на {cell_name}.")
        else:
            self.status_var.set(f"Не можна поставити на {cell_name}. {reason}")
        self.draw_board()

    def remove_piece(self):
        parsed = self.parse_cell(self.remove_input.get())
        if not parsed:
            messagebox.showerror("Некоректний ввід", "Введіть клітинку у форматі a1–h8.")
            return
        col, row, cell_name = parsed
        piece = self.current_piece.get()

        if (col, row) in self.placed[piece]:
            self.placed[piece].remove((col, row))
            self.remove_input.set("")
            self.history_no += 1
            self.tree.insert("", "end",
                             values=(self.history_no, cell_name, "Видалити", "✅ Видалено"))
            self.status_var.set(f"{self.PIECE_NAMES[piece]} видалено з {cell_name}.")
        else:
            other = next((p for p, lst in self.placed.items() if (col, row) in lst), None)
            self.history_no += 1
            self.tree.insert("", "end",
                             values=(self.history_no, cell_name, "Видалити", "❌ Не знайдено"))
            if other:
                self.status_var.set(
                    f"На {cell_name} стоїть {self.PIECE_NAMES[other]}, а не {self.PIECE_NAMES[piece]}."
                )
            else:
                self.status_var.set(f"На клітинці {cell_name} немає {self.PIECE_NAMES[piece]}.")
        self.draw_board()

    def attacked_by_piece(self, piece: str, pos):
        col, row = pos
        attacked = set()
        if piece == "rook":
            for i in range(self.BOARD_SIZE):
                if i != col: attacked.add((i, row))
                if i != row: attacked.add((col, i))
        elif piece == "bishop":
            for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                x, y = col + dc, row + dr
                while 0 <= x < self.BOARD_SIZE and 0 <= y < self.BOARD_SIZE:
                    attacked.add((x, y))
                    x += dc
                    y += dr
        elif piece == "queen":
            attacked |= self.attacked_by_piece("rook", pos)
            attacked |= self.attacked_by_piece("bishop", pos)
        return attacked

    def all_attacked_cells(self):
        cells = set()
        for piece, positions in self.placed.items():
            for pos in positions:
                cells |= self.attacked_by_piece(piece, pos)
        return cells

    def cell_to_canvas(self, col, row):
        x1 = col * self.CELL_SIZE
        y1 = (7 - row) * self.CELL_SIZE
        return x1, y1, x1 + self.CELL_SIZE, y1 + self.CELL_SIZE

    def board_color(self, col, row):
        return "#F0D9B5" if (col + row) % 2 == 0 else "#B58863"

    def draw_board(self):
        self.canvas.delete("all")
        highlight = self.all_attacked_cells() if self.show_hints.get() else set()
        occupied = self.occupied_all()

        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                x1, y1, x2, y2 = self.cell_to_canvas(col, row)
                pos = (col, row)
                color = self.board_color(col, row)
                if pos in highlight:
                    color = self.ATTACKED_SQUARE
                if pos in occupied:
                    color = self.OCCUPIED_ATTACKED if pos in highlight else self.OCCUPIED_SQUARE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=self.BORDER_COLOR, width=1)

        for col in range(self.BOARD_SIZE):
            self.canvas.create_text(
                col * self.CELL_SIZE + self.CELL_SIZE / 2, self.BOARD_PIXELS - 9,
                text=chr(ord("a") + col), fill=self.TEXT_COLOR, font=("Arial", 10, "bold"))
        for row in range(self.BOARD_SIZE):
            self.canvas.create_text(
                10, (7 - row) * self.CELL_SIZE + self.CELL_SIZE / 2,
                text=str(row + 1), fill=self.TEXT_COLOR, font=("Arial", 10, "bold"), anchor="w")

        for piece, positions in self.placed.items():
            for col, row in positions:
                x1, y1, x2, y2 = self.cell_to_canvas(col, row)
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=self.PIECE_SYMBOLS[piece], fill="#111111", font=("Arial", 30, "bold"))


# ──────────────────────────────────────────────────────────────────────────────
#  Вкладка 2: Шашки
# ──────────────────────────────────────────────────────────────────────────────
class CheckersTab:
    """Вкладка для розміщення та видалення шашок (шашка / дамка)."""

    BOARD_SIZE = 8
    CELL_SIZE = 62
    BOARD_PIXELS = BOARD_SIZE * CELL_SIZE

    LIGHT_SQUARE = "#F0D9B5"
    DARK_SQUARE = "#B58863"
    ATTACKED_SQUARE = "#F6B3B3"
    OCCUPIED_SQUARE = "#7FA8D6"
    OCCUPIED_ATTACKED = "#6E9FD1"
    BORDER_COLOR = "#000000"
    TEXT_COLOR = "#1f1f1f"

    PIECE_NAMES = {"checker": "Шашка", "king": "Дамка"}

    def __init__(self, parent_notebook: ttk.Notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="🔴  Шашки")

        self.current_piece = tk.StringVar(value="checker")
        self.show_hints = tk.BooleanVar(value=False)
        self.place_input = tk.StringVar()
        self.remove_input = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Оберіть тип шашки, введіть клітинку та натисніть «Поставити» або «Видалити»."
        )
        self.history_no = 0
        self.placed = {"checker": [], "king": []}

        self._build_ui()
        self.draw_board()

    def _build_ui(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        piece_box = ttk.LabelFrame(left, text="Тип шашки", padding=8)
        piece_box.pack(fill="x")
        self.piece_buttons = {}
        for key in ("checker", "king"):
            btn = tk.Button(
                piece_box,
                text=self.PIECE_NAMES[key],
                width=14,
                relief="raised",
                bd=2,
                command=lambda p=key: self.set_piece(p),
            )
            btn.pack(side="left", padx=4, pady=2)
            self.piece_buttons[key] = btn

        place_box = ttk.LabelFrame(left, text="Поставити шашку", padding=8)
        place_box.pack(fill="x", pady=(10, 0))
        place_row = ttk.Frame(place_box)
        place_row.pack(fill="x")
        ttk.Label(place_row, text="Клітинка (a1-h8):").pack(side="left")
        e1 = ttk.Entry(place_row, textvariable=self.place_input, width=10)
        e1.pack(side="left", padx=6)
        e1.bind("<Return>", lambda _: self.check_and_place())
        ttk.Button(place_row, text="⬆  Поставити", command=self.check_and_place).pack(side="left")

        remove_box = ttk.LabelFrame(left, text="Видалити шашку", padding=8)
        remove_box.pack(fill="x", pady=(8, 0))
        remove_row = ttk.Frame(remove_box)
        remove_row.pack(fill="x")
        ttk.Label(remove_row, text="Клітинка (a1-h8):").pack(side="left")
        e2 = ttk.Entry(remove_row, textvariable=self.remove_input, width=10)
        e2.pack(side="left", padx=6)
        e2.bind("<Return>", lambda _: self.remove_piece())
        ttk.Button(remove_row, text="⬇  Видалити", command=self.remove_piece).pack(side="left")

        ttk.Label(left, textvariable=self.status_var,
                  foreground="#1f4e79", wraplength=340).pack(fill="x", pady=(10, 0))

        rules_box = ttk.LabelFrame(left, text="Правила атаки", padding=8)
        rules_box.pack(fill="x", pady=(8, 0))
        rules_text = (
            "Шашка: може побити суперника, якщо за ним є порожня клітинка.\n"
            "Дамка: б'є на будь-яку відстань, але за суперником має бути порожня клітинка."
        )
        ttk.Label(rules_box, text=rules_text, wraplength=330, justify="left").pack(anchor="w")

        history_box = ttk.LabelFrame(left, text="Історія запитів", padding=8)
        history_box.pack(fill="both", expand=True, pady=(10, 0))
        columns = ("no", "cell", "action", "result")
        self.tree = ttk.Treeview(history_box, columns=columns, show="headings", height=12)
        self.tree.heading("no", text="№")
        self.tree.heading("cell", text="Клітинка")
        self.tree.heading("action", text="Дія")
        self.tree.heading("result", text="Результат")
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("cell", width=80, anchor="center")
        self.tree.column("action", width=80, anchor="center")
        self.tree.column("result", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y")
        board_frame = ttk.LabelFrame(right, text="Шахова дошка", padding=8)
        board_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            board_frame,
            width=self.BOARD_PIXELS, height=self.BOARD_PIXELS,
            highlightthickness=1, highlightbackground="#8a8a8a", bg="#fff",
        )
        self.canvas.pack()
        hint_row = ttk.Frame(board_frame)
        hint_row.pack(fill="x", pady=(8, 0))
        ttk.Checkbutton(
            hint_row, text="Показувати атаковані клітинки",
            variable=self.show_hints, command=self.draw_board,
        ).pack(anchor="w")

        self._refresh_piece_buttons()

    def set_piece(self, piece: str):
        self.current_piece.set(piece)
        self._clear_state()
        self._refresh_piece_buttons()
        self.status_var.set(f"Обрано: {self.PIECE_NAMES[piece]}. Стан очищено.")
        self.draw_board()

    def _clear_state(self):
        self.place_input.set("")
        self.remove_input.set("")
        self.history_no = 0
        for key in self.placed:
            self.placed[key].clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _refresh_piece_buttons(self):
        for key, btn in self.piece_buttons.items():
            if self.current_piece.get() == key:
                btn.configure(relief="sunken", bg="#dbeafe")
            else:
                btn.configure(relief="raised", bg="#f0f0f0")

    def parse_cell(self, text: str):
        n = text.strip().lower()
        if not re.fullmatch(r"[a-h][1-8]", n):
            return None
        col = ord(n[0]) - ord("a")
        row = int(n[1]) - 1
        return col, row, n

    def occupied_all(self):
        return {(c, r) for positions in self.placed.values() for (c, r) in positions}

    def _can_capture(self, attacker_piece: str, attacker_pos, target_pos):
        ac, ar = attacker_pos
        tc, tr = target_pos

        dc = tc - ac
        dr = tr - ar
        if abs(dc) != abs(dr) or dc == 0:
            return False

        step_c = 1 if dc > 0 else -1
        step_r = 1 if dr > 0 else -1

        landing_c = tc + step_c
        landing_r = tr + step_r

        if not (0 <= landing_c < self.BOARD_SIZE and 0 <= landing_r < self.BOARD_SIZE):
            return False

        if (landing_c, landing_r) in self.occupied_all():
            return False

        if attacker_piece == "king":
            cur_c, cur_r = ac + step_c, ar + step_r
            while (cur_c, cur_r) != (tc, tr):
                if (cur_c, cur_r) in self.occupied_all():
                    return False
                cur_c += step_c
                cur_r += step_r

        return True

    def _get_attacked_cells(self, piece: str, pos):
        col, row = pos
        attacked = set()

        if piece == "checker":
            for dc, dr in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                tc, tr = col + dc, row + dr
                if 0 <= tc < self.BOARD_SIZE and 0 <= tr < self.BOARD_SIZE:
                    if self._can_capture(piece, (col, row), (tc, tr)):
                        attacked.add((tc, tr))

        elif piece == "king":
            for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                tc, tr = col + dc, row + dr
                while 0 <= tc < self.BOARD_SIZE and 0 <= tr < self.BOARD_SIZE:
                    if self._can_capture(piece, (col, row), (tc, tr)):
                        attacked.add((tc, tr))
                    if (tc, tr) in self.occupied_all():
                        break
                    tc += dc
                    tr += dr

        return attacked

    def all_attacked_cells(self):
        cells = set()
        for piece, positions in self.placed.items():
            for pos in positions:
                cells |= self._get_attacked_cells(piece, pos)
        return cells

    def can_place(self, piece: str, pos):
        if pos in self.occupied_all():
            return False, "Ця клітинка вже зайнята."

        for p, positions in self.placed.items():
            for opos in positions:
                if pos in self._get_attacked_cells(p, opos):
                    oc, orow = opos
                    cell_name = f"{chr(oc + ord('a'))}{orow + 1}"
                    return False, f"{self.PIECE_NAMES[p]} на {cell_name} може побити цю клітинку."

        return True, ""

    def check_and_place(self):
        parsed = self.parse_cell(self.place_input.get())
        if not parsed:
            messagebox.showerror("Некоректний ввід", "Введіть клітинку у форматі a1–h8.")
            return
        col, row, cell_name = parsed
        piece = self.current_piece.get()
        ok, reason = self.can_place(piece, (col, row))
        self.history_no += 1
        self.tree.insert("", "end",
                         values=(self.history_no, cell_name, "Поставити", "✅ Вдалось" if ok else "❌ Не вдалось"))
        if ok:
            self.placed[piece].append((col, row))
            self.place_input.set("")
            self.status_var.set(f"{self.PIECE_NAMES[piece]} розміщено на {cell_name}.")
        else:
            self.status_var.set(f"Не можна поставити на {cell_name}. {reason}")
        self.draw_board()

    def remove_piece(self):
        parsed = self.parse_cell(self.remove_input.get())
        if not parsed:
            messagebox.showerror("Некоректний ввід", "Введіть клітинку у форматі a1–h8.")
            return
        col, row, cell_name = parsed
        piece = self.current_piece.get()

        if (col, row) in self.placed[piece]:
            self.placed[piece].remove((col, row))
            self.remove_input.set("")
            self.history_no += 1
            self.tree.insert("", "end",
                             values=(self.history_no, cell_name, "Видалити", "✅ Видалено"))
            self.status_var.set(f"{self.PIECE_NAMES[piece]} видалено з {cell_name}.")
        else:
            other = next((p for p, lst in self.placed.items() if (col, row) in lst), None)
            self.history_no += 1
            self.tree.insert("", "end",
                             values=(self.history_no, cell_name, "Видалити", "❌ Не знайдено"))
            if other:
                self.status_var.set(
                    f"На {cell_name} стоїть {self.PIECE_NAMES[other]}, а не {self.PIECE_NAMES[piece]}.")
            else:
                self.status_var.set(f"На клітинці {cell_name} немає {self.PIECE_NAMES[piece]}.")
        self.draw_board()

    def cell_to_canvas(self, col, row):
        x1 = col * self.CELL_SIZE
        y1 = (7 - row) * self.CELL_SIZE
        return x1, y1, x1 + self.CELL_SIZE, y1 + self.CELL_SIZE

    def board_color(self, col, row):
        return self.LIGHT_SQUARE if (col + row) % 2 == 0 else self.DARK_SQUARE

    def draw_board(self):
        self.canvas.delete("all")
        highlight = self.all_attacked_cells() if self.show_hints.get() else set()
        occupied = self.occupied_all()

        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                x1, y1, x2, y2 = self.cell_to_canvas(col, row)
                pos = (col, row)
                color = self.board_color(col, row)
                if pos in highlight:
                    color = self.ATTACKED_SQUARE
                if pos in occupied:
                    color = self.OCCUPIED_ATTACKED if pos in highlight else self.OCCUPIED_SQUARE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=self.BORDER_COLOR, width=1)

        for col in range(self.BOARD_SIZE):
            self.canvas.create_text(
                col * self.CELL_SIZE + self.CELL_SIZE / 2, self.BOARD_PIXELS - 9,
                text=chr(ord("a") + col), fill=self.TEXT_COLOR, font=("Arial", 10, "bold"))
        for row in range(self.BOARD_SIZE):
            self.canvas.create_text(
                10, (7 - row) * self.CELL_SIZE + self.CELL_SIZE / 2,
                text=str(row + 1), fill=self.TEXT_COLOR, font=("Arial", 10, "bold"), anchor="w")

        COLORS = {"checker": ("#cc2222", "#ffffff"), "king": ("#222222", "#ffdd44")}
        LABELS = {"checker": "Ш", "king": "Д"}
        for piece, positions in self.placed.items():
            fill_c, text_c = COLORS[piece]
            for col, row in positions:
                x1, y1, x2, y2 = self.cell_to_canvas(col, row)
                pad = 6
                self.canvas.create_oval(
                    x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                    fill=fill_c, outline="#000", width=2)
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=LABELS[piece], fill=text_c, font=("Arial", 16, "bold"))


# ──────────────────────────────────────────────────────────────────────────────
#  Вкладка 3: Реверсі (Othello / Reversi)
# ──────────────────────────────────────────────────────────────────────────────
class ReversiTab:
    """Вкладка для гри Реверсі - виставлення фішок з перевертанням суперника."""

    BOARD_SIZE = 8
    CELL_SIZE = 62
    BOARD_PIXELS = BOARD_SIZE * CELL_SIZE

    LIGHT_SQUARE = "#2c5a2c"  # Темно-зелений для реверсі
    DARK_SQUARE = "#1a3b1a"
    VALID_MOVE = "#7bc47b"  # Підсвітка можливих ходів
    BORDER_COLOR = "#000000"
    TEXT_COLOR = "#ffffff"

    COLOR_NAMES = {"black": "Чорна", "white": "Біла"}

    def __init__(self, parent_notebook: ttk.Notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="⚫  Реверсі")

        # Стан гри: None - порожньо, "black" - чорна, "white" - біла
        self.board = [[None for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]

        # Початкова розстановка (стандартна для реверсі)
        self.board[3][3] = "white"
        self.board[3][4] = "black"
        self.board[4][3] = "black"
        self.board[4][4] = "white"

        self.current_player = tk.StringVar(value="black")  # Чорні ходять першими
        self.place_input = tk.StringVar()
        self.status_var = tk.StringVar(value="Гра Реверсі. Хід чорних.")

        self.history_no = 0
        self.history = []  # Зберігаємо історію ходів

        self._build_ui()
        self.draw_board()
        self._update_valid_moves_display()

    def _build_ui(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        # Інформація про гравців
        info_box = ttk.LabelFrame(left, text="Інформація", padding=8)
        info_box.pack(fill="x")

        self.black_count_var = tk.StringVar(value="Чорні: 2")
        self.white_count_var = tk.StringVar(value="Білі: 2")

        ttk.Label(info_box, textvariable=self.black_count_var,
                  foreground="#333333", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(info_box, textvariable=self.white_count_var,
                  foreground="#333333", font=("Arial", 12, "bold")).pack(anchor="w")

        ttk.Separator(info_box, orient="horizontal").pack(fill="x", pady=5)

        ttk.Label(info_box, text="Поточний гравець:", font=("Arial", 10)).pack(anchor="w")
        self.current_label = ttk.Label(info_box, text="⚫ Чорні", font=("Arial", 12, "bold"), foreground="black")
        self.current_label.pack(anchor="w", pady=(0, 5))

        # Блок ходу
        move_box = ttk.LabelFrame(left, text="Зробити хід", padding=8)
        move_box.pack(fill="x", pady=(10, 0))

        move_row = ttk.Frame(move_box)
        move_row.pack(fill="x")
        ttk.Label(move_row, text="Клітинка (a1-h8):").pack(side="left")
        e1 = ttk.Entry(move_row, textvariable=self.place_input, width=10)
        e1.pack(side="left", padx=6)
        e1.bind("<Return>", lambda _: self.make_move())

        btn_frame = ttk.Frame(move_box)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="⬆  Зробити хід", command=self.make_move).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🔄  Нова гра", command=self.reset_game).pack(side="left", padx=2)

        # Статус
        ttk.Label(left, textvariable=self.status_var,
                  foreground="#1f4e79", wraplength=340).pack(fill="x", pady=(10, 0))

        # Історія ходів
        history_box = ttk.LabelFrame(left, text="Історія ходів", padding=8)
        history_box.pack(fill="both", expand=True, pady=(10, 0))
        columns = ("no", "cell", "player", "flipped")
        self.tree = ttk.Treeview(history_box, columns=columns, show="headings", height=12)
        self.tree.heading("no", text="№")
        self.tree.heading("cell", text="Клітинка")
        self.tree.heading("player", text="Гравець")
        self.tree.heading("flipped", text="Перевернуто")
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("cell", width=70, anchor="center")
        self.tree.column("player", width=70, anchor="center")
        self.tree.column("flipped", width=150, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Дошка
        right = ttk.Frame(main)
        right.pack(side="right", fill="y")
        board_frame = ttk.LabelFrame(right, text="Дошка Реверсі", padding=8)
        board_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            board_frame,
            width=self.BOARD_PIXELS, height=self.BOARD_PIXELS,
            highlightthickness=1, highlightbackground="#8a8a8a", bg="#fff",
        )
        self.canvas.pack()

        # Прив'язка кліку на дошку
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Легенда
        legend_frame = ttk.Frame(board_frame)
        legend_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(legend_frame, text="●", foreground="black", font=("Arial", 14)).pack(side="left", padx=5)
        ttk.Label(legend_frame, text="Чорні", font=("Arial", 9)).pack(side="left")
        ttk.Label(legend_frame, text="●", foreground="white", font=("Arial", 14)).pack(side="left", padx=(10, 5))
        ttk.Label(legend_frame, text="Білі", font=("Arial", 9)).pack(side="left")
        ttk.Label(legend_frame, text="🟢", foreground="#7bc47b", font=("Arial", 12)).pack(side="left", padx=(10, 5))
        ttk.Label(legend_frame, text="Можливий хід", font=("Arial", 9)).pack(side="left")

    def _update_counts(self):
        """Оновлює лічильники фішок."""
        black_count = sum(1 for row in range(self.BOARD_SIZE) for col in range(self.BOARD_SIZE)
                          if self.board[row][col] == "black")
        white_count = sum(1 for row in range(self.BOARD_SIZE) for col in range(self.BOARD_SIZE)
                          if self.board[row][col] == "white")
        self.black_count_var.set(f"Чорні: {black_count}")
        self.white_count_var.set(f"Білі: {white_count}")

        # Оновлення тексту поточного гравця
        if self.current_player.get() == "black":
            self.current_label.config(text="⚫ Чорні", foreground="black")
        else:
            self.current_label.config(text="⚪ Білі", foreground="white", background="#333", font=("Arial", 12, "bold"))
            self.current_label.config(background="")  # скидаємо фон

    def parse_cell(self, text: str):
        n = text.strip().lower()
        if not re.fullmatch(r"[a-h][1-8]", n):
            return None
        col = ord(n[0]) - ord("a")
        row = int(n[1]) - 1
        return col, row, n

    def get_valid_moves(self, player: str):
        """Повертає список клітинок, куди гравець може поставити фішку."""
        valid_moves = []

        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                if self.board[row][col] is not None:
                    continue

                # Перевіряємо всі 8 напрямків
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue

                        r, c = row + dr, col + dc
                        found_opponent = False

                        while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE:
                            if self.board[r][c] is None:
                                break
                            if self.board[r][c] == player:
                                if found_opponent:
                                    valid_moves.append((col, row))
                                break
                            else:  # суперник
                                found_opponent = True
                            r += dr
                            c += dc

        return valid_moves

    def get_flipped_pieces(self, row, col, player: str):
        """Повертає список клітинок, які будуть перевернуті після ходу."""
        flipped = []
        opponent = "white" if player == "black" else "black"

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue

                r, c = row + dr, col + dc
                pieces_to_flip = []

                while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE:
                    if self.board[r][c] is None:
                        break
                    if self.board[r][c] == opponent:
                        pieces_to_flip.append((r, c))
                    elif self.board[r][c] == player:
                        flipped.extend(pieces_to_flip)
                        break
                    else:
                        break
                    r += dr
                    c += dc

        return flipped

    def make_move(self):
        """Виконує хід гравця."""
        parsed = self.parse_cell(self.place_input.get())
        if not parsed:
            messagebox.showerror("Некоректний ввід", "Введіть клітинку у форматі a1–h8.")
            return

        col, row, cell_name = parsed
        player = self.current_player.get()

        # Перевіряємо, чи клітинка порожня
        if self.board[row][col] is not None:
            self.status_var.set(f"Клітинка {cell_name} вже зайнята!")
            self.place_input.set("")
            return

        # Перевіряємо, чи це допустимий хід
        flipped = self.get_flipped_pieces(row, col, player)
        if not flipped:
            self.status_var.set(f"Недопустимий хід на {cell_name}. Фішка не перевертає жодної суперника.")
            self.place_input.set("")
            return

        # Виконуємо хід
        self.board[row][col] = player
        for r, c in flipped:
            self.board[r][c] = player

        # Записуємо в історію
        self.history_no += 1
        flipped_cells = ", ".join([f"{chr(c + ord('a'))}{r + 1}" for r, c in flipped])
        self.tree.insert("", "end",
                         values=(self.history_no, cell_name, self.COLOR_NAMES[player],
                                 f"{len(flipped)} шт. ({flipped_cells})" if flipped else "0"))

        # Оновлюємо лічильники
        self._update_counts()

        # Змінюємо гравця
        new_player = "white" if player == "black" else "black"

        # Перевіряємо, чи є ходи у нового гравця
        valid_moves = self.get_valid_moves(new_player)
        if not valid_moves:
            # Якщо немає ходів, перевіряємо чи може поточний гравець ходити ще раз
            current_moves = self.get_valid_moves(player)
            if not current_moves:
                # Гра закінчена
                black_count = sum(1 for r in range(self.BOARD_SIZE) for c in range(self.BOARD_SIZE)
                                  if self.board[r][c] == "black")
                white_count = sum(1 for r in range(self.BOARD_SIZE) for c in range(self.BOARD_SIZE)
                                  if self.board[r][c] == "white")

                if black_count > white_count:
                    self.status_var.set(f"🎉 ГРА ЗАКІНЧЕНА! Перемогли чорні ({black_count}:{white_count})!")
                elif white_count > black_count:
                    self.status_var.set(f"🎉 ГРА ЗАКІНЧЕНА! Перемогли білі ({white_count}:{black_count})!")
                else:
                    self.status_var.set(f"🎉 ГРА ЗАКІНЧЕНА! Нічия ({black_count}:{white_count})!")

                messagebox.showinfo("Гра закінчена",
                                    f"Перемогли {'чорні' if black_count > white_count else 'білі' if white_count > black_count else 'нічия'}!\n"
                                    f"Чорні: {black_count}, Білі: {white_count}")
                return
            else:
                # Поточний гравець ходить ще раз
                self.status_var.set(
                    f"{self.COLOR_NAMES[player]} не має ходів. {self.COLOR_NAMES[player]} ходить ще раз.")
        else:
            self.current_player.set(new_player)
            self.status_var.set(
                f"Хід {self.COLOR_NAMES[new_player].lower()} на {cell_name}. Перевернуто {len(flipped)} фішок.")

        self.place_input.set("")
        self._update_counts()
        self.draw_board()
        self._update_valid_moves_display()

    def reset_game(self):
        """Починає нову гру."""
        # Очищаємо дошку
        self.board = [[None for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]

        # Початкова розстановка
        self.board[3][3] = "white"
        self.board[3][4] = "black"
        self.board[4][3] = "black"
        self.board[4][4] = "white"

        self.current_player.set("black")
        self.history_no = 0
        self.history.clear()

        # Очищаємо історію
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.place_input.set("")
        self.status_var.set("Нова гра! Хід чорних.")
        self._update_counts()
        self.draw_board()
        self._update_valid_moves_display()

    def _update_valid_moves_display(self):
        """Оновлює підсвітку можливих ходів (викликається при малюванні)."""
        # Просто перемальовуємо дошку - можливі ходи підсвічуються в draw_board
        self.draw_board()

    def cell_to_canvas(self, col, row):
        x1 = col * self.CELL_SIZE
        y1 = (7 - row) * self.CELL_SIZE
        return x1, y1, x1 + self.CELL_SIZE, y1 + self.CELL_SIZE

    def board_color(self, col, row):
        return self.LIGHT_SQUARE if (col + row) % 2 == 0 else self.DARK_SQUARE

    def draw_board(self):
        self.canvas.delete("all")

        # Отримуємо можливі ходи для поточного гравця
        valid_moves = self.get_valid_moves(self.current_player.get())

        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                x1, y1, x2, y2 = self.cell_to_canvas(col, row)

                # Колір клітинки
                color = self.board_color(col, row)

                # Підсвітка можливих ходів
                if (col, row) in valid_moves and self.board[row][col] is None:
                    color = self.VALID_MOVE

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=self.BORDER_COLOR, width=1)

                # Малюємо фішку
                piece = self.board[row][col]
                if piece is not None:
                    pad = 8
                    fill_color = "black" if piece == "black" else "white"
                    outline_color = "#666666"
                    self.canvas.create_oval(
                        x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                        fill=fill_color, outline=outline_color, width=2
                    )

                    # Додаємо невеликий блиск для білих фішок
                    if piece == "white":
                        self.canvas.create_oval(
                            x1 + pad + 4, y1 + pad + 4, x2 - pad - 8, y2 - pad - 8,
                            fill="#e0e0e0", outline="", width=0
                        )

        # Підписи рядків і стовпців
        for col in range(self.BOARD_SIZE):
            self.canvas.create_text(
                col * self.CELL_SIZE + self.CELL_SIZE / 2, self.BOARD_PIXELS - 9,
                text=chr(ord("a") + col), fill=self.TEXT_COLOR, font=("Arial", 10, "bold"))
        for row in range(self.BOARD_SIZE):
            self.canvas.create_text(
                10, (7 - row) * self.CELL_SIZE + self.CELL_SIZE / 2,
                text=str(row + 1), fill=self.TEXT_COLOR, font=("Arial", 10, "bold"), anchor="w")

    def on_canvas_click(self, event):
        """Обробка кліку мишкою на дошці."""
        col = event.x // self.CELL_SIZE
        row = 7 - (event.y // self.CELL_SIZE)

        if 0 <= col < self.BOARD_SIZE and 0 <= row < self.BOARD_SIZE:
            cell_name = f"{chr(col + ord('a'))}{row + 1}"
            self.place_input.set(cell_name)
            self.make_move()


# ──────────────────────────────────────────────────────────────────────────────
#  Головне вікно
# ──────────────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.title("Розміщення фігур — Bevziuk (повна версія)")
    root.resizable(False, False)

    try:
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=6, pady=6)

    ChessTab(notebook)  # 3.1, 3.2, 3.3 - Тура, Слон, Ферзь
    CheckersTab(notebook)  # 3.4 - Шашки
    ReversiTab(notebook)  # 3.5 - Реверсі

    root.mainloop()


if __name__ == "__main__":
    main()