from dequirked.engine import QuirkTranslator
from dequirked.classify import LineWiseDetector

def test_explain_counts_and_caps():
    t = QuirkTranslator("rules")
    d = LineWiseDetector(t)
    src = "GC: *GC L4NDS ON YOUR WH3LP1NG STOOP*\nGC: *4ND ONC3 W1TH H3R M1GHTY SNOUT*"
    explained = d.explain_block(src)
    assert explained["text"]  # translated text present
    # at least some rules should have fired
    some = sum(c for _, c in explained["details"][0]["rule_counts"]) > 0
    assert some
