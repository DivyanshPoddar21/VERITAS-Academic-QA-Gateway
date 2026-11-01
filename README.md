# VERITAS — Academic QA Gateway
> **HCLTech Career Shaper Programme — Project #72 (III Year Industry Project)**  
> **Student:** Divyansh Kumar (Roll No: 2400320100440) | ABES Engineering College, Ghaziabad  
> **Mentors:** Prof. Alok Patel (College Mentor) | Prathima Kadari (HCLTech Industry Mentor)

## Overview
VERITAS is a closed-corpus, embedding-based document QA gateway using RAG-style retrieval, deterministic confidence gating ($\tau = 0.35$), and extractive answer synthesis. Live inference utilizes strictly extractive sentence-aligned synthesis with citation provenance to prevent hallucinations.

## Key Verification
- **Automated Tests:** 83/83 `pytest` tests passing (`test_ingest.py`, `test_retriever.py`, `test_gating.py`, `test_api.py`, `test_index_rebuild.py`, `test_hardening.py`)
- **Frontend Build:** React 19 / TypeScript / Tailwind CSS v4 (`tsc -b && vite build` — 0 errors)
- **Vector Index:** HuggingFace `all-MiniLM-L6-v2` (384-d, L2-normalized) with FAISS `IndexFlatIP`
