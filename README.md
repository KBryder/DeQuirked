# DeQuirked

Normalize quirked dialogue (e.g., Homestuck / Vast Error) into screen-reader-friendly text.

## Quick start
## Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8080
# open http://localhost:8080/
