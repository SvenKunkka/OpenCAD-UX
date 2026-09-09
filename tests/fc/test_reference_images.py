# -*- coding: utf-8 -*-
"""Console tests - reference image import/attach/calibrate/transparency/lock."""
import os
import struct
import sys
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import FreeCAD as App  # noqa: E402
from opencad_ux.reference_images import (create_reference_image,  # noqa: E402
                                         set_image_plane, set_transparency,
                                         set_locked, set_visibility,
                                         set_world_width,
                                         calibrate_from_two_points,
                                         image_size, RefImageError)


def _mini_png(path, w=80, h=50):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

    row = b"\x00" + b"\xff\x00\x00" * w
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" +
                 chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
                 chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b""))


class TestReferenceImages(unittest.TestCase):
    def setUp(self):
        self.dir = os.path.join(ROOT, "tests", "output")
        os.makedirs(self.dir, exist_ok=True)
        self.png = os.path.join(self.dir, "ref.png")
        _mini_png(self.png, 80, 50)
        self.doc = App.newDocument("refimg")

    def tearDown(self):
        try:
            App.closeDocument(self.doc.Name)
        except Exception:
            pass

    def test_create_and_attach(self):
        obj = create_reference_image(self.doc, self.png, plane="XZ")
        self.assertEqual(image_size(self.png), (80, 50))
        self.assertEqual(obj.RefImagePlane, "XZ")
        self.assertEqual(obj.RefImageSource, os.path.abspath(self.png))
        self.assertEqual(obj.XSize, 80.0)
        set_image_plane(obj, "YZ")
        self.assertEqual(obj.RefImagePlane, "YZ")

    def test_world_width_and_calibration(self):
        obj = create_reference_image(self.doc, self.png, plane="XY")
        set_world_width(obj, 160.0)
        self.assertAlmostEqual(obj.XSize, 160.0)
        self.assertAlmostEqual(obj.YSize, 100.0)
        mm = calibrate_from_two_points(obj, (0, 0), (40, 0), 80.0)
        self.assertAlmostEqual(mm, 2.0)
        self.assertAlmostEqual(obj.XSize, 160.0)
        self.assertAlmostEqual(obj.YSize, 100.0)

    def test_opacity_lock_visibility(self):
        obj = create_reference_image(self.doc, self.png)
        set_transparency(obj, 0.5)
        self.assertAlmostEqual(obj.RefImageOpacity, 0.5)
        set_locked(obj, True)
        self.assertTrue(obj.RefImageLocked)
        with self.assertRaises(RefImageError):
            set_world_width(obj, 300.0)
        set_locked(obj, False)
        set_world_width(obj, 300.0)
        set_visibility(obj, False)
        self.assertAlmostEqual(obj.XSize, 300.0)

    def test_errors(self):
        with self.assertRaises(RefImageError):
            create_reference_image(self.doc, "/no/such/file.png")


if __name__ == "__main__":
    unittest.main(verbosity=2)
