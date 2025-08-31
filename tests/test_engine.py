from dequirked.engine import QuirkTranslator
from dequirked.classify import LineWiseDetector

def test_generic_replacements():
    t = QuirkTranslator("rules")
    s = t.translate("H3LL0 W0RLD \\)\\(", "generic_leet")
    assert "HELLO WORLD h" in s or "hello world h" in s

def test_linewise_detection():
    t = QuirkTranslator("rules")
    d = LineWiseDetector(t)
    text = ")(3R3Z1 15 4W350M3\nK4RK4T 15 L0UD"
    out = d.translate_block_auto(text)
    assert len(out["lines"]) == 2
    assert out["text"]
