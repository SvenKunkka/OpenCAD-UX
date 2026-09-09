# -*- coding: utf-8 -*-
"""Reference image workflow (import/attach/calibrate/transparency/lock).

FreeCAD ships ``Image::ImagePlane`` objects (public API) which we use as the
backing object, so nothing here requires the Image workbench UI or any third
party library.  Plane attachment is implemented through the object Placement
(original logic; Fusion-style plane names used only as *labels*).
"""

import math
import os
import struct


class RefImageError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# image pixel dimensions without external dependencies
# ---------------------------------------------------------------------------

def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if not head.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    if head[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return int(w), int(h)


def jpeg_size(path):
    with open(path, "rb") as fh:
        data = fh.read(2 ** 16)
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xD9 or marker == 0xDA:
            return None
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9,
                      0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return int(w), int(h)
        i += 2 + length
    return None


def image_size(path):
    if not os.path.isfile(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext == ".png":
        return png_size(path)
    if ext in (".jpg", ".jpeg"):
        return jpeg_size(path)
    return None


# ---------------------------------------------------------------------------
# plane helpers (original placement math)
# ---------------------------------------------------------------------------

PLANE_INFO = {
    "XY": {"en": "XY (top view)", "zh": "XY (俯视图)"},
    "XZ": {"en": "XZ (front view)", "zh": "XZ (前视图)"},
    "YZ": {"en": "YZ (right view)", "zh": "YZ (右视图)"},
}


def plane_placement(plane, center=(0, 0, 0)):
    """Placement orienting the image on the given plane.

    The ImagePlane default lies in the global XY plane.  XZ = rotate -90 deg
    about X; YZ = rotate +90 deg about Y.
    """
    import FreeCAD as App  # noqa

    rot = App.Rotation()
    if plane == "XY":
        pass
    elif plane == "XZ":
        rot = App.Rotation(App.Vector(1, 0, 0), -90.0)
    elif plane == "YZ":
        rot = App.Rotation(App.Vector(0, 1, 0), 90.0)
    else:
        raise RefImageError("unknown plane '%s' (use XY, XZ or YZ)" % plane)
    return App.Placement(App.Vector(*center), rot)


# ---------------------------------------------------------------------------
# calibration (pure math: pixels <-> millimetres)
# ---------------------------------------------------------------------------

def scale_from_pixels(p1_px, p2_px, real_distance_mm):
    """mm per pixel from two image points and a known real distance."""
    dx = p2_px[0] - p1_px[0]
    dy = p2_px[1] - p1_px[1]
    px_dist = math.hypot(dx, dy)
    if px_dist <= 0:
        raise RefImageError("the two calibration points coincide")
    if real_distance_mm <= 0:
        raise RefImageError("the known distance must be > 0")
    return real_distance_mm / px_dist


def dimensions_from_calibration(img_px_w, img_px_h, mm_per_px):
    return img_px_w * mm_per_px, img_px_h * mm_per_px


# ---------------------------------------------------------------------------
# document level API (works headless; GUI commands wrap these)
# ---------------------------------------------------------------------------

def create_reference_image(doc, image_path, name=None, plane="XY",
                           world_width_mm=None):
    """Create an ImagePlane-backed reference image attached to ``plane``."""
    if not os.path.isfile(image_path):
        raise RefImageError("image file not found: %s" % image_path)
    size = image_size(image_path)
    if size is None:
        raise RefImageError("unsupported/unknown image format (PNG/JPEG only): %s"
                            % image_path)
    obj = doc.addObject("Image::ImagePlane", name or "RefImage")
    obj.ImageFile = image_path
    px_w, px_h = size
    if world_width_mm and world_width_mm > 0:
        xsize = float(world_width_mm)
        ysize = float(world_width_mm) * px_h / px_w
    else:
        xsize = float(px_w)   # default 1 px = 1 mm until calibrated
        ysize = float(px_h)
    obj.XSize = xsize
    obj.YSize = ysize
    obj.Placement = plane_placement(plane)
    obj.addProperty("App::PropertyString", "RefImagePlane", "OpenCADUX",
                    "Attached plane id").RefImagePlane = plane
    obj.addProperty("App::PropertyString", "RefImageSource", "OpenCADUX",
                    "Original file").RefImageSource = os.path.abspath(image_path)
    obj.addProperty("App::PropertyBool", "RefImageLocked", "OpenCADUX",
                    "Locked against edits").RefImageLocked = False
    obj.addProperty("App::PropertyFloat", "RefImageOpacity", "OpenCADUX",
                    "Opacity 0..1").RefImageOpacity = 1.0
    obj.addProperty("App::PropertyFloat", "RefImageDrawOrder", "OpenCADUX",
                    "Draw-order hint (larger on top)").RefImageDrawOrder = 0.0
    doc.recompute()
    _apply_view_state(obj, opacity=1.0, visible=True)
    return obj


def _apply_view_state(obj, opacity=None, visible=None):
    try:
        vo = obj.ViewObject
    except Exception:
        return
    if vo is None:
        return
    try:
        if opacity is not None and hasattr(vo, "Transparency"):
            vo.Transparency = int(round((1.0 - float(opacity)) * 100))
    except Exception:
        pass
    try:
        if visible is not None and hasattr(vo, "Visibility"):
            vo.Visibility = bool(visible)
    except Exception:
        pass


def set_image_plane(obj, plane):
    if getattr(obj, "RefImageLocked", False):
        raise RefImageError("image is locked; unlock it first")
    obj.Placement = plane_placement(plane)
    obj.RefImagePlane = plane
    return True


def set_transparency(obj, opacity):
    """opacity 0..1 (1 fully opaque)."""
    if not (0.0 <= float(opacity) <= 1.0):
        raise RefImageError("opacity must be between 0 and 1")
    if getattr(obj, "RefImageLocked", False):
        raise RefImageError("image is locked; unlock it first")
    obj.RefImageOpacity = float(opacity)
    _apply_view_state(obj, opacity=float(opacity))
    return True


def set_locked(obj, locked):
    obj.RefImageLocked = bool(locked)
    return bool(locked)


def set_visibility(obj, visible):
    _apply_view_state(obj, visible=bool(visible))
    return bool(visible)


def calibrate_from_two_points(obj, p1_px, p2_px, real_distance_mm):
    """Resize the image so the pixel distance between two picked points equals
    ``real_distance_mm`` (points in image-pixel space; GUI converts clicks)."""
    if getattr(obj, "RefImageLocked", False):
        raise RefImageError("image is locked; unlock it first")
    mm_per_px = scale_from_pixels(p1_px, p2_px, real_distance_mm)
    size = image_size(obj.RefImageSource) or (obj.XSize, obj.YSize)
    obj.XSize, obj.YSize = dimensions_from_calibration(size[0], size[1], mm_per_px)
    return mm_per_px


def set_world_width(obj, world_width_mm):
    """Rescale keeping aspect ratio using the original pixel size."""
    if getattr(obj, "RefImageLocked", False):
        raise RefImageError("image is locked; unlock it first")
    if world_width_mm <= 0:
        raise RefImageError("width must be > 0")
    size = image_size(obj.RefImageSource) or (obj.XSize, obj.YSize)
    ratio = size[1] / size[0]
    obj.XSize = float(world_width_mm)
    obj.YSize = float(world_width_mm) * ratio
    return True
