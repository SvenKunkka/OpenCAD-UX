# -*- coding: utf-8 -*-
"""Shortcut conflict detection (pure logic, unit-testable).

A shortcut string uses Qt-ish notation: ``L``, ``Shift+F``, ``Delete``,
``Esc``, ``mod+Z`` ... where ``mod`` means *Ctrl on Windows/Linux and Command
on macOS*.  Conflicts are computed per concrete platform so a preset that is
safe on one platform is reported accurately.
"""

MOD_KEY = "mod"

WORLDS = ("any", "win/linux", "mac")


def expand_keys(key):
    """Expand a shortcut into concrete platform forms.

    Returns [(world, concrete_key), ...].  Keys without a mod component are
    identical on every platform and get the pseudo world "any".
    """
    parts = [p for p in key.split("+") if p.strip()]
    if MOD_KEY not in parts:
        return [("any", key.strip())]
    rest = "+".join(p for p in parts if p != MOD_KEY)
    return [("win/linux", "Ctrl+" + rest), ("mac", "Meta+" + rest)]


def normalize_key(key):
    return "+".join(p.strip().lower() for p in key.split("+") if p.strip())


def _worlds_of(key):
    for world, concrete in expand_keys(key):
        if world == "any":
            yield "any", concrete
            # non-mod keys also collide with concrete ctrl/meta bindings
            yield "win/linux", concrete
            yield "mac", concrete
        else:
            yield world, concrete


def internal_conflicts(entries):
    """Duplicate bindings *inside* one preset (same action self-aliases from
    the 'any' world expansion are ignored)."""
    out = []
    seen = {}
    for e in entries:
        if not e.key:
            continue
        for world, concrete in _worlds_of(e.key):
            nk = normalize_key(concrete)
            prev = seen.get(nk)
            if prev is None:
                seen[nk] = (e.action, e.key)
            elif prev != (e.action, e.key):
                out.append({"entry_action": e.action, "entry_key": e.key,
                            "other_action": prev[0], "other_key": concrete,
                            "platform": world})
    return out


def external_conflicts(preset_entries, other_shortcuts=None, platform=None):
    """Conflicts between a preset and existing bindings."""
    if not other_shortcuts:
        return []
    out = []
    preset_by = {}
    for e in preset_entries:
        if not e.key:
            continue
        for world, concrete in _worlds_of(e.key):
            if platform and world not in (platform, "any"):
                continue
            preset_by.setdefault(world, {}).setdefault(
                normalize_key(concrete), (e.action, e.key))
    for action, key in other_shortcuts.items():
        if not key:
            continue
        for world, concrete in _worlds_of(key):
            if platform and world not in (platform, "any"):
                continue
            nk = normalize_key(concrete)
            hit = preset_by.get(world, {}).get(nk)
            if hit and hit[0] != action:
                out.append({"entry_action": hit[0], "entry_key": hit[1],
                            "other_action": action, "other_key": concrete,
                            "platform": world})
    return out


def find_conflicts(preset_entries, other_shortcuts=None, platform=None):
    seen = set()
    out = []
    for r in (internal_conflicts(preset_entries) + external_conflicts(
            preset_entries, other_shortcuts, platform)):
        key = (r["entry_action"], r["other_action"], r["platform"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def summarize_conflicts(results):
    if not results:
        return "No shortcut conflicts detected."
    lines = ["Shortcut conflicts:"]
    for r in results:
        lines.append("  %s (%s) <-> %s (%s)  [%s]"
                     % (r["entry_action"], r["entry_key"],
                        r["other_action"], r["other_key"], r["platform"]))
    return "\n".join(lines)
