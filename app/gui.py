from __future__ import annotations

import random
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from typing import Any

from PIL import Image, ImageDraw, ImageTk

from core.grafkom_shapes import SHAPE_LABELS, SHAPE_TOOLS, create_shape
from core import grafkom_transforms as tf
from models.graphic_object import GraphicObject, Point


APP_TITLE = "Aplikasi Grafika Komputer"
CANVAS_W = 900
CANVAS_H = 560

APP_BG = "#D7DEE8"
PANEL_BG = "#F8FAFC"
CANVAS_BG = "#FFFFFF"
WORKSPACE_BG = "#BFC7D3"

PALETTE = [
    "#000000", "#374151", "#6B7280", "#FFFFFF",
    "#EF4444", "#F97316", "#FACC15", "#22C55E",
    "#06B6D4", "#3B82F6", "#8B5CF6", "#EC4899",
]


class GrafkomApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1440x820")
        self.minsize(1280, 720)
        self.configure(bg=APP_BG)

        self.canvas_w = CANVAS_W
        self.canvas_h = CANVAS_H
        self.zoom = 1.0

        self.tool = tk.StringVar(value="select")
        self.tool_buttons: dict[str, tk.Button] = {}
        self.outline_color = tk.StringVar(value="#000000")
        self.fill_color = tk.StringVar(value="#FACC15")
        self.paper_fill = '#FFFFFF'
        self.use_fill_when_draw = tk.BooleanVar(value=False)
        self.stroke_width = tk.IntVar(value=3)
        self.translate_step = tk.IntVar(value=50)

        self.status = tk.StringVar(value="Siap. Pilih alat atau bentuk.")
        self.mouse_info = tk.StringVar(value="x=0, y=0")

        self.objects: list[GraphicObject] = []
        self.selected_id: str | None = None
        self.clipboard: GraphicObject | None = None
        self.counter = 1

        self.undo_stack: list[dict[str, Any]] = []
        self.redo_stack: list[dict[str, Any]] = []

        self.background = Image.new("RGB", (self.canvas_w, self.canvas_h), CANVAS_BG)
        self.tk_background: ImageTk.PhotoImage | None = None

        self.page_x = 24
        self.page_y = 24

        self.is_drawing = False
        self.is_moving = False
        self.move_started = False

        self.start_x = 0.0
        self.start_y = 0.0
        self.last_x = 0.0
        self.last_y = 0.0

        self.preview_object: GraphicObject | None = None
        self.pencil_points: list[Point] = []

        self.build_ui()
        self.build_context_menu()
        self.bind_events()
        self.refresh_tool_buttons()
        self.redraw()

    # =====================
    # UI sederhana
    # =====================

    def build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_left_panel()
        self.build_canvas()
        self.build_right_panel()
        self.build_statusbar()

    def build_header(self) -> None:
        header = tk.Frame(self, bg="#111827", height=46)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_propagate(False)

        tk.Label(
            header,
            text="Aplikasi Grafika Komputer",
            bg="#111827",
            fg="#FFFFFF",
            font=("Arial", 15, "bold"),
        ).pack(side="left", padx=16)

        tk.Label(
            header,
            text="Shape • Translasi • Scaling • Rotasi • Fill",
            bg="#111827",
            fg="#CBD5E1",
            font=("Arial", 10),
        ).pack(side="left", padx=12)

    def section(self, parent: tk.Widget, title: str) -> tk.Frame:
        frame = tk.LabelFrame(
            parent,
            text=title,
            bg=PANEL_BG,
            fg="#111827",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=8,
        )
        frame.pack(fill="x", padx=8, pady=6)
        return frame

    def btn(self, parent: tk.Widget, text: str, command, width: int = 18) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            width=width,
            command=command,
            bg="#FFFFFF",
            fg="#111827",
            activebackground="#DBEAFE",
            relief="groove",
            bd=1,
            font=("Arial", 9),
        )

    def tool_btn(self, parent: tk.Widget, text: str, tool: str, width: int = 18) -> tk.Button:
        button = self.btn(parent, text, lambda: self.set_tool(tool), width)
        self.tool_buttons[tool] = button
        return button

    def refresh_tool_buttons(self) -> None:
        active = self.tool.get()

        for tool, button in self.tool_buttons.items():
            if tool == active:
                button.configure(
                    bg="#2563EB",
                    fg="#FFFFFF",
                    relief="sunken",
                    activebackground="#1D4ED8",
                )
            else:
                button.configure(
                    bg="#FFFFFF",
                    fg="#111827",
                    relief="groove",
                    activebackground="#DBEAFE",
                )

    def build_left_panel(self) -> None:
        panel = tk.Frame(self, bg=PANEL_BG, width=430, bd=1, relief="solid")
        panel.grid(row=1, column=0, sticky="ns")
        panel.grid_propagate(False)

        file_box = self.section(panel, "File")
        self.btn(file_box, "Canvas Baru", self.new_canvas).pack(fill="x", pady=2)
        self.btn(file_box, "Simpan PNG", self.save_image).pack(fill="x", pady=2)
        self.btn(file_box, "Bersihkan", self.clear_canvas).pack(fill="x", pady=2)

        edit_box = self.section(panel, "Edit")
        self.btn(edit_box, "Undo", self.undo).grid(row=0, column=0, padx=2, pady=2)
        self.btn(edit_box, "Redo", self.redo).grid(row=0, column=1, padx=2, pady=2)
        self.btn(edit_box, "Hapus Objek", self.delete_selected, 18).grid(row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        tool_box = self.section(panel, "Alat")
        self.tool_btn(tool_box, "Pilih / Geser", "select").pack(fill="x", pady=2)
        self.tool_btn(tool_box, "Pensil / Corat-coret", "pencil").pack(fill="x", pady=2)
        self.tool_btn(tool_box, "Fill / Isi Warna", "fill").pack(fill="x", pady=2)

        tk.Label(tool_box, text="Ketebalan garis", bg=PANEL_BG).pack(anchor="w", pady=(6, 0))
        tk.Spinbox(tool_box, from_=1, to=20, width=6, textvariable=self.stroke_width).pack(anchor="w")

        shape_box = self.section(panel, "Shape")
        for icon, kind, label in SHAPE_TOOLS:
            self.tool_btn(shape_box, f"{icon}  {label}", kind).pack(fill="x", pady=2)

    def build_canvas(self) -> None:
        workspace = tk.Frame(self, bg=WORKSPACE_BG)
        workspace.grid(row=1, column=1, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(workspace, bg=WORKSPACE_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

    def build_right_panel(self) -> None:
        panel = tk.Frame(self, bg=PANEL_BG, width=430, bd=1, relief="solid")
        panel.grid(row=1, column=2, sticky="ns")
        panel.grid_propagate(False)

        translate_box = self.section(panel, "Translasi Pixel")
        tk.Label(translate_box, text="Jarak pixel", bg=PANEL_BG).grid(row=0, column=0, sticky="w")
        tk.Spinbox(translate_box, from_=1, to=500, width=7, textvariable=self.translate_step).grid(row=0, column=1, sticky="w", padx=4)

        self.btn(translate_box, "↖ Kiri Atas", lambda: self.translate_by_step(-1, -1), 12).grid(row=1, column=0, padx=2, pady=2)
        self.btn(translate_box, "↑ Atas", lambda: self.translate_by_step(0, -1), 12).grid(row=1, column=1, padx=2, pady=2)
        self.btn(translate_box, "↗ Kanan Atas", lambda: self.translate_by_step(1, -1), 12).grid(row=1, column=2, padx=2, pady=2)

        self.btn(translate_box, "← Kiri", lambda: self.translate_by_step(-1, 0), 12).grid(row=2, column=0, padx=2, pady=2)
        self.btn(translate_box, "→ Kanan", lambda: self.translate_by_step(1, 0), 12).grid(row=2, column=2, padx=2, pady=2)

        self.btn(translate_box, "↙ Kiri Bawah", lambda: self.translate_by_step(-1, 1), 12).grid(row=3, column=0, padx=2, pady=2)
        self.btn(translate_box, "↓ Bawah", lambda: self.translate_by_step(0, 1), 12).grid(row=3, column=1, padx=2, pady=2)
        self.btn(translate_box, "↘ Kanan Bawah", lambda: self.translate_by_step(1, 1), 12).grid(row=3, column=2, padx=2, pady=2)

        scale_box = self.section(panel, "Scaling")
        self.btn(scale_box, "0.5x", lambda: self.scale_selected(0.5, 0.5), 10).grid(row=0, column=0, padx=2, pady=2)
        self.btn(scale_box, "1x", lambda: self.scale_selected(1.0, 1.0), 10).grid(row=0, column=1, padx=2, pady=2)
        self.btn(scale_box, "2x", lambda: self.scale_selected(2.0, 2.0), 10).grid(row=0, column=2, padx=2, pady=2)
        self.btn(scale_box, "Custom", self.scale_custom, 32).grid(row=1, column=0, columnspan=3, sticky="ew", padx=2, pady=2)

        rotate_box = self.section(panel, "Rotasi Sudut")
        self.btn(rotate_box, "45°", lambda: self.rotate_selected(45), 10).grid(row=0, column=0, padx=2, pady=2)
        self.btn(rotate_box, "90°", lambda: self.rotate_selected(90), 10).grid(row=0, column=1, padx=2, pady=2)
        self.btn(rotate_box, "180°", lambda: self.rotate_selected(180), 10).grid(row=0, column=2, padx=2, pady=2)
        self.btn(rotate_box, "Custom", self.rotate_custom, 32).grid(row=1, column=0, columnspan=3, sticky="ew", padx=2, pady=2)

        color_box = self.section(panel, "Warna & Fill")
        color_box = self.section(panel, "Warna & Fill")

        self.outline_button = tk.Button(
            color_box,
            text="Warna Garis",
            bg=self.outline_color.get(),
            fg="white",
            command=self.choose_outline_color,
            font=("Arial", 9, "bold"),
        )
        self.outline_button.grid(row=0, column=0, columnspan=6, sticky="ew", padx=2, pady=2)

        self.fill_button = tk.Button(
            color_box,
            text="Warna Fill",
            bg=self.fill_color.get(),
            fg="#111827",
            command=self.choose_fill_color,
            font=("Arial", 9, "bold"),
        )
        self.fill_button.grid(row=1, column=0, columnspan=6, sticky="ew", padx=2, pady=2)

        tk.Label(color_box, text="Palet Garis", bg=PANEL_BG, fg="#334155", font=("Arial", 8, "bold")).grid(
            row=2, column=0, columnspan=6, sticky="w", padx=2, pady=(6, 1)
        )

        for index, color in enumerate(PALETTE):
            tk.Button(
                color_box,
                bg=color,
                width=3,
                height=1,
                relief="ridge",
                command=lambda c=color: self.set_outline_color(c),
            ).grid(row=3 + index // 6, column=index % 6, padx=2, pady=2)

        tk.Label(color_box, text="Palet Fill", bg=PANEL_BG, fg="#334155", font=("Arial", 8, "bold")).grid(
            row=6, column=0, columnspan=6, sticky="w", padx=2, pady=(8, 1)
        )

        for index, color in enumerate(PALETTE):
            tk.Button(
                color_box,
                bg=color,
                width=3,
                height=1,
                relief="ridge",
                command=lambda c=color: self.set_fill_color(c),
            ).grid(row=7 + index // 6, column=index % 6, padx=2, pady=2)

        tk.Checkbutton(
            color_box,
            text="Fill saat membuat shape",
            variable=self.use_fill_when_draw,
            bg=PANEL_BG,
            fg="#111827",
        ).grid(row=10, column=0, columnspan=6, sticky="w", padx=2, pady=(6, 2))

        tk.Label(
            color_box,
            text="Fill: pilih warna fill, pilih alat Fill, lalu klik shape tertutup.",
            bg=PANEL_BG,
            fg="#475569",
            wraplength=330,
            justify="left",
            font=("Arial", 8),
        ).grid(row=11, column=0, columnspan=6, sticky="w", padx=2, pady=(2, 4))


    def build_statusbar(self) -> None:
        bar = tk.Frame(self, bg="#F8FAFC", bd=1, relief="solid")
        bar.grid(row=2, column=0, columnspan=3, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        tk.Label(bar, textvariable=self.status, bg="#F8FAFC", fg="#334155").grid(row=0, column=0, sticky="w", padx=8)
        tk.Label(bar, textvariable=self.mouse_info, bg="#F8FAFC", fg="#334155").grid(row=0, column=1, sticky="e", padx=8)

    def build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Salin", command=self.copy_selected)
        self.context_menu.add_command(label="Tempel", command=self.paste_selected)
        self.context_menu.add_command(label="Duplikat", command=self.duplicate_selected)
        self.context_menu.add_command(label="Cut", command=self.cut_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Hapus Objek", command=self.delete_selected)
        self.context_menu.add_command(label="Batal Pilih", command=self.clear_selection)

    def bind_events(self) -> None:
        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Button-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.canvas.bind("<Button-3>", self.on_right_click)

        self.bind("<Delete>", lambda _event: self.delete_selected())
        self.bind("<BackSpace>", lambda _event: self.delete_selected())
        self.bind("<Escape>", lambda _event: self.clear_selection())

        self.bind("<Control-z>", lambda _event: self.undo())
        self.bind("<Control-y>", lambda _event: self.redo())
        self.bind("<Control-s>", lambda _event: self.save_image())
        self.bind("<Control-n>", lambda _event: self.new_canvas())

        self.bind("<Control-c>", lambda _event: self.copy_selected())
        self.bind("<Control-v>", lambda _event: self.paste_selected())
        self.bind("<Control-x>", lambda _event: self.cut_selected())
        self.bind("<Control-d>", lambda _event: self.duplicate_selected())

        self.bind("<Left>", lambda _event: self.nudge(-10, 0))
        self.bind("<Right>", lambda _event: self.nudge(10, 0))
        self.bind("<Up>", lambda _event: self.nudge(0, -10))
        self.bind("<Down>", lambda _event: self.nudge(0, 10))

        self.bind("<Shift-Left>", lambda _event: self.nudge(-50, 0))
        self.bind("<Shift-Right>", lambda _event: self.nudge(50, 0))
        self.bind("<Shift-Up>", lambda _event: self.nudge(0, -50))
        self.bind("<Shift-Down>", lambda _event: self.nudge(0, 50))

        self.bind("v", lambda _event: self.set_tool("select"))
        self.bind("p", lambda _event: self.set_tool("pencil"))
        self.bind("f", lambda _event: self.set_tool("fill"))
        self.bind("r", lambda _event: self.rotate_selected(45))

    # =====================
    # State
    # =====================

    def snapshot(self) -> dict[str, Any]:
        return {
            "objects": [obj.to_dict() for obj in self.objects],
            "selected_id": self.selected_id,
            "counter": self.counter,
            "background": self.background.copy(),
        }

    def restore(self, snap: dict[str, Any]) -> None:
        self.objects = [GraphicObject.from_dict(data) for data in snap["objects"]]
        self.selected_id = snap["selected_id"]
        self.counter = snap["counter"]
        self.background = snap["background"].copy()
        self.redraw()

    def push_undo(self) -> None:
        self.undo_stack.append(self.snapshot())
        self.undo_stack = self.undo_stack[-80:]
        self.redo_stack.clear()

    def undo(self) -> None:
        if not self.undo_stack:
            self.status.set("Tidak ada aksi untuk Undo.")
            return
        self.redo_stack.append(self.snapshot())
        self.restore(self.undo_stack.pop())
        self.status.set("Undo berhasil.")

    def redo(self) -> None:
        if not self.redo_stack:
            self.status.set("Tidak ada aksi untuk Redo.")
            return
        self.undo_stack.append(self.snapshot())
        self.restore(self.redo_stack.pop())
        self.status.set("Redo berhasil.")

    # =====================
    # Coordinates
    # =====================

    def display_w(self) -> int:
        return int(self.canvas_w * self.zoom)

    def display_h(self) -> int:
        return int(self.canvas_h * self.zoom)

    def update_page_position(self) -> None:
        view_w = max(1, self.canvas.winfo_width())
        view_h = max(1, self.canvas.winfo_height())
        self.page_x = max(24, (view_w - self.display_w()) // 2)
        self.page_y = max(24, (view_h - self.display_h()) // 2)

    def to_world(self, sx: float, sy: float) -> Point:
        return (sx - self.page_x) / self.zoom, (sy - self.page_y) / self.zoom

    def to_screen(self, point: Point) -> Point:
        return self.page_x + point[0] * self.zoom, self.page_y + point[1] * self.zoom

    def screen_flat(self, points: list[Point]) -> list[float]:
        flat: list[float] = []
        for point in points:
            x, y = self.to_screen(point)
            flat.extend([x, y])
        return flat

    def inside_canvas(self, x: float, y: float) -> bool:
        return 0 <= x <= self.canvas_w and 0 <= y <= self.canvas_h

    # =====================
    # Draw
    # =====================

    def redraw(self) -> None:
        if not hasattr(self, "canvas"):
            return

        self.update_page_position()
        self.canvas.delete("all")

        sw = self.display_w()
        sh = self.display_h()
        view_w = max(self.canvas.winfo_width(), self.page_x + sw + 24)
        view_h = max(self.canvas.winfo_height(), self.page_y + sh + 24)

        self.canvas.create_rectangle(0, 0, view_w, view_h, fill=WORKSPACE_BG, outline="")
        self.canvas.create_rectangle(
            self.page_x - 12,
            self.page_y - 12,
            self.page_x + sw + 12,
            self.page_y + sh + 12,
            fill="#DCE3EC",
            outline="#AEB8C5",
        )

        bg = self.background.resize((sw, sh), Image.Resampling.BILINEAR)
        self.tk_background = ImageTk.PhotoImage(bg)

        self.canvas.create_rectangle(
            self.page_x,
            self.page_y,
            self.page_x + sw,
            self.page_y + sh,
            fill=CANVAS_BG,
            outline="#64748B",
        )
        self.canvas.create_image(self.page_x, self.page_y, anchor="nw", image=self.tk_background)

        for obj in self.objects:
            self.draw_object(obj)

        if self.preview_object:
            self.draw_object(self.preview_object)

        self.draw_clip_mask(view_w, view_h, sw, sh)
        self.draw_selection()

    def draw_object(self, obj: GraphicObject) -> None:
        tag = f"obj:{obj.object_id}"
        outline = obj.outline
        fill = obj.fill if obj.closed else ""
        width = max(1, round(obj.width * self.zoom))
        points = obj.points

        if obj.kind == "pencil":
            if len(points) >= 2:
                if obj.closed:
                    self.canvas.create_polygon(
                        *self.screen_flat(points),
                        outline=outline,
                        fill=obj.fill,
                        width=width,
                        smooth=True,
                        tags=(tag,),
                    )
                else:
                    self.canvas.create_line(
                        *self.screen_flat(points),
                        fill=outline,
                        width=width,
                        capstyle="round",
                        joinstyle="round",
                        smooth=True,
                        tags=(tag,),
                    )
            return

        if obj.closed:
            self.canvas.create_polygon(
                *self.screen_flat(points),
                outline=outline,
                fill=fill,
                width=width,
                smooth=True if obj.kind in {"circle", "ellipse"} else False,
                tags=(tag,),
            )
        else:
            self.canvas.create_line(
                *self.screen_flat(points),
                fill=outline,
                width=width,
                capstyle="round",
                joinstyle="round",
                tags=(tag,),
            )

    def draw_clip_mask(self, view_w: int, view_h: int, sw: int, sh: int) -> None:
        left = self.page_x
        top = self.page_y
        right = self.page_x + sw
        bottom = self.page_y + sh

        self.canvas.create_rectangle(0, 0, view_w, top, fill=WORKSPACE_BG, outline="", tags=("clip_mask",))
        self.canvas.create_rectangle(0, bottom, view_w, view_h, fill=WORKSPACE_BG, outline="", tags=("clip_mask",))
        self.canvas.create_rectangle(0, top, left, bottom, fill=WORKSPACE_BG, outline="", tags=("clip_mask",))
        self.canvas.create_rectangle(right, top, view_w, bottom, fill=WORKSPACE_BG, outline="", tags=("clip_mask",))
        self.canvas.create_rectangle(left, top, right, bottom, outline="#64748B", width=1, tags=("clip_mask",))

    def draw_selection(self) -> None:
        obj = self.selected_object()
        if not obj:
            return

        bbox = self.canvas.bbox(f"obj:{obj.object_id}")
        if not bbox:
            return

        x1, y1, x2, y2 = bbox
        self.canvas.create_rectangle(
            x1 - 6,
            y1 - 6,
            x2 + 6,
            y2 + 6,
            outline="#2563EB",
            dash=(4, 3),
            width=2,
            tags=("selection_ui",),
        )

    def point_distance(self, a: Point, b: Point) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx * dx + dy * dy) ** 0.5

    def is_pencil_closed(self, points: list[Point]) -> bool:
        if len(points) < 8:
            return False

        start = points[0]
        end = points[-1]

        # Toleransi dibuat cukup nyaman untuk gambar pakai mouse.
        return self.point_distance(start, end) <= max(28, int(self.stroke_width.get()) * 8)

    def point_inside_polygon(self, x: float, y: float, points: list[Point]) -> bool:
        if len(points) < 3:
            return False

        inside = False
        j = len(points) - 1

        for i in range(len(points)):
            xi, yi = points[i]
            xj, yj = points[j]

            intersects = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
            )

            if intersects:
                inside = not inside

            j = i

        return inside

    def find_closed_object_containing(self, x: float, y: float) -> GraphicObject | None:
        """
        Mencari objek tertutup yang berisi titik klik.

        Untuk pensil:
        - Walaupun user tidak menutup garis dengan sempurna,
          jika bentuknya sudah mengelilingi titik klik, coretan dianggap sebagai loop.
        - Ini membuat Fill lebih mirip Paint: klik di dalam coretan tertutup akan mengisi area itu,
          bukan background.
        """
        for obj in reversed(self.objects):
            if len(obj.points) < 3:
                continue

            if obj.closed and self.point_inside_polygon(x, y, obj.points):
                return obj

            if obj.kind == "pencil" and len(obj.points) >= 8:
                if self.point_inside_polygon(x, y, obj.points):
                    return obj

        return None

    def close_pencil_object_if_needed(self, obj: GraphicObject) -> None:
        if obj.kind != "pencil":
            return

        if obj.closed:
            return

        if len(obj.points) < 3:
            return

        obj.closed = True

        # Tutup polygon dengan menyambungkan titik akhir ke titik awal.
        if obj.points[0] != obj.points[-1]:
            obj.points.append(obj.points[0])

    # =====================
    # Mouse
    # =====================
    # Mouse
    # =====================

    def on_motion(self, event) -> None:
        x, y = self.to_world(event.x, event.y)
        self.mouse_info.set(f"x={int(x)}, y={int(y)}")

    def on_down(self, event) -> None:
        self.focus_set()
        self.canvas.focus_set()

        x, y = self.to_world(event.x, event.y)
        active_tool = self.tool.get()

        if active_tool == "select":
            self.select_at(event.x, event.y)
            self.is_moving = self.selected_id is not None
            self.move_started = False
            self.last_x = x
            self.last_y = y
            self.redraw()
            return

        if active_tool == "fill":
            if not self.inside_canvas(x, y):
                self.status.set("Fill hanya bisa dilakukan di area canvas.")
                return

            # Prioritas 1: isi shape/coretan tertutup yang mengandung titik klik.
            obj = self.find_closed_object_containing(x, y)

            # Prioritas 2: kalau klik tepat pada objek tertutup.
            if obj is None:
                clicked_obj = self.find_object_at(event.x, event.y)
                if clicked_obj and clicked_obj.closed:
                    obj = clicked_obj
                elif clicked_obj and not clicked_obj.closed:
                    self.status.set("Objek ini belum membentuk area tertutup, jadi belum bisa di-fill.")
                    return

            if obj is not None:
                self.push_undo()

                if obj.kind == "pencil":
                    self.close_pencil_object_if_needed(obj)

                obj.fill = self.fill_color.get()
                self.selected_id = obj.object_id
                self.status.set(f"Fill diterapkan ke {obj.name}.")
                self.redraw()
                return

            # Kalau klik benar-benar area kosong canvas, fill background seperti Paint.
            self.push_undo()
            self.background = Image.new("RGB", (self.canvas_w, self.canvas_h), self.fill_color.get())
            self.status.set("Background canvas berhasil di-fill.")
            self.redraw()
            return

        if not self.inside_canvas(x, y):
            self.status.set("Mulai menggambar dari dalam canvas putih.")
            return

        self.is_drawing = True
        self.start_x = x
        self.start_y = y
        self.last_x = x
        self.last_y = y

        if active_tool == "pencil":
            self.push_undo()
            self.pencil_points = [(x, y)]

    def on_drag(self, event) -> None:
        x, y = self.to_world(event.x, event.y)

        if self.tool.get() == "select" and self.is_moving:
            obj = self.selected_object()
            if obj:
                if not self.move_started:
                    self.push_undo()
                    self.move_started = True

                dx = x - self.last_x
                dy = y - self.last_y
                obj.points = tf.translate_keep_visible(obj.points, dx, dy, self.canvas_w, self.canvas_h)

                self.last_x = x
                self.last_y = y
                self.redraw()
            return

        if not self.is_drawing:
            return

        if self.tool.get() == "pencil":
            self.pencil_points.append((x, y))
            self.preview_object = GraphicObject(
                object_id="preview",
                name="Preview",
                kind="pencil",
                points=list(self.pencil_points),
                outline=self.outline_color.get(),
                fill="",
                width=self.stroke_width.get(),
                closed=False,
            )
            self.redraw()
            return

        if self.tool.get() in SHAPE_LABELS:
            self.preview_object = self.make_shape("preview", self.tool.get(), self.start_x, self.start_y, x, y)
            self.redraw()

    def on_up(self, event) -> None:
        x, y = self.to_world(event.x, event.y)

        if self.tool.get() == "select":
            self.is_moving = False
            self.move_started = False
            return

        if not self.is_drawing:
            return

        self.is_drawing = False

        if self.tool.get() == "pencil":
            self.pencil_points.append((x, y))

            closed = self.is_pencil_closed(self.pencil_points)
            points = list(self.pencil_points)

            if closed:
                # Tutup titik akhir ke titik awal agar area fill tidak bocor.
                points.append(points[0])

            obj = GraphicObject(
                object_id=self.next_id(),
                name=f"Coretan {self.counter}",
                kind="pencil",
                points=points,
                outline=self.outline_color.get(),
                fill="",
                width=self.stroke_width.get(),
                closed=closed,
            )
            self.add_object(obj, save_undo=False)
            self.preview_object = None

            if closed:
                self.status.set("Coretan tertutup dibuat. Bisa di-fill.")
            return

        if self.tool.get() in SHAPE_LABELS:
            self.push_undo()
            obj = self.make_shape(self.next_id(), self.tool.get(), self.start_x, self.start_y, x, y)
            self.add_object(obj, save_undo=False)
            self.preview_object = None

    def on_right_click(self, event) -> None:
        self.select_at(event.x, event.y)
        self.redraw()
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # =====================
    # Object
    # =====================

    def next_id(self) -> str:
        return f"obj-{self.counter}-{random.random()}"

    def make_shape(self, object_id: str, kind: str, x1: float, y1: float, x2: float, y2: float) -> GraphicObject:
        fill = self.fill_color.get() if self.use_fill_when_draw.get() else ""
        return create_shape(
            object_id=object_id,
            kind=kind,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            outline=self.outline_color.get(),
            fill=fill,
            width=self.stroke_width.get(),
        )

    def add_object(self, obj: GraphicObject, save_undo: bool = True) -> None:
        if save_undo:
            self.push_undo()

        self.objects.append(obj)
        self.selected_id = obj.object_id
        self.counter += 1
        self.status.set(f"{obj.name} dibuat.")
        self.redraw()

    def selected_object(self) -> GraphicObject | None:
        for obj in self.objects:
            if obj.object_id == self.selected_id:
                return obj
        return None

    def find_object_at(self, sx: int, sy: int) -> GraphicObject | None:
        found = self.canvas.find_overlapping(sx - 4, sy - 4, sx + 4, sy + 4)

        for item in reversed(found):
            tags = self.canvas.gettags(item)
            if "clip_mask" in tags or "selection_ui" in tags:
                continue

            for tag in tags:
                if tag.startswith("obj:"):
                    object_id = tag.replace("obj:", "")
                    for obj in self.objects:
                        if obj.object_id == object_id:
                            return obj

        return None

    def select_at(self, sx: int, sy: int) -> None:
        obj = self.find_object_at(sx, sy)

        if obj:
            self.selected_id = obj.object_id
            self.status.set(f"Objek dipilih: {obj.name}")
        else:
            self.selected_id = None
            self.status.set("Tidak ada objek dipilih.")

    def delete_selected(self) -> None:
        if not self.selected_id:
            self.status.set("Tidak ada objek dipilih.")
            return

        self.push_undo()
        self.objects = [obj for obj in self.objects if obj.object_id != self.selected_id]
        self.selected_id = None
        self.status.set("Objek dihapus.")
        self.redraw()

    def clear_selection(self) -> None:
        self.selected_id = None
        self.status.set("Pilihan dibatalkan.")
        self.redraw()

    def apply_fill_to_selected(self) -> None:
        obj = self.selected_object()
        if not obj:
            self.status.set("Pilih objek tertutup dulu untuk diberi fill.")
            return

        if not obj.closed:
            self.status.set("Fill hanya untuk bentuk tertutup.")
            return

        self.push_undo()
        obj.fill = self.fill_color.get()
        self.status.set(f"Fill diterapkan ke {obj.name}.")
        self.redraw()

    def copy_selected(self) -> None:
        obj = self.selected_object()
        if not obj:
            self.status.set("Pilih objek dulu untuk disalin.")
            return

        self.clipboard = obj.copy()
        self.status.set("Objek disalin. Gunakan Ctrl+V untuk menempel.")

    def paste_selected(self) -> None:
        if not self.clipboard:
            self.status.set("Belum ada objek yang disalin.")
            return

        self.push_undo()
        obj = self.clipboard.copy()
        obj.object_id = self.next_id()
        obj.name = f"{obj.name} Copy"
        obj.points = tf.translate_keep_visible(obj.points, 30, 30, self.canvas_w, self.canvas_h)

        self.objects.append(obj)
        self.selected_id = obj.object_id
        self.counter += 1
        self.status.set("Objek ditempel.")
        self.redraw()

    def duplicate_selected(self) -> None:
        self.copy_selected()
        self.paste_selected()

    def cut_selected(self) -> None:
        obj = self.selected_object()
        if not obj:
            self.status.set("Pilih objek dulu untuk cut.")
            return

        self.copy_selected()
        self.delete_selected()
        self.status.set("Objek dipotong. Gunakan Ctrl+V untuk menempel.")

    # =====================
    # Transform
    # =====================

    def require_selected(self) -> GraphicObject | None:
        obj = self.selected_object()
        if not obj:
            messagebox.showinfo("Pilih Objek", "Pilih objek terlebih dahulu menggunakan alat Pilih.")
            return None
        return obj

    def translate_by_step(self, direction_x: int, direction_y: int) -> None:
        try:
            step = max(1, min(int(self.translate_step.get()), 500))
        except Exception:
            step = 50

        self.translate_selected(direction_x * step, direction_y * step)

    def translate_selected(self, dx: float, dy: float) -> None:
        obj = self.require_selected()
        if not obj:
            return

        self.push_undo()
        obj.points = tf.translate_keep_visible(obj.points, dx, dy, self.canvas_w, self.canvas_h)
        self.status.set(f"Translasi: {dx} px, {dy} px")
        self.redraw()

    def nudge(self, dx: float, dy: float) -> None:
        obj = self.selected_object()
        if not obj:
            self.status.set("Pilih objek dulu.")
            return

        self.push_undo()
        obj.points = tf.translate_keep_visible(obj.points, dx, dy, self.canvas_w, self.canvas_h)
        self.redraw()

    def scale_selected(self, sx: float, sy: float) -> None:
        obj = self.require_selected()
        if not obj:
            return

        self.push_undo()
        obj.points = tf.scale(obj.points, sx, sy)
        self.status.set(f"Scaling: sx={sx}, sy={sy}")
        self.redraw()

    def scale_custom(self) -> None:
        sx = simpledialog.askfloat("Scaling Custom", "Masukkan skala X:", initialvalue=1.5)
        if sx is None:
            return

        sy = simpledialog.askfloat("Scaling Custom", "Masukkan skala Y:", initialvalue=sx)
        if sy is None:
            return

        self.scale_selected(sx, sy)

    def rotate_selected(self, angle: float) -> None:
        obj = self.require_selected()
        if not obj:
            return

        self.push_undo()
        obj.points = tf.rotate(obj.points, angle)
        self.status.set(f"Rotasi: {angle}°")
        self.redraw()

    def rotate_custom(self) -> None:
        angle = simpledialog.askfloat("Rotasi Custom", "Masukkan sudut derajat:", initialvalue=45)
        if angle is None:
            return

        self.rotate_selected(angle)

    # =====================
    # File
    # =====================
    # File
    # =====================

    def flatten_image(self) -> Image.Image:
        image = self.background.copy()
        draw = ImageDraw.Draw(image)

        for obj in self.objects:
            if obj.kind == "pencil":
                if len(obj.points) >= 2:
                    if obj.closed:
                        draw.polygon(obj.points, outline=obj.outline, fill=obj.fill or None)
                    else:
                        draw.line(obj.points, fill=obj.outline, width=obj.width)
            elif obj.closed:
                draw.polygon(obj.points, outline=obj.outline, fill=obj.fill or None)
            else:
                draw.line(obj.points, fill=obj.outline, width=obj.width)

        return image

    def new_canvas(self) -> None:
        self.push_undo()
        self.objects.clear()
        self.selected_id = None
        self.background = Image.new("RGB", (self.canvas_w, self.canvas_h), CANVAS_BG)
        self.status.set("Canvas baru.")
        self.redraw()

    def clear_canvas(self) -> None:
        if messagebox.askyesno("Bersihkan Canvas", "Hapus semua gambar?"):
            self.new_canvas()

    def save_image(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
        )
        if not path:
            return

        self.flatten_image().save(path)
        self.status.set(f"Gambar disimpan: {path}")

    # =====================
    # Color / Tool
    # =====================

    def set_tool(self, tool: str) -> None:
        self.tool.set(tool)
        label = SHAPE_LABELS.get(tool, {"select": "Pilih", "pencil": "Pensil", "fill": "Fill"}.get(tool, tool))
        self.status.set(f"Tool aktif: {label}")
        self.refresh_tool_buttons()

    def set_outline_color(self, color: str) -> None:
        self.outline_color.set(color)
        self.outline_button.configure(bg=color, fg="white" if color.lower() != "#ffffff" else "#111827")

    def set_fill_color(self, color: str) -> None:
        self.fill_color.set(color)
        self.fill_button.configure(bg=color, fg="white" if color.lower() != "#ffffff" else "#111827")

    def choose_outline_color(self) -> None:
        result = colorchooser.askcolor(color=self.outline_color.get(), title="Pilih warna garis")
        if result and result[1]:
            self.set_outline_color(result[1])

    def choose_fill_color(self) -> None:
        result = colorchooser.askcolor(color=self.fill_color.get(), title="Pilih warna fill")
        if result and result[1]:
            self.set_fill_color(result[1])


def run_app() -> None:
    app = GrafkomApp()
    app.mainloop()
