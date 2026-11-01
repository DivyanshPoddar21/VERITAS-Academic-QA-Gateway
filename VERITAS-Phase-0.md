# VERITAS Phase 0

Requires Python 3.11+ and Node.js 22.12+ with npm.

## Windows PowerShell (from veritas/)

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..
```

If activation is disabled, invoke `venv\Scripts\python.exe` directly instead of `python`.

## macOS/Linux (from veritas/)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..
```

## Create the frontend (from veritas/, only if frontend/ does not exist)

```bash
npm create vite@9.3.1 frontend -- --template react-ts --no-interactive
cd frontend
npm install
npm install tailwindcss@4 @tailwindcss/vite@4 axios
cd ..
```

Then replace the application files with the complete contents below. No tailwind.config.js is needed.

The archive already contains the frontend and its package-lock.json. When using the archive, install with these commands instead:

```bash
cd frontend
npm ci
cd ..
```

## Run backend (from veritas/backend/, venv active)

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run frontend (separate terminal, from veritas/frontend/)

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

## Verify (from veritas/, venv active, Bash or PowerShell 7+)

```bash
cd backend && python -c "from app.main import app; from app import config; print(app.title, config.INDEX_DIR)" && cd ../frontend && npm run build
```

PowerShell 5.1 does not support `&&`; run each command separately and stop if any fails.

Verification performed: backend import, health response, CORS preflight, resolved directory paths, exact public configuration exports, and frontend production build all passed. Python 3.12 was used. Only FastAPI, uvicorn[standard], and httpx were installed for backend verification; the complete RAG dependency set is declared but was not installed or exercised in Phase 0.

## Complete files

All __init__.py and .gitkeep files are empty (zero bytes). The generated npm lockfile is included in the archive.

### veritas/.gitignore

```text
venv/
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
node_modules/
dist/
.env
backend/data/index/*
!backend/data/index/.gitkeep
backend/data/pdfs/*
!backend/data/pdfs/.gitkeep
```

### veritas/backend/app/__init__.py

```python
```

### veritas/backend/app/config.py

```python
"""Shared configuration for the VERITAS backend."""

import os as _os
from pathlib import Path as _Path

BASE_DIR: _Path = _Path(__file__).resolve().parent.parent
PDF_DIR: _Path = BASE_DIR / "data" / "pdfs"
INDEX_DIR: _Path = BASE_DIR / "data" / "index"
MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM: int = 384
WINDOW_WORDS: int = 180
STRIDE_WORDS: int = 120
MIN_CHUNK_WORDS: int = 30
TAU_MIN: float = 0.20
TAU_MAX: float = 0.95
DEFAULT_TAU: float = 0.35
DEFAULT_TOP_K: int = 5
JWT_SECRET: str = _os.environ.get("VERITAS_JWT_SECRET", "dev-only-change-me")
JWT_ALGO: str = "HS256"
TOKEN_TTL_HOURS: int = 2
CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
```

### veritas/backend/app/main.py

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.routers.health import router as health_router

app: FastAPI = FastAPI(title="VERITAS — Academic QA Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
```

### veritas/backend/app/routers/__init__.py

```python
```

### veritas/backend/app/routers/health.py

```python
"""Health endpoint for the VERITAS service."""

from fastapi import APIRouter

router: APIRouter = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "veritas"}
```

### veritas/backend/app/services/__init__.py

```python
```

### veritas/backend/data/index/.gitkeep

```text
```

### veritas/backend/data/pdfs/.gitkeep

```text
```

### veritas/backend/pytest.ini

```ini
[pytest]
testpaths = tests
pythonpath = .
```

### veritas/backend/requirements.txt

```text
fastapi
uvicorn[standard]
pymupdf
sentence-transformers
faiss-cpu
numpy
pyjwt
python-multipart
pydantic
pytest
httpx
```

### veritas/backend/scripts/.gitkeep

```text
```

### veritas/backend/tests/__init__.py

```python
```

### veritas/frontend/.gitignore

```text
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
```

### veritas/frontend/.oxlintrc.json

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

### veritas/frontend/index.html

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>VERITAS — Academic QA Gateway</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### veritas/frontend/package.json

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "oxlint",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tailwindcss/vite": "^4.3.3",
    "axios": "^1.20.0",
    "react": "^19.3.1",
    "react-dom": "^19.3.1",
    "tailwindcss": "^4.3.3"
  },
  "devDependencies": {
    "@types/node": "^24.19.2",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.1.2",
    "oxlint": "^1.88.0",
    "typescript": "~6.0.3",
    "vite": "^8.3.4"
  }
}
```

### veritas/frontend/src/App.tsx

```tsx
export default function App() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <h1 className="text-center text-2xl font-semibold tracking-tight sm:text-3xl">
        VERITAS — Academic QA Gateway
      </h1>
    </main>
  )
}
```

### veritas/frontend/src/index.css

```css
@import "tailwindcss";

@theme {
  --color-ink: #0b0f17;
  --color-panel: #121826;
  --color-edge: #1f2937;
  --color-accent: #38bdf8;
}

body {
  @apply bg-ink text-slate-200;
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}
```

### veritas/frontend/src/main.tsx

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### veritas/frontend/tsconfig.app.json

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023", "DOM"],
    "module": "esnext",
    "types": ["vite/client"],
    "allowArbitraryExtensions": true,
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

### veritas/frontend/tsconfig.json

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

### veritas/frontend/tsconfig.node.json

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023"],
    "types": ["node"],
    "skipLibCheck": true,

    /* Bundler mode */
    "module": "nodenext",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

### veritas/frontend/vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

