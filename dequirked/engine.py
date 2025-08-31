import json, re, unicodedata
from pathlib import Path
from typing import List, Dict, Tuple

TAG_MACRO = r'((?:\s*[\w\-]{1,30}:\s*)?)'


class QuirkTranslator:
    def __init__(self, rules_dir: str = "rules"):
        self.rules_dir = Path(rules_dir)
        self._cache = {}
        self._profiles = None

    @property
    def profiles(self):
        if self._profiles is None:
            names = []
            for p in self.rules_dir.glob("*.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "rules" in data and isinstance(data["rules"], list):
                        names.append(p.stem)
                except Exception:
                    pass
            self._profiles = names
        return self._profiles
    
    def load_profile(self, name: str):
        if name in self._cache:
            return self._cache[name]
        fp = self.rules_dir / f"{name}.json"
        data = json.loads(fp.read_text(encoding="utf-8"))

        compiled = []
        for pat, repl in data["rules"]:
            # Macro expansion
            pat = pat.replace("@TAG", TAG_MACRO)
            compiled.append((re.compile(pat), repl))
        data["_compiled_rules"] = compiled

        self._cache[name] = data
        return data
    
    def apply_extra_post(self, text: str, steps: list[str]) -> str:
        # Reuse the same internal logic
        return self._postprocess(text, steps)


    def _postprocess(self, text: str, steps: list[str]) -> str:
        for s in steps or []:
            if s == "collapse_whitespace":
                text = re.sub(r"\s+", " ", text).strip()
            elif s == "nfkc":
                text = unicodedata.normalize("NFKC", text)
            elif s == "sentence_case":
                # Sentence-case each line, preserving speaker tags like "GC:" and
                # capitalizing the first alphabetic letter even if punctuation (e.g., '*') comes first.
                def fix_line(line: str) -> str:
                    # Pull out optional speaker tag "ABC:" (1-4 letters) at start of line
                    m = re.match(r'^(\s*[A-Za-z]{1,4}:\s*)(.*)$', line)
                    prefix, body = (m.group(1), m.group(2)) if m else ("", line)

                    # Lowercase body, then capitalize first alphabetic char at start or after .?! + space
                    b = body.lower()

                    # Capitalize the first alphabetic character, skipping leading non-letters (e.g., '*')
                    def cap_after_sentence(s: str) -> str:
                        # start-of-string or after .?! + whitespace
                        pattern = r'(^|[\.!\?]\s+)([^A-Za-z]*)([a-z])'
                        return re.sub(pattern,
                                      lambda m: m.group(1) + m.group(2) + m.group(3).upper(),
                                      s)

                    b = cap_after_sentence(b)

                    # Capitalize standalone pronoun "i"
                    b = re.sub(r'\bi\b', 'I', b)

                    return prefix + b

                text = "\n".join(fix_line(ln) for ln in text.splitlines())
        return text

    def apply_profile_once(self, text: str, profile: str) -> str:
        data = self.load_profile(profile)
        out = text
        for rx, repl in data["_compiled_rules"]:
            out = rx.sub(repl, out)
        return self._postprocess(out, data.get("postprocessors", []))

    def translate(self, text: str, profile: str | None = None) -> str:
        """If profile is None, caller should do detection per line."""
        if profile:
            return self.apply_profile_once(text, profile)
        return text  # unchanged if not specified

    def apply_with_counts(self, text: str, profile: str) -> Tuple[str, list[tuple[str,int]]]:
        data = self.load_profile(profile)
        counts: list[tuple[str,int]] = []
        out = text
        for rx, repl in data["_compiled_rules"]:
            n = 0
            def _count_sub(m):
                nonlocal n
                n += 1
                return repl
            out = rx.sub(_count_sub, out)
            if n:
                counts.append((rx.pattern, n))
        out = self._postprocess(out, data.get("postprocessors", []))
        return out, counts
