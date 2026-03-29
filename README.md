# OpsCtl AI

ML/AI analytics platform for the OpsCtl ecosystem — RAG search, iterative fine-tuning, versioned dataset management, and market analytics dashboards.

> **All data in this project is 100% synthetic.** Generated for demonstration and educational purposes only. No real company data, personal information, or proprietary datasets are used. All names, domains, financial figures, and market data are fictitious.

## Overview

OpsCtl AI processes synthetic affiliate marketing data through a RAG pipeline and fine-tuned LLM to deliver conversational analytics, dashboards, and training run management. Currently in active development — runs locally on Apple Silicon with MLX for native inference and LoRA fine-tuning.

## Features

- **Conversational Analytics** — chat with AI model grounded in dataset context (RAG + fine-tuned)
- **Market Dashboards** — leads, revenue, ROI, buyer performance, geo heatmaps
- **Dataset Versioning** — deterministic generation, semver, side-by-side comparison
- **Iterative Training** — MLX LoRA fine-tuning, run tracking, adapter management
- **Lead Scoring** — quality prediction based on source, geo, and behavioral signals
- **Report Generation** — AI-powered summaries with streaming responses (SSE)
- **RAG Knowledge Base** — natural language queries over structured data via ChromaDB

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Socket.IO, i18n (EN/RU/UA) |
| Backend | NestJS, Prisma, PostgreSQL, JWT, Socket.IO |
| ML Engine | FastAPI, MLX, LangChain, ChromaDB, Sentence-Transformers |
| Training | MLX LoRA/QLoRA, PEFT, Hugging Face Transformers, Llama 3.1 8B |
| Inference | MLX (Apple Silicon native), Ollama (x86 fallback) |
| Infrastructure | Docker Compose, nginx, Let's Encrypt |

## Architecture

```
React (:5173)  ->  NestJS (:3000)  ->  FastAPI (:8100)  ->  MLX / Ollama
                        |                    |
                   PostgreSQL            ChromaDB
                    (Prisma)            (Vectors)
```

- **NestJS** — API gateway: auth, CRUD, WebSocket, ML proxy
- **FastAPI** — ML engine: inference, RAG pipeline, fine-tuning orchestration
- **MLX** — Apple Silicon native LoRA fine-tuning + inference (M4 Max 36GB)

## Synthetic Dataset

Deterministic seed generator (`ml/seeds/generator.py`) produces 12 months of data across 3 verticals (SaaS, E-commerce, Fintech):

| Entity | Count |
|--------|-------|
| Buyers | 15 (3 teams, 1 fired at month 8) |
| Domains | 200 (brandable names, 5 TLDs) |
| Servers | 15 (4 providers) |
| Offers | 44 (12 base x multiple geos) |
| Leads | 30,000 (seasonality, geo-appropriate names) |
| Incomes | ~7,000 (leads x payout) |
| Expenses | ~900 (5 categories + server costs) |

## Quick Start

```bash
cp .env.example .env
make infra              # Start PostgreSQL + ChromaDB (Docker)
make db-migrate         # Prisma migrations (15 tables)
make db-seed            # Generate synthetic dataset v1.0.0 (30K leads)
make dev-backend        # NestJS on :3000
make dev-ml             # FastAPI on :8100
make dev-frontend       # React on :5173
```

## Project Structure

```
ai-opsctl/
|-- backend/                NestJS API gateway (TypeScript)
|   |-- src/modules/        auth, chat, datasets, dashboard, training, rag
|   +-- prisma/             schema (15 tables), migrations
|
|-- ml/                     FastAPI ML engine (Python)
|   |-- app/                inference, training, rag, api
|   |-- seeds/              synthetic data generator
|   +-- tests/              pytest (18 tests)
|
|-- frontend/               React 18 SPA (TypeScript)
|   +-- src/features/       auth, chat, dashboard, datasets, training
|
|-- data/                   runtime data (.gitignored)
|   |-- datasets/           exported JSON/JSONL versions
|   |-- models/             MLX base models + LoRA adapters
|   +-- chromadb/           vector store
|
+-- docs/                   VitePress documentation site
```

## Status

In active development. Phase 1 (infrastructure + seed generator) complete.

Demo will be available at `ai.opsctl.tech` — currently redirects to this repository.

## Author

Kyrylo Pryiomyshev — [GitHub](https://github.com/Vilis322)

## License

All rights reserved.
