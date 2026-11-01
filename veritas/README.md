# VERITAS — Academic QA Gateway

Closed-corpus academic question answering over course PDFs. PyMuPDF extracts
page-local chunks, MiniLM produces normalized 384-dimensional embeddings, and
FAISS IndexFlatIP retrieves evidence. A maximum-similarity threshold gates
extractive answer synthesis. The React interface displays answers, refusals,
and page-level source cards.

## Prerequisites

- Python 3.11 or newer, with a compatible PyTorch installation.
- Node.js 22.12 or newer and npm.
- Internet access for Python/npm installation and the first MiniLM download.
- Text-based course PDFs; the ingestion layer does not perform OCR.

Commands below use Windows PowerShell. Start in the repository root, `veritas/`,
unless another directory is specified.

## Backend setup

```powershell
Set-Location backend
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy course PDFs into `backend/data/pdfs/`. From `backend/`, build the index:

```powershell
.\venv\Scripts\python.exe scripts/build_index.py
```

This creates `data/index/faiss.index` and `data/index/chunks.json`. The first
embedding run downloads `sentence-transformers/all-MiniLM-L6-v2`. Rebuilding
replaces the index using every matching PDF currently in `data/pdfs/`.

On macOS/Linux, the equivalent environment setup from the repository root is:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/build_index.py
```

## Frontend setup

From the repository root:

```powershell
Set-Location frontend
npm install
npm run build
```

## Run the current single-server setup

If the local startup fix has installed `start-veritas.ps1`, use this command
from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-veritas.ps1
```

The launcher builds the frontend with a same-origin API URL and starts the
backend. After `Application startup complete`, open
<http://127.0.0.1:8000>. Keep the terminal running. This mode uses one server;
Vite does not need to run alongside it. Restart the launcher after frontend
edits or an index rebuild. API documentation is at
<http://127.0.0.1:8000/docs> and health is at
<http://127.0.0.1:8000/health>.

The static frontend mount must remain after all API router registrations in
`backend/app/main.py`. Otherwise it can intercept API routes.

## Run separate development servers

Backend terminal, from `backend/`:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal, from `frontend/`:

```powershell
$env:VITE_API_URL = "http://127.0.0.1:8000"
npm run dev -- --host localhost --port 5187 --strictPort
```

Open <http://localhost:5187>. Ensure `CORS_ORIGINS` includes
`http://localhost:5187` and `http://127.0.0.1:5187` when using this port.
The standard `npm run dev` command uses the Vite configuration's default port;
the explicit flags above keep this project's port predictable.

## Demo login

- Username: `divyansh`
- Password: `admin123`

Start testing with top-k `5` and threshold `0.35`. A similarity score is not a
probability of correctness. Recalibrate against questions matched to the PDFs.

## Tests

From `backend/`, run every backend test:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

Run the fast tests without the real-model integration file:

```powershell
.\venv\Scripts\python.exe -m pytest -v --ignore=tests/test_retriever.py
```

Run only the Phase 6 tests:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_hardening.py tests/test_index_rebuild.py -v
```

Shared API fixtures install a fresh FakeRetriever per test. TestClient is
created without a context manager, so application lifespan does not run.
The fixture also rejects accidental real Retriever construction. Monkeypatch
restores application state and patched symbols during teardown. Existing
module-local fixtures in `test_api.py` retain their normal pytest precedence.

The rebuild test uses deterministic unit vectors in place of model embeddings
but exercises real FAISS creation, persistence, reload, and search. It verifies
replacement of both vector rows and chunk metadata; it does not measure semantic
retrieval quality. `test_retriever.py` provides real MiniLM integration coverage
and may access the model service unless its cache is used in offline mode.
Tests generate their own data and do not require the course PDFs or a saved
course index.

From `frontend/`, verify TypeScript and the production build:

```powershell
npm run build
```

For Bash with an activated backend venv, the complete check from the repository
root is:

```bash
cd backend && pytest -v && cd ../frontend && npm run build
```

These Python tests do not execute the browser's Axios interceptors or React
components. Manually verify login failure, answered/refused states, source
expansion, and sign-out clearing. To check session expiry, replace
`veritas_token` with an invalid value in browser storage and submit a question;
the API should return 401 and the frontend should clear the session.

## Adding PDFs and calibrating tau

Stop the running backend with Ctrl+C before replacing its index. From
`backend/`, after adding or removing PDFs:

```powershell
.\venv\Scripts\python.exe scripts/build_index.py
.\venv\Scripts\python.exe scripts/calibrate.py
```

Edit `tests/eval_set.json` first: in-scope questions must actually be answerable
from the loaded PDFs. Calibration prints score statistics and sweeps thresholds
from 0.20 through 0.95. It maximizes in-scope recall plus out-of-scope rejection,
breaking ties toward the higher threshold. It does not modify `DEFAULT_TAU`.
Use a separate held-out question set to assess the selected threshold.

Restart the backend or single-server launcher afterward. A Retriever already
loaded in memory continues using its old index until it is reloaded.

## Known limitations

- Authentication is a demo-only, hard-coded mock. Replace it with a real identity
  system and secure password handling before any deployment.
- Set `VERITAS_JWT_SECRET` in the backend environment before deployment; never
  deploy with the `dev-only-change-me` fallback. Use a stable, randomly generated
  secret of at least 32 bytes, keep it outside source control, and use the hosting
  platform's secret management. Changing it invalidates existing tokens.
- For local Windows use, generate and persist a secret once from `backend/`:

  ```powershell
  $jwtSecret = & ".\venv\Scripts\python.exe" -c "import secrets; print(secrets.token_hex(32))"
  [Environment]::SetEnvironmentVariable("VERITAS_JWT_SECRET", $jwtSecret, "User")
  $env:VERITAS_JWT_SECRET = $jwtSecret
  ```

  Restart the backend to apply it. Do not regenerate the secret on every start.
  Short-key warnings may appear while tests use the development fallback.
- Max-cosine gating is a heuristic. Generic in-corpus phrasing can pass the gate
  even when the requested answer is unsupported. Higher thresholds can also
  reject valid questions. Passing the gate does not guarantee answer correctness.
- IndexFlatIP is an exact, linear-search index suited to corpora on the order of
  roughly 100,000 chunks, depending on hardware and latency requirements. Larger
  corpora and higher concurrency require benchmarking and possibly another index.
- Answers are extractive sentence selections, not LLM-generated explanations.
  PDF extraction order and sentence splitting can affect readability.
- Scanned pages without extractable text are skipped. The current explicit
  AKGEC footer filter is corpus-specific; different footers are not automatically
  removed by that filter.
- Index and JSON files are written separately, not as an atomic pair. Build
  offline and restart the service rather than rebuilding under live traffic.
- The bundled 40-question calibration set is a starter tuning set, not evidence
  of general accuracy or hallucination prevention.