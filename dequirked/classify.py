# dequirked/classify.py
import json, re
from pathlib import Path
from typing import Dict, List, Tuple
from .engine import QuirkTranslator

def score_text_against_profile(text: str, compiled_rules: List[Tuple[re.Pattern, str]]) -> float:
    score = 0.0
    for rx, _ in compiled_rules:
        matches = rx.findall(text)
        if not matches:
            continue
        pat_len = max(1, len(rx.pattern))
        score += pat_len * len(matches)
    return score


class LineWiseDetector:
    def __init__(self, translator: QuirkTranslator):
        self.t = translator
        # Preload compiled rules for scoring
        self._compiled_by_profile: Dict[str, List[Tuple[re.Pattern, str]]] = {
            name: self.t.load_profile(name)["_compiled_rules"]
            for name in self.t.profiles
        }
        # Build tag-hint regexes from each profile's "tags": ["UK", "Murrit", "Executive"]
        self._tag_regexes: List[Tuple[re.Pattern, str]] = []
        for name in self.t.profiles:
            data = self.t.load_profile(name)
            for tag in data.get("tags", []):
                # ^\s*TAG:\s*  (case-insensitive; tag may contain non-word chars)
                rx = re.compile(r"^\s*" + re.escape(tag) + r":\s*", re.IGNORECASE)
                self._tag_regexes.append((rx, name))

    def detect_profile_for_line(self, line: str) -> str:
        # 1) Tag hints win if any match
        for rx, prof in self._tag_regexes:
            if rx.search(line):
                return prof

        # 2) Otherwise score by rule matches
        best_profile, best_score = "generic_leet", 0.0
        for name, comp in self._compiled_by_profile.items():
            s = score_text_against_profile(line, comp)
            if s > best_score:
                best_profile, best_score = name, s

        # 3) If nothing matches, default to generic (avoids random mislabels)
        if best_score == 0.0:
            return "generic_leet"
        return best_profile

    def translate_block_auto(self, text: str) -> Dict:
        lines = text.splitlines()
        out_lines: List[str] = []
        meta: List[Dict] = []
        for i, line in enumerate(lines):
            if not line.strip():
                out_lines.append(line)
                meta.append({"line": i, "profile": None, "input": line, "output": line})
                continue
            prof = self.detect_profile_for_line(line)
            translated = self.t.apply_profile_once(line, prof)
            out_lines.append(translated)
            meta.append({"line": i, "profile": prof, "input": line, "output": translated})
        return {"text": "\n".join(out_lines), "lines": meta}

    def explain_block(self, text: str) -> Dict:
        lines = text.splitlines()
        out_lines = []
        details = []
        for i, line in enumerate(lines):
            if not line.strip():
                out_lines.append(line)
                details.append({"line": i, "profile": None, "rule_counts": []})
                continue
            prof = self.detect_profile_for_line(line)
            translated, counts = self.t.apply_with_counts(line, prof)
            out_lines.append(translated)
            details.append({"line": i, "profile": prof, "rule_counts": counts})
        return {"text": "\n".join(out_lines), "details": details}
