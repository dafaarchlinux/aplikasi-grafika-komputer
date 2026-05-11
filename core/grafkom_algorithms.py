from __future__ import annotations

import math

PointInt = tuple[int, int]
PointFloat = tuple[float, float]


def line_dda(x1: float, y1: float, x2: float, y2: float) -> list[PointInt]:
    """
    Algoritma DDA Line.

    dx = x2 - x1
    dy = y2 - y1
    steps = max(|dx|, |dy|)
    x_inc = dx / steps
    y_inc = dy / steps
    """
    dx = x2 - x1
    dy = y2 - y1
    steps = int(max(abs(dx), abs(dy)))

    if steps == 0:
        return [(round(x1), round(y1))]

    x_inc = dx / steps
    y_inc = dy / steps

    x = x1
    y = y1
    points: list[PointInt] = []

    for _ in range(steps + 1):
        points.append((round(x), round(y)))
        x += x_inc
        y += y_inc

    return points


def line_bresenham(x1: float, y1: float, x2: float, y2: float) -> list[PointInt]:
    """
    Algoritma Bresenham Line.

    Lebih efisien dari DDA karena memakai operasi integer.
    Cocok dijelaskan saat presentasi grafika komputer.
    """
    x1, y1, x2, y2 = map(round, (x1, y1, x2, y2))

    points: list[PointInt] = []

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    err = dx - dy

    x = x1
    y = y1

    while True:
        points.append((x, y))

        if x == x2 and y == y2:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x += sx

        if e2 < dx:
            err += dx
            y += sy

    return points


def midpoint_circle(cx: float, cy: float, radius: float) -> list[PointFloat]:
    """
    Midpoint Circle Algorithm.

    Memanfaatkan simetri 8 arah lingkaran.
    Titik yang dihasilkan berupa perimeter lingkaran.
    """
    r = max(1, round(abs(radius)))
    x = 0
    y = r
    p = 1 - r

    points: set[PointInt] = set()

    def add_circle_points(px: int, py: int) -> None:
        candidates = [
            (round(cx + px), round(cy + py)),
            (round(cx - px), round(cy + py)),
            (round(cx + px), round(cy - py)),
            (round(cx - px), round(cy - py)),
            (round(cx + py), round(cy + px)),
            (round(cx - py), round(cy + px)),
            (round(cx + py), round(cy - px)),
            (round(cx - py), round(cy - px)),
        ]
        points.update(candidates)

    add_circle_points(x, y)

    while x < y:
        x += 1

        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1

        add_circle_points(x, y)

    return sort_points_around_center([(float(x), float(y)) for x, y in points], cx, cy)


def midpoint_ellipse(cx: float, cy: float, rx: float, ry: float) -> list[PointFloat]:
    """
    Midpoint Ellipse Algorithm.

    Menggunakan dua region:
    Region 1: slope < 1
    Region 2: slope >= 1
    """
    rx = max(1, round(abs(rx)))
    ry = max(1, round(abs(ry)))

    x = 0
    y = ry

    rx2 = rx * rx
    ry2 = ry * ry

    px = 0
    py = 2 * rx2 * y

    points: set[PointInt] = set()

    def add_ellipse_points(px_: int, py_: int) -> None:
        candidates = [
            (round(cx + px_), round(cy + py_)),
            (round(cx - px_), round(cy + py_)),
            (round(cx + px_), round(cy - py_)),
            (round(cx - px_), round(cy - py_)),
        ]
        points.update(candidates)

    add_ellipse_points(x, y)

    # Region 1
    p1 = ry2 - (rx2 * ry) + (0.25 * rx2)

    while px < py:
        x += 1
        px += 2 * ry2

        if p1 < 0:
            p1 += ry2 + px
        else:
            y -= 1
            py -= 2 * rx2
            p1 += ry2 + px - py

        add_ellipse_points(x, y)

    # Region 2
    p2 = (
        ry2 * ((x + 0.5) ** 2)
        + rx2 * ((y - 1) ** 2)
        - rx2 * ry2
    )

    while y > 0:
        y -= 1
        py -= 2 * rx2

        if p2 > 0:
            p2 += rx2 - py
        else:
            x += 1
            px += 2 * ry2
            p2 += rx2 - py + px

        add_ellipse_points(x, y)

    return sort_points_around_center([(float(x), float(y)) for x, y in points], cx, cy)


def regular_polygon(cx: float, cy: float, radius: float, sides: int, start_angle: float = -90) -> list[PointFloat]:
    """
    Membuat polygon beraturan seperti pentagon dan hexagon.
    """
    radius = max(1, radius)
    points: list[PointFloat] = []

    for i in range(sides):
        angle = math.radians(start_angle + 360 * i / sides)
        points.append((
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle),
        ))

    return points


def sort_points_around_center(points: list[PointFloat], cx: float, cy: float) -> list[PointFloat]:
    """
    Mengurutkan titik berdasarkan sudut terhadap pusat.

    Ini penting agar titik midpoint circle/ellipse bisa digambar sebagai polygon
    yang rapi, bukan acak.
    """
    return sorted(points, key=lambda point: math.atan2(point[1] - cy, point[0] - cx))


def bounds(points: list[PointFloat]) -> tuple[float, float, float, float]:
    if not points:
        return 0, 0, 0, 0

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]

    return min(xs), min(ys), max(xs), max(ys)


def center(points: list[PointFloat]) -> PointFloat:
    x1, y1, x2, y2 = bounds(points)
    return (x1 + x2) / 2, (y1 + y2) / 2
