import json, re, sys
from pathlib import Path

RULES_DIR = Path("rules")

def main() -> int:
    ok = True
    for fp in sorted(RULES_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[JSON] {fp.name}: {e}")
            ok = False
            continue

        if "name" not in data or "rules" not in data:
            print(f"[SCHEMA] {fp.name}: missing 'name' or 'rules'")
            ok = False
            continue

        # compile regex patterns
        for i, pair in enumerate(data["rules"]):
            try:
                pat, repl = pair
            except Exception:
                print(f"[SCHEMA] {fp.name} rule #{i}: not a [pattern, replacement] pair")
                ok = False
                continue
            try:
                re.compile(pat)
            except re.error as e:
                print(f"[REGEX] {fp.name} rule #{i}: {pat!r} -> {e}")
                ok = False

        # optional tags sanity
        for tag in data.get("tags", []):
            if ":" in tag:
                print(f"[TAGS] {fp.name}: tag '{tag}' should be bare (no colon)")
                ok = False

    print("OK" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
