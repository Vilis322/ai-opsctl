# AI OpsCtl — Design Spec

**Domain:** ai.opsctl.tech
**Project:** ~/Projects/work/opsctl/ai-opsctl/
**Date:** 2026-03-29
**Status:** Approved

---

## 1. Purpose

Demo/portfolio AI analytics platform for affiliate marketing data. Doubles as stack testing ground (NestJS + React + FastAPI + MLX) and iterative model training environment with versioned datasets.

**Key constraints:**
- 100% fake data — NDA-safe, no company data
- Realistic affiliate marketing data patterns, fully synthetic
- MLX for Apple Silicon native fine-tuning + inference
- Ollama as fallback for x86 VPS deployment

---

## 2. Architecture

```
React (Vite + Tailwind)
        |
        v
NestJS (TypeScript)              <- API gateway, auth, CRUD, WebSocket
   |-- /api/auth/*               <- JWT, login, i18n preferences
   |-- /api/chat/*               <- conversations, messages -> proxy to FastAPI
   |-- /api/datasets/*           <- CRUD datasets, versions, metadata
   |-- /api/dashboard/*          <- aggregations from PostgreSQL
   |-- /api/training/*           <- training runs CRUD -> proxy to FastAPI
   |-- /api/rag/*                <- RAG queries -> proxy to FastAPI
        |
        v
FastAPI (Python)                 <- ML-only: inference, training, RAG
   |-- /ml/chat                  <- MLX inference (streaming SSE)
   |-- /ml/train                 <- LoRA fine-tuning
   |-- /ml/train/status          <- training run status
   |-- /ml/rag/query             <- ChromaDB search -> LLM answer
   |-- /ml/rag/ingest            <- load documents into ChromaDB
   |-- /ml/models                <- list models/adapters
        |
        v
MLX + ChromaDB + PostgreSQL
```

**Responsibility split:**

| Layer | What | Stack |
|-------|------|-------|
| React | UI: chat, dashboard, datasets, auth | React 18, Vite, Tailwind, i18n, Socket.IO |
| NestJS | API gateway: auth, CRUD, WebSocket, ML proxy | NestJS, Prisma, PostgreSQL, Socket.IO |
| FastAPI | ML engine: inference, training, RAG | FastAPI, MLX, LangChain, ChromaDB |

**NestJS <-> FastAPI communication:**
- HTTP for request-response (query, ingest, train start)
- SSE for streaming chat: React <- NestJS <- FastAPI <- MLX
- NestJS proxies SSE stream transparently

**Prisma in NestJS** owns all tables. FastAPI reads PostgreSQL via SQLAlchemy (read-only for ML queries), writes only training_runs metrics.

---

## 3. ML/AI Stack

| Technology | Role | How Used |
|---|---|---|
| MLX / MLX-LM | Fine-tuning + inference | LoRA adapters on Apple Silicon, model load/unload |
| Llama 3.1 8B | Base LLM | Meta open-weight, converted to MLX format |
| PEFT | Parameter-efficient fine-tuning | LoRA/QLoRA config, adapter merge with base |
| LangChain | RAG orchestration | Document loader -> splitter -> embeddings -> ChromaDB -> retrieval -> LLM chain |
| ChromaDB | Vector store | Embedding storage, semantic search |
| Hugging Face Transformers | Model hub + tokenizers | Base model download, datasets library |
| Sentence-Transformers | Embeddings for RAG | Document/query vectorization (all-MiniLM or multilingual-e5) |
| Ollama | Fallback inference | x86 VPS deployment when MLX unavailable |

**Platform detection:**
```python
INFERENCE_BACKEND = "mlx" if platform.machine() == "arm64" else "ollama"
```

---

## 4. Project Structure

```
~/Projects/work/opsctl/ai-opsctl/
|
|-- backend/                     <- NestJS (TypeScript)
|   |-- src/
|   |   |-- modules/
|   |   |   |-- auth/            <- JWT, guards, login
|   |   |   |-- chat/            <- conversations CRUD + ML proxy
|   |   |   |-- datasets/        <- dataset CRUD, versioning
|   |   |   |-- dashboard/       <- aggregation queries
|   |   |   |-- training/        <- training runs CRUD + ML proxy
|   |   |   +-- rag/             <- RAG proxy
|   |   |-- prisma/              <- schema, seeds, migrations
|   |   +-- common/              <- guards, interceptors, i18n
|   +-- test/
|
|-- ml/                          <- FastAPI (Python)
|   |-- app/
|   |   |-- api/                 <- ML endpoints
|   |   |-- inference/           <- MLX chat + streaming
|   |   |-- training/            <- LoRA fine-tuning pipeline
|   |   |-- rag/                 <- LangChain + ChromaDB
|   |   +-- core/                <- config
|   |-- seeds/                   <- fake data generator
|   +-- tests/
|
|-- frontend/                    <- React 18 + Vite + Tailwind
|   +-- src/
|       |-- features/
|       |   |-- auth/
|       |   |-- chat/
|       |   |-- dashboard/
|       |   +-- datasets/
|       |-- shared/
|       +-- i18n/
|
|-- data/
|   |-- datasets/                <- exported JSON versions
|   |-- models/                  <- MLX base + adapters
|   +-- chromadb/                <- vector store
|
|-- docs/                        <- VitePress documentation site
|   |-- index.md                 <- Landing page
|   |-- guide/                   <- Setup, architecture, deploy
|   |-- api/                     <- API reference
|   |-- ml/                      <- ML docs (training, RAG, datasets)
|   +-- about/                   <- Stack, synthetic data disclaimer
|
|-- docker-compose.yml           <- PostgreSQL + ChromaDB
+-- Makefile
```

---

## 5. Database Schema (PostgreSQL)

### Auth
```
users              -- id, login, password_hash, language (en/ru/ua), created_at
```

### Chat
```
conversations      -- id, user_id, title, model_version, dataset_version, created_at
messages           -- id, conversation_id, role (user/assistant/system), content,
                      tokens_in, tokens_out, latency_ms, created_at
```

### Datasets (versioning)
```
datasets           -- id, name, version (semver), description,
                      status (draft/active/archived),
                      record_count, date_range_start, date_range_end, created_at
dataset_metadata   -- id, dataset_id, key, value (json)
```

### Fake CRM Data (per dataset)
```
ds_buyers          -- id, dataset_id, tag, name, team, vertical, is_active
ds_domains         -- id, dataset_id, domain_name, server_ip, buyer_id, status,
                      geo, tld, registrar, monthly_cost, created_date
ds_offers          -- id, dataset_id, name, vertical (saas/ecom/fintech), geo,
                      lang, conversion_rate, payout_amount, payout_currency
ds_leads           -- id, dataset_id, domain_id, offer_id, buyer_id, geo,
                      first_name, last_name, email, phone, source,
                      crm_status (success/fail/duplicate), is_test, created_at
ds_servers         -- id, dataset_id, ip, provider, location, monthly_cost,
                      domain_count, status
ds_expenses        -- id, dataset_id, buyer_id, category, amount, currency, date
ds_incomes         -- id, dataset_id, buyer_id, offer_id, geo, type (cpl/cpa/crg),
                      amount, currency, date
```

### ML Training
```
training_runs      -- id, dataset_id, model_base, adapter_name,
                      hyperparams (json), metrics (json: loss, eval_loss, perplexity),
                      status (pending/running/completed/failed),
                      started_at, completed_at, duration_sec
training_comparisons -- id, run_a_id, run_b_id, comparison_notes, created_at
```

### RAG
```
rag_collections    -- id, dataset_id, name, doc_count, embedding_model,
                      status (indexing/ready), created_at
```

**Key decisions:**
- All fake CRM tables prefixed `ds_` with FK to `dataset_id` — switching dataset = changing filter
- Datasets versioned via semver (v1.0.0, v1.1.0, v2.0.0)
- Training runs linked to specific dataset — compare "model on v1 vs model on v2"
- RAG collections also linked to dataset — re-indexed on new version

---

## 6. Fake Dataset Specification

### Verticals and Distribution

| Vertical | Share | Offers (examples) | Geos | Avg Payout |
|----------|-------|-------------------|------|------------|
| SaaS | 35% | CloudSync Pro, DataVault, TaskFlow, CodeMetrics | US, UK, DE, CA | $40-80 CPL |
| E-commerce | 35% | ShopNest, DealHunter, PriceRadar, StyleBox | US, UK, AU, FR, JP | $8-25 CPA |
| Fintech | 30% | WealthBridge, PayStream, CryptoEdge, LoanFlex | UK, DE, CH, SG, AU | $80-200 CPA |

### Buyer Tags (15, white-label names)
```
SaaS:       Maxwell, Harper, Quinn, Reese, Avery
E-commerce: Jordan, Blake, Cameron, Morgan, Riley
Fintech:    Spencer, Emerson, Parker, Sloane, Kendall
```

### Generation Patterns (12 months)
- Seasonality: Q4 peak (Black Friday, Christmas for ecom), Q1 dip
- Buyer trends: 2-3 growing, 2-3 stable, 1-2 declining ROI, 1 fired (month 8)
- Conversion rates: SaaS 2-5%, E-com 3-8%, Fintech 1-3% with +/-30% variance
- Domains: `{brand}.{tld}` — TLD mix: .com 40%, .io 20%, .co 15%, .app 10%, .dev 15%
- Servers: 15 servers, providers: DigitalOcean, Hetzner, Linode, Vultr
- Leads: 30K total, monthly distribution with seasonality, 85% SUCCESS / 10% FAIL / 5% DUPLICATE
- Finances: incomes from leads (payout x leads), expenses: domains, servers, tools, team costs

### Generator
```bash
python ml/seeds/generator.py --version v1.0.0 --months 12 --leads 30000 --domains 200 --buyers 15 --seed 42
```
Deterministic (seed=42). Output: PostgreSQL records + JSONL for training + JSON for RAG ingest.
Fake names/emails via Faker (en_US, de_DE, fr_FR, ja_JP per geo). Phones via phonenumbers. Domains via brandable word dictionary.

### Training Data Format
```jsonl
{"prompt": "What is the average ROI for SaaS campaigns in US?", "completion": "Based on the dataset, the average ROI for SaaS campaigns targeting US is 340%..."}
{"prompt": "Compare lead conversion rates across verticals", "completion": "Fintech has the lowest conversion at 2.1% but highest payout ($140 avg)..."}
{"prompt": "Which buyers underperformed in Q3?", "completion": "Buyer Sloane showed a 45% drop in ROI in Q3..."}
```
Auto-generated from dataset — seed generator creates both data and Q&A pairs.

---

## 7. UI Pages

### Login (`/login`)
- Pre-filled: admin / admin
- Default language EN, switcher EN/RU/UA
- After login -> `/chat`

### Global UI Elements
- **Footer:** persistent "Demo mode — all data is synthetic" text on every page
- **Top bar:** active dataset + active model (global context)

### Chat (`/chat`)
- Minimalist interface (Claude/ChatGPT style)
- Left: sidebar with conversation history
- Right: chat window with streaming responses
- Top: active dataset dropdown + active model/adapter
- Query types: RAG (data search), Analytics (SQL + LLM), General (pure LLM)
- Markdown rendering (tables, code, lists)
- SSE streaming (token by token)

### Dashboard (`/dashboard`)
- Depends on selected dataset
- Metric cards: total leads, revenue, expenses, ROI, active domains
- Charts: timeline (leads/revenue by month), bar (ROI by buyer), pie (verticals), heatmap (geo x vertical)
- Table: top buyers with metrics (sortable, filterable)
- Chart library: Recharts

### Datasets (`/datasets`)
- List: name, version, status (draft/active/archived), record count, date range
- Create: generation params (months, leads, buyers, seed) -> run generator
- Detail: per-table stats, data preview (first 20 records)
- Compare: diff metrics between two versions
- Activate/Archive: switch active dataset

### Training (`/training`)
- List: training runs with model, dataset, status, loss, duration
- Start new: select base model, dataset, hyperparams (learning rate, epochs, LoRA rank)
- Detail: loss chart by steps, eval metrics
- Compare: two runs side-by-side
- Models: list available, activate for chat

### Navigation
```
Sidebar:
|-- Chat          (/chat)
|-- Dashboard     (/dashboard)
|-- Datasets      (/datasets)
|-- Training      (/training)
+-- Settings      (/settings — language, theme)
```
Top bar: active dataset + active model — global context, visible from any page.

---

## 8. API Endpoints

### NestJS (port 3000)

```
AUTH
  POST   /api/auth/login
  POST   /api/auth/refresh
  GET    /api/auth/me

CHAT
  GET    /api/chat/conversations
  POST   /api/chat/conversations
  DELETE /api/chat/conversations/:id
  GET    /api/chat/conversations/:id/messages
  POST   /api/chat/conversations/:id/messages       (SSE stream)

DATASETS
  GET    /api/datasets
  POST   /api/datasets                               (trigger generation)
  GET    /api/datasets/:id
  PATCH  /api/datasets/:id                           (activate/archive)
  DELETE /api/datasets/:id                           (draft only)
  GET    /api/datasets/:id/preview/:table
  GET    /api/datasets/compare/:a/:b

DASHBOARD
  GET    /api/dashboard/summary
  GET    /api/dashboard/charts/timeline
  GET    /api/dashboard/charts/buyers
  GET    /api/dashboard/charts/verticals
  GET    /api/dashboard/charts/geo-heatmap
  GET    /api/dashboard/tables/buyers
  (all accept ?dataset_id=)

TRAINING
  GET    /api/training/runs
  POST   /api/training/runs                          (proxy to FastAPI)
  GET    /api/training/runs/:id
  DELETE /api/training/runs/:id
  GET    /api/training/runs/compare/:a/:b
  GET    /api/training/models
  PATCH  /api/training/models/:id/activate

RAG
  POST   /api/rag/query                              (proxy to FastAPI)
  POST   /api/rag/ingest                             (proxy to FastAPI)
  GET    /api/rag/collections
```

### FastAPI (port 8100)

```
INFERENCE
  POST   /ml/chat                   (SSE streaming)
  POST   /ml/chat/complete          (non-streaming)

TRAINING
  POST   /ml/train
  GET    /ml/train/:run_id
  POST   /ml/train/:run_id/stop

RAG
  POST   /ml/rag/query
  POST   /ml/rag/ingest
  GET    /ml/rag/collections

MODELS
  GET    /ml/models
  POST   /ml/models/load
  POST   /ml/models/unload
```

---

## 9. Deployment

### Local Dev (Mac M4 Max)

```bash
docker compose up -d postgres chromadb
cd backend && npm run start:dev          # port 3000
cd ml && uvicorn app.main:app --port 8100 --reload
cd frontend && npm run dev               # port 5173, proxy -> 3000
```

### Docker Compose (dev infra only)

```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: ai_opsctl
      POSTGRES_USER: opsctl
      POSTGRES_PASSWORD: opsctl_dev
    volumes: [pgdata:/var/lib/postgresql/data]

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8000:8000"]
    volumes: [chromadata:/chroma/chroma]
```

### VPS Deploy (when ready)

```
ai.opsctl.tech (nginx + Let's Encrypt)
|-- /              -> frontend static (nginx serve)
|-- /api/*         -> NestJS (PM2, port 3000)
|-- /ml/*          -> FastAPI (uvicorn, port 8100)
|-- PostgreSQL     -> Docker (5432)
|-- ChromaDB       -> Docker (8000)
+-- MLX models     -> /data/models/
```

MLX = Apple Silicon only. On x86 VPS: fallback to Ollama via config detection.

### Git
- Repo: ~/Projects/work/opsctl/ai-opsctl/
- Branches: main (protected), stage (working)
- .gitignore: data/, .env, node_modules/, __pycache__/, *.gguf

---

## 10. Documentation Site (GitHub Pages)

### Structure
Project root serves as a docs landing page via GitHub Pages (VitePress or Docusaurus):

```
docs/
|-- index.md                  <- Landing page with project overview
|-- guide/
|   |-- getting-started.md    <- Setup, env, first run
|   |-- architecture.md       <- Service diagram, stack overview
|   +-- deployment.md         <- Local dev, VPS deploy
|-- api/
|   |-- nestjs.md             <- NestJS endpoints reference
|   +-- fastapi.md            <- FastAPI ML endpoints reference
|-- ml/
|   |-- training.md           <- Fine-tuning workflow, LoRA, MLX
|   |-- rag.md                <- RAG pipeline, ChromaDB, LangChain
|   +-- datasets.md           <- Dataset versioning, generation
+-- about/
    |-- stack.md              <- Full technology list with descriptions
    +-- synthetic-data.md     <- Disclaimer: all data is synthetic
```

### Landing Page Content
- Project title + one-line description
- Navigation sidebar (all doc pages)
- Architecture diagram (interactive or SVG)
- Tech stack badges (MLX, Llama, FastAPI, NestJS, React, etc.)
- Live demo link: `ai.opsctl.tech`
- **Prominent banner:** "All data in this project is 100% synthetic — generated for demonstration purposes"

### Synthetic Data Disclaimer
Present in THREE places:
1. **Docs landing page** — banner at top
2. **App UI footer** — persistent text: "Demo mode — all data is synthetic"
3. **README.md** — first section after title

**Disclaimer text (EN):**
> This project uses entirely synthetic data generated for demonstration and educational purposes. No real company data, personal information, or proprietary datasets are used. All names, domains, financial figures, and market data are fictitious. Any resemblance to real entities is coincidental.

**Tool:** VitePress (lightweight, Vue-based, fits the stack). Built from `docs/` dir, deployed to GitHub Pages or as static files on ai.opsctl.tech/docs.

---

## 11. Iterative Training Workflow

```
1. Generate dataset v1.0.0 (seed generator)
2. Load into ChromaDB (RAG ingest)
3. Fine-tune Llama 3.1 8B via MLX LoRA
   - Input: JSONL (Q&A pairs from dataset)
   - Output: LoRA adapter (~50-100MB)
   - RAM: ~8-10GB for 8B on M4 Max
   - Time: ~15-30 min per 1000 examples
4. Test in chat
5. Adjust dataset -> v1.1.0
6. Repeat from step 2

Adapter storage:
  data/models/
  |-- base/llama-3.1-8b-mlx/
  |-- adapters/v1.0.0-market-analysis/
  |-- adapters/v1.1.0-market-analysis/
  +-- adapters/v2.0.0-mixed-vertical/
```

---

## 12. Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| MLX = Apple Silicon only | No fine-tuned deploy on x86 VPS | Ollama fallback (GGUF export) or Mac as server |
| Llama 3.1 8B = mid-tier | Not GPT-4 quality | Good enough for demo, RAG compensates |
| 36GB unified memory | Max ~13B for training | 8B with LoRA is fine |
| Fake data | Model doesn't learn real market | Patterns realistic, sufficient for portfolio |
| Single user demo | No load testing | Not needed for portfolio |

---

## 13. Security

- No real company data in code/seeds/models
- `.env` with credentials in `.gitignore`
- VPS: basic auth on nginx level on top of JWT
- Models/adapters in `.gitignore` (large files)
- `data/` entirely in `.gitignore`, seed generator reproduces deterministically
