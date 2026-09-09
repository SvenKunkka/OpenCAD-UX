# -*- coding: utf-8 -*-
"""Canonical -> display names for ids that are not ribbon buttons."""

EXTRA = {
    "pocket": ("Pocket", "凹槽/挖槽"),
    "edit_sketch": ("Edit Sketch", "编辑草图"),
    "calibrate_ref_image": ("Calibrate Image", "校准图片"),
    "ref_image_transparency": ("Transparency", "透明度"),
    "ref_image_lock": ("Lock Image", "锁定图片"),
    "ref_image_hide": ("Hide/Show Image", "隐藏/显示图片"),
    "command_search": ("Command Search", "命令搜索"),
    "context_actions": ("Context Actions", "上下文操作"),
    "settings": ("Settings", "设置"),
    "help_about": ("About OpenCAD UX", "关于"),
    "calibrate": ("Calibrate", "校准"),
    "selftest": ("GUI Self-test", "界面自检"),
    "product-design": ("Product Design", "产品设计"),
}


def resolve_label(canonical, lang="en"):
    pair = EXTRA.get(canonical)
    if pair:
        return pair[1] if lang == "zh" else pair[0]
    return None


def resolve_icon(canonical):
    """Icon asset name for a canonical id (fallback: the id itself)."""
    return canonical
