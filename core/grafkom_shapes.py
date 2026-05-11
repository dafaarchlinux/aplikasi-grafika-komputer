from __future__ import annotations

import math

from core.grafkom_algorithms import line_bresenham
from models.graphic_object import GraphicObject, Point


# Fokus sesuai ketentuan dosen: minimal 5 bentuk.
# Dibuat tepat 5 agar GUI lebih rapi, mudah dipresentasikan, dan tidak berantakan.
SHAPE_TOOLS: list[tuple[str, str, str]] = [
    ("╱", "line", "Garis"),
    ("▭", "rect", "Persegi"),
    ("○", "circle", "Lingkaran"),
    ("△", "triangle", "Segitiga"),
    ("⬭", "ellipse", "Ellipse"),
]

SHAPE_LABELS = {kind: label for _, kind, label in SHAPE_TOOLS}


def _bbox(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float, float, float]:
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def _smooth_ellipse_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    samples: int = 180,
) -> list[Point]:
    """
    Titik ellipse halus untuk tampilan GUI.

    Catatan presentasi:
    - Logika dasar ellipse tetap mengikuti konsep pembentukan titik tepi.
    - Untuk GUI modern, jumlah titik dibuat banyak agar lingkaran/ellipse terlihat halus.
    """
    rx = max(1.0, abs(rx))
    ry = max(1.0, abs(ry))

    points: list[Point] = []

    for i in range(samples):
        theta = 2 * math.pi * i / samples
        points.append((
            cx + rx * math.cos(theta),
            cy + ry * math.sin(theta),
        ))

    return points


def create_shape(
    object_id: str,
    kind: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    outline: str,
    fill: str,
    width: int,
) -> GraphicObject:
    """
    Membuat objek grafika.

    Logika:
    - Garis memakai Bresenham sebagai referensi algoritma grafika komputer.
    - Persegi dan segitiga memakai titik polygon.
    - Lingkaran dan ellipse memakai titik tepi halus agar tampilan aplikasi rapi.
    - Semua shape disimpan sebagai daftar titik agar bisa ditransformasi matriks:
      translasi, scaling, rotasi, refleksi, dan shear.
    """
    label = SHAPE_LABELS.get(kind, kind)
    closed = True

    if kind == "line":
        points = [(float(x), float(y)) for x, y in line_bresenham(x1, y1, x2, y2)]
        closed = False
        fill = ""

    elif kind == "rect":
        ax, ay, bx, by = _bbox(x1, y1, x2, y2)
        points = [
            (ax, ay),
            (bx, ay),
            (bx, by),
            (ax, by),
        ]

    elif kind == "circle":
        side = max(abs(x2 - x1), abs(y2 - y1))
        signed_x2 = x1 + side * (1 if x2 >= x1 else -1)
        signed_y2 = y1 + side * (1 if y2 >= y1 else -1)

        ax, ay, bx, by = _bbox(x1, y1, signed_x2, signed_y2)
        cx = (ax + bx) / 2
        cy = (ay + by) / 2
        radius = min(bx - ax, by - ay) / 2
        points = _smooth_ellipse_points(cx, cy, radius, radius, samples=220)

    elif kind == "triangle":
        ax, ay, bx, by = _bbox(x1, y1, x2, y2)
        points = [
            ((ax + bx) / 2, ay),
            (bx, by),
            (ax, by),
        ]

    elif kind == "ellipse":
        ax, ay, bx, by = _bbox(x1, y1, x2, y2)
        cx = (ax + bx) / 2
        cy = (ay + by) / 2
        rx = (bx - ax) / 2
        ry = (by - ay) / 2
        points = _smooth_ellipse_points(cx, cy, rx, ry, samples=220)

    else:
        points = [(x1, y1), (x2, y2)]
        closed = False
        fill = ""

    return GraphicObject(
        object_id=object_id,
        name=label,
        kind=kind,
        points=points,
        outline=outline,
        fill=fill,
        width=width,
        closed=closed,
    )
