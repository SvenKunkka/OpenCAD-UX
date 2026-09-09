# -*- coding: utf-8 -*-
"""Bilingual fuzzy command search engine (pure logic).

English queries are matched with a subsequence/prefix fuzzy scorer; Chinese
queries use exact substring on the Chinese labels and keywords (a full pinyin
index needs a dictionary dependency we intentionally avoid - documented).
"""

import json
import os
import time

from .. import config


def normalize(q):
    return (q or "").strip().lower()


def subsequence_score(query, text):
    """Returns a score for ``query`` as a subsequence of ``text`` (0 = none).

    Prefers prefix and word-boundary hits, falls back to plain subsequence.
    """
    q = normalize(query)
    t = normalize(text)
    if not q or not t:
        return 0.0
    if q == t:
        return 100.0
    if t.startswith(q):
        return 90.0
    if " " in t and any(part.startswith(q) for part in t.split(" ")):
        return 80.0
    # subsequence with early-position bonus
    pos = -1
    dist = 0
    for ch in q:
        nxt = t.find(ch, pos + 1)
        if nxt < 0:
            return 0.0
        if pos >= 0:
            dist += nxt - pos - 1
        pos = nxt
    base = 55.0
    return max(1.0, base - dist)


class SearchIndex(object):
    def __init__(self, items=None, recents_path=None):
        """items: list of dicts:
        {id, canonical, label_en, label_zh, keywords[], group, group_en,
         group_zh, icon, shortcut, enabled}
        """
        self.items = items or []
        self.recents_path = recents_path or os.path.join(
            config.user_data_dir(), "command_recents.json")

    # -- recents ----------------------------------------------------------
    def _read_recents(self):
        try:
            with open(self.recents_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write_recents(self, recents):
        try:
            with open(self.recents_path, "w", encoding="utf-8") as fh:
                json.dump(recents[:40], fh)
        except OSError:
            pass

    def record_use(self, item_id):
        recents = self._read_recents()
        recents = [r for r in recents if r.get("id") != item_id]
        recents.insert(0, {"id": item_id, "ts": time.time()})
        self._write_recents(recents)

    def recent_ids(self):
        return [r.get("id") for r in self._read_recents()]

    # -- query ------------------------------------------------------------
    def search(self, query, limit=12, only_enabled=True):
        q = normalize(query)
        if not q:
            return [i for i in self.items if not only_enabled or i.get("enabled", True)][:limit]
        scored = []
        for item in self.items:
            if only_enabled and not item.get("enabled", True):
                continue
            best = 0.0
            best_kind = None
            if _is_cjk(q):
                # CJK: substring on zh label + keywords (pinyin not supported)
                cands = [item.get("label_zh", ""), item.get("group_zh", "")] + \
                        [k for k in item.get("keywords", []) if _is_cjk(k)]
                for c in cands:
                    if q in (c or "").lower():
                        ln = len(q) / max(1, len(c))
                        best = max(best, 60.0 + 30.0 * ln)
                        best_kind = "zh"
                if best == 0:
                    continue
            else:
                texts = [(item.get("label_en", ""), 1.0),
                         (item.get("group_en", ""), 0.4)]
                for k in item.get("keywords", []):
                    if not _is_cjk(k):
                        texts.append((k, 0.8))
                for text, weight in texts:
                    s = subsequence_score(q, text)
                    if s:
                        best = max(best, s * weight)
                        best_kind = "en"
            if best > 0:
                scored.append((best, item, best_kind))
        scored.sort(key=lambda x: (-x[0], x[1].get("label_en", "")))
        # recency boost: +6 for each recent rank position (1st strongest)
        recents = self.recent_ids()
        ranked = []
        for score, item, kind in scored:
            try:
                boost = max(0, 6 - recents.index(item.get("id")) * 2)
            except ValueError:
                boost = 0
            ranked.append((score + boost, item, kind))
        ranked.sort(key=lambda x: (-x[0], x[1].get("label_en", "")))
        return [r[1] for r in ranked[:limit]]


def _is_cjk(text):
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)
