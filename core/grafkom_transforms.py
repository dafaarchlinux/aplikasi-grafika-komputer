from __future__ import annotations

import math

Point = tuple[float, float]
Matrix3x3 = list[list[float]]


def mat_translate(dx: float, dy: float) -> Matrix3x3:
    return [[1, 0, dx], [0, 1, dy], [0, 0, 1]]


def mat_scale(sx: float, sy: float) -> Matrix3x3:
    return [[sx, 0, 0], [0, sy, 0], [0, 0, 1]]


def mat_rotate(angle_degrees: float) -> Matrix3x3:
    rad = math.radians(angle_degrees)
    c = math.cos(rad)
    s = math.sin(rad)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def mat_reflect_x() -> Matrix3x3:
    return [[1, 0, 0], [0, -1, 0], [0, 0, 1]]


def mat_reflect_y() -> Matrix3x3:
    return [[-1, 0, 0], [0, 1, 0], [0, 0, 1]]


def mat_shear_x(shx: float) -> Matrix3x3:
    return [[1, shx, 0], [0, 1, 0], [0, 0, 1]]


def mat_shear_y(shy: float) -> Matrix3x3:
    return [[1, 0, 0], [shy, 1, 0], [0, 0, 1]]


def apply_point(matrix: Matrix3x3, x: float, y: float) -> Point:
    return (
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2],
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2],
    )


def bounds(points: list[Point]) -> tuple[float, float, float, float]:
    if not points:
        return 0, 0, 0, 0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def center(points: list[Point]) -> Point:
    x1, y1, x2, y2 = bounds(points)
    return (x1 + x2) / 2, (y1 + y2) / 2


def apply_matrix(points: list[Point], matrix: Matrix3x3, about_center: bool = True) -> list[Point]:
    if not points:
        return []
    cx, cy = center(points) if about_center else (0, 0)
    result: list[Point] = []

    for x, y in points:
        lx = x - cx
        ly = y - cy
        tx, ty = apply_point(matrix, lx, ly)
        result.append((tx + cx, ty + cy))

    return result


def translate(points: list[Point], dx: float, dy: float) -> list[Point]:
    return [apply_point(mat_translate(dx, dy), x, y) for x, y in points]


def translate_keep_visible(points: list[Point], dx: float, dy: float, canvas_w: int, canvas_h: int) -> list[Point]:
    if not points:
        return []

    x1, y1, x2, y2 = bounds(points)
    obj_w = max(1, x2 - x1)
    obj_h = max(1, y2 - y1)

    visible_x = min(canvas_w * 0.45, max(32, obj_w * 0.35))
    visible_y = min(canvas_h * 0.45, max(32, obj_h * 0.35))

    nx1 = x1 + dx
    ny1 = y1 + dy

    min_left = -obj_w + visible_x
    max_left = canvas_w - visible_x
    min_top = -obj_h + visible_y
    max_top = canvas_h - visible_y

    corrected_x1 = min(max(nx1, min_left), max_left)
    corrected_y1 = min(max(ny1, min_top), max_top)

    return translate(points, corrected_x1 - x1, corrected_y1 - y1)


def scale(points: list[Point], sx: float, sy: float) -> list[Point]:
    return apply_matrix(points, mat_scale(sx, sy), about_center=True)


def rotate(points: list[Point], angle: float) -> list[Point]:
    return apply_matrix(points, mat_rotate(angle), about_center=True)


def reflect_x(points: list[Point]) -> list[Point]:
    return apply_matrix(points, mat_reflect_x(), about_center=True)


def reflect_y(points: list[Point]) -> list[Point]:
    return apply_matrix(points, mat_reflect_y(), about_center=True)


def shear_x(points: list[Point], shx: float) -> list[Point]:
    return apply_matrix(points, mat_shear_x(shx), about_center=True)


def shear_y(points: list[Point], shy: float) -> list[Point]:
    return apply_matrix(points, mat_shear_y(shy), about_center=True)
