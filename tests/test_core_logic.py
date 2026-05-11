import unittest

from core.grafkom_shapes import SHAPE_TOOLS, create_shape
from core import grafkom_transforms as tf


class TestCoreGrafkomLogic(unittest.TestCase):
    def test_five_required_shapes_exist(self):
        kinds = [kind for _, kind, _ in SHAPE_TOOLS]
        self.assertEqual(kinds, ["line", "rect", "circle", "triangle", "ellipse"])

    def test_all_shapes_create_points(self):
        for _, kind, _ in SHAPE_TOOLS:
            with self.subTest(kind=kind):
                obj = create_shape(
                    object_id="test",
                    kind=kind,
                    x1=10,
                    y1=10,
                    x2=120,
                    y2=90,
                    outline="#000000",
                    fill="#FFFFFF",
                    width=3,
                )
                self.assertTrue(obj.points)
                self.assertGreaterEqual(len(obj.points), 2)

    def test_translation_formula(self):
        points = [(10, 10), (20, 20)]
        result = tf.translate(points, 5, -3)
        self.assertEqual(result, [(15, 7), (25, 17)])

    def test_scaling_changes_size(self):
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = tf.scale(points, 2, 2)
        x1, y1, x2, y2 = tf.bounds(result)
        self.assertEqual(round(x2 - x1), 20)
        self.assertEqual(round(y2 - y1), 20)

    def test_rotation_keeps_number_of_points(self):
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = tf.rotate(points, 90)
        self.assertEqual(len(result), len(points))

    def test_reflection_keeps_number_of_points(self):
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertEqual(len(tf.reflect_x(points)), len(points))
        self.assertEqual(len(tf.reflect_y(points)), len(points))

    def test_shear_keeps_number_of_points(self):
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertEqual(len(tf.shear_x(points, 0.3)), len(points))
        self.assertEqual(len(tf.shear_y(points, 0.3)), len(points))

    def test_translate_keep_visible_not_empty(self):
        points = [(100, 100), (200, 100), (200, 200), (100, 200)]
        result = tf.translate_keep_visible(points, 9999, 0, 900, 560)
        x1, y1, x2, y2 = tf.bounds(result)
        self.assertLess(x1, 900)
        self.assertGreater(x2, 0)


if __name__ == "__main__":
    unittest.main()
