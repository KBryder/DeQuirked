# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dequirked.engine import QuirkTranslator
from dequirked.classify import LineWiseDetector
from typing import List

app = FastAPI(title="DeQuirked API", version="0.1.1")

# CORS: safe to keep permissive during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Core services
t = QuirkTranslator(rules_dir="rules")
detector = LineWiseDetector(t)

class TranslateRequest(BaseModel):
    text: str
    profile: str | None = None
    auto_detect: bool = True
    normalize_caps: bool = False 

class LineOut(BaseModel):
    line: int
    profile: str | None
    input: str
    output: str

class TranslateResponse(BaseModel):
    translated: str
    detected_profiles: list[LineOut]

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if req.auto_detect or not req.profile:
        result = detector.translate_block_auto(req.text)
        out_text = result["text"]
        if req.normalize_caps:
            out_text = t.apply_extra_post(out_text, ["sentence_case"])
        return TranslateResponse(
            translated=out_text,
            detected_profiles=[LineOut(**d) for d in result["lines"]]
        )
    else:
        out_text = t.translate(req.text, req.profile)
        if req.normalize_caps:
            out_text = t.apply_extra_post(out_text, ["sentence_case"])
        return TranslateResponse(translated=out_text, detected_profiles=[])


class ProfilesResponse(BaseModel):
    profiles: List[str]

@app.get("/profiles", response_model=ProfilesResponse)
def list_profiles():
    return ProfilesResponse(profiles=t.profiles)

# Serve the UI (so visiting http://localhost:8080/ opens the app)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

class RuleCount(BaseModel):
    pattern: str
    count: int

class ExplainLine(BaseModel):
    line: int
    profile: str | None
    rule_counts: list[RuleCount]

class ExplainResponse(BaseModel):
    translated: str
    details: list[ExplainLine]

@app.post("/translate_explain", response_model=ExplainResponse)
def translate_explain(req: TranslateRequest):
    # normalize_caps applies after profile-specific postprocessors
    result = detector.explain_block(req.text)
    out_text = result["text"]
    if req.normalize_caps:
        out_text = t.apply_extra_post(out_text, ["sentence_case"])
    return ExplainResponse(
        translated=out_text,
        details=[
            ExplainLine(
                line=d["line"],
                profile=d["profile"],
                rule_counts=[RuleCount(pattern=p, count=c) for p, c in d["rule_counts"]]
            )
            for d in result["details"]
        ]
    )
