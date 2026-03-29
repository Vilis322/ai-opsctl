# Phase 1: Infrastructure + Fake Data Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up project infrastructure (Docker Compose, PostgreSQL, Prisma schema) and build a deterministic fake data generator that produces 12 months of synthetic affiliate marketing data across 3 verticals.

**Architecture:** Monorepo with 3 service directories (backend/, ml/, frontend/). PostgreSQL via Docker Compose. Prisma ORM in backend/ owns the schema. Python seed generator in ml/seeds/ writes data via SQLAlchemy (direct DB access). All data is 100% synthetic — NDA-safe.

**Tech Stack:** Docker Compose, PostgreSQL 16, Prisma 7.x (NestJS), SQLAlchemy (Python read/write for seeds), Faker, Python 3.12+

**Spec:** `docs/superpowers/specs/2026-03-29-ai-opsctl-design.md`

---

## File Structure

```
ai-opsctl/
|-- docker-compose.yml                    <- PostgreSQL + ChromaDB
|-- Makefile                              <- dev commands
|-- .env.example                          <- env template
|-- .gitignore                            <- data/, node_modules/, .env, etc.
|-- README.md                             <- project overview + synthetic data disclaimer
|
|-- backend/
|   |-- package.json
|   |-- tsconfig.json
|   |-- nest-cli.json
|   |-- prisma/
|   |   |-- schema.prisma                 <- full DB schema (13 tables)
|   |   +-- migrations/                   <- Prisma Migrate
|   +-- src/
|       +-- main.ts                       <- minimal NestJS bootstrap (placeholder)
|
|-- ml/
|   |-- requirements.txt                  <- Python deps
|   |-- seeds/
|   |   |-- generator.py                  <- main entry point
|   |   |-- config.py                     <- generation parameters
|   |   |-- buyers.py                     <- buyer generation
|   |   |-- domains.py                    <- domain generation
|   |   |-- servers.py                    <- server generation
|   |   |-- offers.py                     <- offer generation
|   |   |-- leads.py                      <- lead generation (30K)
|   |   |-- financials.py                 <- incomes + expenses
|   |   |-- training_data.py              <- Q&A JSONL generation
|   |   +-- db.py                         <- SQLAlchemy connection + models
|   +-- tests/
|       +-- test_generator.py             <- seed generator tests
|
+-- data/                                 <- .gitignored
    |-- datasets/                         <- exported JSON/JSONL versions
    +-- models/                           <- MLX models (later)
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `Makefile`
- Create: `README.md`

- [ ] **Step 1: Initialize git repo**

```bash
cd ~/Projects/work/opsctl/ai-opsctl
git init
git checkout -b stage
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Data (reproducible via seed generator)
data/
*.gguf
*.safetensors

# Environment
.env
.env.local
.env.production

# Build
dist/
build/
.next/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Prisma
backend/prisma/migrations/**/migration_lock.toml

# Logs
logs/
*.log
```

- [ ] **Step 3: Create .env.example**

```env
# PostgreSQL
POSTGRES_DB=ai_opsctl
POSTGRES_USER=opsctl
POSTGRES_PASSWORD=opsctl_dev
DATABASE_URL=postgresql://opsctl:opsctl_dev@localhost:5432/ai_opsctl

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# ML Service
ML_SERVICE_URL=http://localhost:8100
INFERENCE_BACKEND=mlx

# NestJS
PORT=3000
JWT_SECRET=dev-secret-ai-opsctl
JWT_REFRESH_SECRET=dev-refresh-secret-ai-opsctl

# App
DEFAULT_LANGUAGE=en
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: ai-opsctl-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-ai_opsctl}
      POSTGRES_USER: ${POSTGRES_USER:-opsctl}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-opsctl_dev}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-opsctl}"]
      interval: 5s
      timeout: 3s
      retries: 5

  chromadb:
    image: chromadb/chroma:latest
    container_name: ai-opsctl-chromadb
    ports:
      - "8000:8000"
    volumes:
      - chromadata:/chroma/chroma
    environment:
      ANONYMIZED_TELEMETRY: "false"

volumes:
  pgdata:
  chromadata:
```

- [ ] **Step 5: Create Makefile**

```makefile
.PHONY: infra infra-down db-migrate db-seed dev-backend dev-ml dev-frontend test clean

# Infrastructure
infra:
	docker compose up -d postgres chromadb

infra-down:
	docker compose down

# Database
db-migrate:
	cd backend && npx prisma migrate dev

db-push:
	cd backend && npx prisma db push

db-seed:
	cd ml && python seeds/generator.py --version v1.0.0 --months 12 --leads 30000 --seed 42

db-reset:
	cd backend && npx prisma migrate reset --force

# Dev servers (run in separate terminals)
dev-backend:
	cd backend && npm run start:dev

dev-ml:
	cd ml && uvicorn app.main:app --port 8100 --reload

dev-frontend:
	cd frontend && npm run dev

# Tests
test:
	cd ml && python -m pytest tests/ -v
	cd backend && npm test

# Clean
clean:
	docker compose down -v
	rm -rf data/datasets/* data/models/*
```

- [ ] **Step 6: Create README.md**

```markdown
# AI OpsCtl

AI-powered analytics platform for affiliate marketing data with iterative model training.

> **All data in this project is 100% synthetic.** Generated for demonstration and educational purposes only. No real company data, personal information, or proprietary datasets are used. All names, domains, financial figures, and market data are fictitious. Any resemblance to real entities is coincidental.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, i18n (EN/RU/UA) |
| Backend | NestJS, Prisma, PostgreSQL, Socket.IO |
| ML | FastAPI, MLX, Llama 3.1 8B, LangChain, ChromaDB |
| Training | MLX LoRA/QLoRA, PEFT, Hugging Face Transformers |
| Infra | Docker Compose, nginx, Let's Encrypt |

## Quick Start

```bash
cp .env.example .env
make infra          # Start PostgreSQL + ChromaDB
make db-migrate     # Run migrations
make db-seed        # Generate synthetic dataset v1.0.0
make dev-backend    # NestJS on :3000
make dev-ml         # FastAPI on :8100
make dev-frontend   # React on :5173
```

## Live Demo

https://ai.opsctl.tech (login: admin / admin)

## Documentation

https://ai.opsctl.tech/docs
```

- [ ] **Step 7: Create data directories**

```bash
mkdir -p data/datasets data/models data/chromadb
```

- [ ] **Step 8: Commit**

```bash
git add .gitignore .env.example docker-compose.yml Makefile README.md
git commit -m "chore: project scaffolding — Docker Compose, Makefile, env template"
```

---

### Task 2: NestJS Bootstrap + Prisma Schema

**Files:**
- Create: `backend/package.json`
- Create: `backend/tsconfig.json`
- Create: `backend/nest-cli.json`
- Create: `backend/prisma/schema.prisma`
- Create: `backend/src/main.ts`

- [ ] **Step 1: Initialize NestJS project**

```bash
cd ~/Projects/work/opsctl/ai-opsctl
npx @nestjs/cli new backend --skip-git --package-manager npm --strict
```

- [ ] **Step 2: Install Prisma**

```bash
cd backend
npm install @prisma/client
npm install -D prisma
npx prisma init
```

- [ ] **Step 3: Write Prisma schema**

Replace `backend/prisma/schema.prisma` with:

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// === Auth ===

model User {
  id            String   @id @default(cuid())
  login         String   @unique
  passwordHash  String   @map("password_hash")
  language      String   @default("en") // en, ru, ua
  createdAt     DateTime @default(now()) @map("created_at")
  updatedAt     DateTime @updatedAt @map("updated_at")

  conversations Conversation[]

  @@map("users")
}

// === Chat ===

model Conversation {
  id             String   @id @default(cuid())
  userId         String   @map("user_id")
  title          String   @default("New conversation")
  modelVersion   String?  @map("model_version")
  datasetVersion String?  @map("dataset_version")
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")

  user     User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  messages Message[]

  @@index([userId, createdAt])
  @@map("conversations")
}

model Message {
  id             String   @id @default(cuid())
  conversationId String   @map("conversation_id")
  role           String   // user, assistant, system
  content        String
  tokensIn       Int?     @map("tokens_in")
  tokensOut      Int?     @map("tokens_out")
  latencyMs      Int?     @map("latency_ms")
  createdAt      DateTime @default(now()) @map("created_at")

  conversation Conversation @relation(fields: [conversationId], references: [id], onDelete: Cascade)

  @@index([conversationId, createdAt])
  @@map("messages")
}

// === Datasets ===

enum DatasetStatus {
  DRAFT
  ACTIVE
  ARCHIVED
}

model Dataset {
  id             String        @id @default(cuid())
  name           String
  version        String        // semver: v1.0.0
  description    String?
  status         DatasetStatus @default(DRAFT)
  recordCount    Int           @default(0) @map("record_count")
  dateRangeStart DateTime?     @map("date_range_start")
  dateRangeEnd   DateTime?     @map("date_range_end")
  generatorParams Json?        @map("generator_params") // { months, leads, buyers, seed }
  createdAt      DateTime      @default(now()) @map("created_at")

  metadata       DatasetMetadata[]
  buyers         DsBuyer[]
  domains        DsDomain[]
  servers        DsServer[]
  offers         DsOffer[]
  leads          DsLead[]
  expenses       DsExpense[]
  incomes        DsIncome[]
  trainingRuns   TrainingRun[]
  ragCollections RagCollection[]

  @@unique([name, version])
  @@map("datasets")
}

model DatasetMetadata {
  id        String @id @default(cuid())
  datasetId String @map("dataset_id")
  key       String
  value     Json

  dataset Dataset @relation(fields: [datasetId], references: [id], onDelete: Cascade)

  @@unique([datasetId, key])
  @@map("dataset_metadata")
}

// === Fake CRM Data ===

model DsBuyer {
  id        String  @id @default(cuid())
  datasetId String  @map("dataset_id")
  tag       String  // Maxwell, Harper, etc.
  name      String  // Full name
  team      String  // SaaS Team, E-commerce Team, Fintech Team
  vertical  String  // saas, ecom, fintech
  isActive  Boolean @default(true) @map("is_active")

  dataset  Dataset     @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  domains  DsDomain[]
  leads    DsLead[]
  expenses DsExpense[]
  incomes  DsIncome[]

  @@index([datasetId])
  @@map("ds_buyers")
}

model DsServer {
  id          String  @id @default(cuid())
  datasetId   String  @map("dataset_id")
  ip          String
  provider    String  // DigitalOcean, Hetzner, Linode, Vultr
  location    String  // NYC, AMS, FRA, SIN, SYD
  monthlyCost Decimal @map("monthly_cost") @db.Decimal(10, 2)
  domainCount Int     @default(0) @map("domain_count")
  status      String  @default("active") // active, maintenance, decommissioned

  dataset Dataset    @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  domains DsDomain[]

  @@index([datasetId])
  @@map("ds_servers")
}

model DsDomain {
  id          String   @id @default(cuid())
  datasetId   String   @map("dataset_id")
  domainName  String   @map("domain_name")
  serverId    String?  @map("server_id")
  buyerId     String?  @map("buyer_id")
  status      String   @default("active") // active, banned, inactive
  geo         String?
  tld         String   // .com, .io, .co, .app, .dev
  registrar   String   @default("Namecheap")
  monthlyCost Decimal  @map("monthly_cost") @db.Decimal(10, 2)
  createdDate DateTime @map("created_date")

  dataset Dataset   @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  server  DsServer? @relation(fields: [serverId], references: [id], onDelete: SetNull)
  buyer   DsBuyer?  @relation(fields: [buyerId], references: [id], onDelete: SetNull)
  leads   DsLead[]

  @@index([datasetId])
  @@index([buyerId])
  @@map("ds_domains")
}

model DsOffer {
  id             String  @id @default(cuid())
  datasetId      String  @map("dataset_id")
  name           String  // CloudSync Pro, ShopNest, WealthBridge
  vertical       String  // saas, ecom, fintech
  geo            String  // US, UK, DE, etc.
  lang           String  // en, de, fr, ja
  conversionRate Decimal @map("conversion_rate") @db.Decimal(5, 4) // 0.0350 = 3.5%
  payoutAmount   Decimal @map("payout_amount") @db.Decimal(10, 2)
  payoutCurrency String  @default("USD") @map("payout_currency")

  dataset Dataset  @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  leads   DsLead[]
  incomes DsIncome[]

  @@index([datasetId])
  @@map("ds_offers")
}

model DsLead {
  id        String   @id @default(cuid())
  datasetId String   @map("dataset_id")
  domainId  String?  @map("domain_id")
  offerId   String?  @map("offer_id")
  buyerId   String?  @map("buyer_id")
  geo       String
  firstName String   @map("first_name")
  lastName  String   @map("last_name")
  email     String
  phone     String
  source    String   @default("organic") // organic, paid, referral, direct
  crmStatus String   @default("success") @map("crm_status") // success, fail, duplicate
  isTest    Boolean  @default(false) @map("is_test")
  createdAt DateTime @map("created_at")

  dataset Dataset   @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  domain  DsDomain? @relation(fields: [domainId], references: [id], onDelete: SetNull)
  offer   DsOffer?  @relation(fields: [offerId], references: [id], onDelete: SetNull)
  buyer   DsBuyer?  @relation(fields: [buyerId], references: [id], onDelete: SetNull)

  @@index([datasetId, createdAt])
  @@index([buyerId])
  @@index([geo])
  @@index([crmStatus])
  @@map("ds_leads")
}

model DsExpense {
  id        String   @id @default(cuid())
  datasetId String   @map("dataset_id")
  buyerId   String?  @map("buyer_id")
  category  String   // domains, servers, tools, team, advertising
  amount    Decimal  @db.Decimal(10, 2)
  currency  String   @default("USD")
  date      DateTime

  dataset Dataset  @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  buyer   DsBuyer? @relation(fields: [buyerId], references: [id], onDelete: SetNull)

  @@index([datasetId, date])
  @@index([buyerId])
  @@map("ds_expenses")
}

model DsIncome {
  id        String   @id @default(cuid())
  datasetId String   @map("dataset_id")
  buyerId   String?  @map("buyer_id")
  offerId   String?  @map("offer_id")
  geo       String
  type      String   // cpl, cpa, crg
  amount    Decimal  @db.Decimal(10, 2)
  currency  String   @default("USD")
  date      DateTime

  dataset Dataset  @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  buyer   DsBuyer? @relation(fields: [buyerId], references: [id], onDelete: SetNull)
  offer   DsOffer? @relation(fields: [offerId], references: [id], onDelete: SetNull)

  @@index([datasetId, date])
  @@index([buyerId])
  @@index([geo])
  @@map("ds_incomes")
}

// === ML Training ===

enum TrainingStatus {
  PENDING
  RUNNING
  COMPLETED
  FAILED
}

model TrainingRun {
  id           String         @id @default(cuid())
  datasetId    String         @map("dataset_id")
  modelBase    String         @map("model_base") // llama-3.1-8b
  adapterName  String         @map("adapter_name") // v1.0.0-market-analysis
  hyperparams  Json           // { learning_rate, epochs, lora_rank, lora_alpha }
  metrics      Json?          // { loss, eval_loss, perplexity }
  status       TrainingStatus @default(PENDING)
  startedAt    DateTime?      @map("started_at")
  completedAt  DateTime?      @map("completed_at")
  durationSec  Int?           @map("duration_sec")
  createdAt    DateTime       @default(now()) @map("created_at")

  dataset     Dataset              @relation(fields: [datasetId], references: [id], onDelete: Cascade)
  comparisonsA TrainingComparison[] @relation("ComparisonRunA")
  comparisonsB TrainingComparison[] @relation("ComparisonRunB")

  @@index([datasetId])
  @@index([status])
  @@map("training_runs")
}

model TrainingComparison {
  id              String   @id @default(cuid())
  runAId          String   @map("run_a_id")
  runBId          String   @map("run_b_id")
  comparisonNotes String?  @map("comparison_notes")
  createdAt       DateTime @default(now()) @map("created_at")

  runA TrainingRun @relation("ComparisonRunA", fields: [runAId], references: [id], onDelete: Cascade)
  runB TrainingRun @relation("ComparisonRunB", fields: [runBId], references: [id], onDelete: Cascade)

  @@map("training_comparisons")
}

// === RAG ===

enum RagStatus {
  INDEXING
  READY
  FAILED
}

model RagCollection {
  id             String    @id @default(cuid())
  datasetId      String    @map("dataset_id")
  name           String
  docCount       Int       @default(0) @map("doc_count")
  embeddingModel String    @default("all-MiniLM-L6-v2") @map("embedding_model")
  status         RagStatus @default(INDEXING)
  createdAt      DateTime  @default(now()) @map("created_at")

  dataset Dataset @relation(fields: [datasetId], references: [id], onDelete: Cascade)

  @@index([datasetId])
  @@map("rag_collections")
}
```

- [ ] **Step 4: Create minimal NestJS entry point**

Replace `backend/src/main.ts`:

```typescript
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api');
  await app.listen(process.env.PORT ?? 3000);
  console.log(`NestJS running on port ${process.env.PORT ?? 3000}`);
}
bootstrap();
```

- [ ] **Step 5: Copy .env.example to backend .env and run migration**

```bash
cp .env.example backend/.env
cd backend && npx prisma migrate dev --name init
```

Expected: Migration created, 13 tables in PostgreSQL.

- [ ] **Step 6: Verify tables exist**

```bash
docker exec -it ai-opsctl-postgres psql -U opsctl -d ai_opsctl -c "\dt"
```

Expected: All tables listed (users, conversations, messages, datasets, dataset_metadata, ds_buyers, ds_domains, ds_servers, ds_offers, ds_leads, ds_expenses, ds_incomes, training_runs, training_comparisons, rag_collections).

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: NestJS bootstrap with Prisma schema — 13 tables for datasets, CRM, training, RAG"
```

---

### Task 3: Python Seed Environment Setup

**Files:**
- Create: `ml/requirements.txt`
- Create: `ml/seeds/__init__.py`
- Create: `ml/seeds/db.py`
- Create: `ml/seeds/config.py`
- Create: `ml/tests/__init__.py`

- [ ] **Step 1: Create ml directory structure**

```bash
cd ~/Projects/work/opsctl/ai-opsctl
mkdir -p ml/seeds ml/tests ml/app
touch ml/seeds/__init__.py ml/tests/__init__.py ml/app/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```
# Seed generator
sqlalchemy==2.0.*
psycopg2-binary==2.9.*
faker==33.*
phonenumbers==8.*

# ML (for later phases, install now)
fastapi==0.115.*
uvicorn[standard]==0.34.*
langchain==0.3.*
langchain-community==0.3.*
chromadb==0.6.*
sentence-transformers==3.*
mlx-lm==0.21.*
peft==0.14.*
transformers==4.*
huggingface-hub==0.28.*

# Testing
pytest==8.*
pytest-asyncio==0.25.*
```

- [ ] **Step 3: Create Python virtualenv and install**

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 4: Create ml/seeds/db.py**

```python
"""SQLAlchemy connection and table models for seed generator."""

from sqlalchemy import (
    create_engine, Column, String, Boolean, Integer, DateTime, Numeric,
    JSON, ForeignKey, Enum as PgEnum, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os
import enum

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsctl:opsctl_dev@localhost:5432/ai_opsctl"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class DatasetStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="DRAFT")
    record_count = Column(Integer, default=0)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    generator_params = Column(JSON)
    created_at = Column(DateTime, server_default=text("NOW()"))


class DsBuyer(Base):
    __tablename__ = "ds_buyers"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String, nullable=False)
    name = Column(String, nullable=False)
    team = Column(String, nullable=False)
    vertical = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class DsServer(Base):
    __tablename__ = "ds_servers"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    ip = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    location = Column(String, nullable=False)
    monthly_cost = Column(Numeric(10, 2), nullable=False)
    domain_count = Column(Integer, default=0)
    status = Column(String, default="active")


class DsDomain(Base):
    __tablename__ = "ds_domains"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    domain_name = Column(String, nullable=False)
    server_id = Column(String, ForeignKey("ds_servers.id", ondelete="SET NULL"))
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    status = Column(String, default="active")
    geo = Column(String)
    tld = Column(String, nullable=False)
    registrar = Column(String, default="Namecheap")
    monthly_cost = Column(Numeric(10, 2), nullable=False)
    created_date = Column(DateTime, nullable=False)


class DsOffer(Base):
    __tablename__ = "ds_offers"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    vertical = Column(String, nullable=False)
    geo = Column(String, nullable=False)
    lang = Column(String, nullable=False)
    conversion_rate = Column(Numeric(5, 4), nullable=False)
    payout_amount = Column(Numeric(10, 2), nullable=False)
    payout_currency = Column(String, default="USD")


class DsLead(Base):
    __tablename__ = "ds_leads"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(String, ForeignKey("ds_domains.id", ondelete="SET NULL"))
    offer_id = Column(String, ForeignKey("ds_offers.id", ondelete="SET NULL"))
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    geo = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    source = Column(String, default="organic")
    crm_status = Column(String, default="success")
    is_test = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)


class DsExpense(Base):
    __tablename__ = "ds_expenses"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    date = Column(DateTime, nullable=False)


class DsIncome(Base):
    __tablename__ = "ds_incomes"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    offer_id = Column(String, ForeignKey("ds_offers.id", ondelete="SET NULL"))
    geo = Column(String, nullable=False)
    type = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    date = Column(DateTime, nullable=False)


def get_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def clear_dataset(session: Session, dataset_id: str) -> None:
    """Delete all records for a dataset (cascade handled by FK)."""
    session.query(Dataset).filter(Dataset.id == dataset_id).delete()
    session.commit()
```

- [ ] **Step 5: Create ml/seeds/config.py**

```python
"""Seed generator configuration — all generation parameters."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GeneratorConfig:
    """Parameters for fake dataset generation."""
    version: str = "v1.0.0"
    months: int = 12
    total_leads: int = 30000
    total_domains: int = 200
    total_buyers: int = 15
    total_servers: int = 15
    seed: int = 42
    dataset_name: str = "Affiliate Marketing Demo"

    # Vertical distribution
    verticals: dict = field(default_factory=lambda: {
        "saas": 0.35,
        "ecom": 0.35,
        "fintech": 0.30,
    })

    # Buyer tags per vertical
    buyer_tags: dict = field(default_factory=lambda: {
        "saas": ["Maxwell", "Harper", "Quinn", "Reese", "Avery"],
        "ecom": ["Jordan", "Blake", "Cameron", "Morgan", "Riley"],
        "fintech": ["Spencer", "Emerson", "Parker", "Sloane", "Kendall"],
    })

    # Offers per vertical
    offers: dict = field(default_factory=lambda: {
        "saas": [
            {"name": "CloudSync Pro", "geos": ["US", "UK", "DE", "CA"], "payout_range": (40, 80), "type": "cpl"},
            {"name": "DataVault", "geos": ["US", "UK", "DE"], "payout_range": (50, 90), "type": "cpl"},
            {"name": "TaskFlow", "geos": ["US", "CA", "AU"], "payout_range": (35, 70), "type": "cpl"},
            {"name": "CodeMetrics", "geos": ["US", "UK", "DE", "FR"], "payout_range": (45, 85), "type": "cpl"},
        ],
        "ecom": [
            {"name": "ShopNest", "geos": ["US", "UK", "AU", "FR"], "payout_range": (8, 25), "type": "cpa"},
            {"name": "DealHunter", "geos": ["US", "UK", "DE", "JP"], "payout_range": (10, 22), "type": "cpa"},
            {"name": "PriceRadar", "geos": ["US", "UK", "AU"], "payout_range": (12, 28), "type": "cpa"},
            {"name": "StyleBox", "geos": ["US", "FR", "JP", "DE"], "payout_range": (15, 30), "type": "cpa"},
        ],
        "fintech": [
            {"name": "WealthBridge", "geos": ["UK", "DE", "CH", "SG"], "payout_range": (80, 200), "type": "cpa"},
            {"name": "PayStream", "geos": ["UK", "DE", "AU"], "payout_range": (90, 180), "type": "cpa"},
            {"name": "CryptoEdge", "geos": ["UK", "CH", "SG", "AU"], "payout_range": (100, 220), "type": "cpa"},
            {"name": "LoanFlex", "geos": ["UK", "DE", "AU", "SG"], "payout_range": (70, 160), "type": "cpa"},
        ],
    })

    # Geo → language mapping
    geo_lang: dict = field(default_factory=lambda: {
        "US": "en", "UK": "en", "CA": "en", "AU": "en",
        "DE": "de", "CH": "de", "FR": "fr", "JP": "ja", "SG": "en",
    })

    # Geo → Faker locale mapping
    geo_locale: dict = field(default_factory=lambda: {
        "US": "en_US", "UK": "en_GB", "CA": "en_CA", "AU": "en_AU",
        "DE": "de_DE", "CH": "de_CH", "FR": "fr_FR", "JP": "ja_JP", "SG": "en_US",
    })

    # Conversion rates per vertical (base, with +-30% variance)
    conversion_rates: dict = field(default_factory=lambda: {
        "saas": (0.02, 0.05),
        "ecom": (0.03, 0.08),
        "fintech": (0.01, 0.03),
    })

    # CRM status distribution
    crm_status_weights: dict = field(default_factory=lambda: {
        "success": 0.85,
        "fail": 0.10,
        "duplicate": 0.05,
    })

    # Seasonality multipliers (month 1-12)
    seasonality: list = field(default_factory=lambda: [
        0.75,  # Jan — Q1 dip
        0.80,  # Feb
        0.90,  # Mar
        0.95,  # Apr — Q2 recovery
        1.00,  # May
        1.00,  # Jun
        0.90,  # Jul — summer dip
        0.95,  # Aug
        1.05,  # Sep — Q3 ramp
        1.15,  # Oct
        1.30,  # Nov — Black Friday
        1.25,  # Dec — Christmas
    ])

    # Domain TLD distribution
    tld_weights: dict = field(default_factory=lambda: {
        ".com": 0.40,
        ".io": 0.20,
        ".co": 0.15,
        ".app": 0.10,
        ".dev": 0.15,
    })

    # Server providers
    server_providers: list = field(default_factory=lambda: [
        {"name": "DigitalOcean", "locations": ["NYC", "AMS", "SIN"], "cost_range": (12, 24)},
        {"name": "Hetzner", "locations": ["FRA", "HEL"], "cost_range": (8, 18)},
        {"name": "Linode", "locations": ["FRA", "SIN", "SYD"], "cost_range": (10, 20)},
        {"name": "Vultr", "locations": ["NYC", "AMS", "SYD", "NRT"], "cost_range": (11, 22)},
    ])

    # Expense categories with monthly ranges per buyer
    expense_categories: dict = field(default_factory=lambda: {
        "domains": (200, 600),
        "servers": (150, 400),
        "tools": (50, 200),
        "advertising": (500, 3000),
        "team": (100, 500),
    })

    # Fired buyer config
    fired_buyer_month: int = 8  # buyer Kendall gets fired in month 8
    fired_buyer_tag: str = "Kendall"
```

- [ ] **Step 6: Commit**

```bash
git add ml/
git commit -m "feat: Python seed environment — SQLAlchemy models, generator config, requirements"
```

---

### Task 4: Buyer + Server + Domain Generators

**Files:**
- Create: `ml/seeds/buyers.py`
- Create: `ml/seeds/servers.py`
- Create: `ml/seeds/domains.py`
- Create: `ml/tests/test_generator.py`

- [ ] **Step 1: Write test for buyer generation**

```python
# ml/tests/test_generator.py
"""Tests for seed generator modules."""

import random
from seeds.config import GeneratorConfig
from seeds.buyers import generate_buyers
from seeds.servers import generate_servers
from seeds.domains import generate_domains


def test_generate_buyers_count():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    assert len(buyers) == 15


def test_generate_buyers_verticals():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    verticals = {b["vertical"] for b in buyers}
    assert verticals == {"saas", "ecom", "fintech"}


def test_generate_buyers_tags_unique():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    tags = [b["tag"] for b in buyers]
    assert len(tags) == len(set(tags))


def test_generate_buyers_fired():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    kendall = [b for b in buyers if b["tag"] == "Kendall"][0]
    assert kendall["is_active"] is False


def test_generate_servers_count():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    servers = generate_servers(cfg)
    assert len(servers) == 15


def test_generate_servers_providers():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    servers = generate_servers(cfg)
    providers = {s["provider"] for s in servers}
    assert providers.issubset({"DigitalOcean", "Hetzner", "Linode", "Vultr"})


def test_generate_domains_count():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    assert len(domains) == 200


def test_generate_domains_tlds():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    tlds = {d["tld"] for d in domains}
    assert tlds.issubset({".com", ".io", ".co", ".app", ".dev"})


def test_generate_domains_unique_names():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    names = [d["domain_name"] for d in domains]
    assert len(names) == len(set(names))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ml && python -m pytest tests/test_generator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'seeds.buyers'`

- [ ] **Step 3: Create ml/seeds/buyers.py**

```python
"""Generate fake buyer data."""

import random
from typing import Any
from .config import GeneratorConfig


def _generate_cuid() -> str:
    """Generate a cuid-like ID."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "c" + "".join(random.choices(chars, k=24))


def generate_buyers(cfg: GeneratorConfig) -> list[dict[str, Any]]:
    """Generate buyer records from config.

    Returns list of dicts with keys: id, tag, name, team, vertical, is_active.
    """
    buyers = []

    team_names = {
        "saas": "SaaS Team",
        "ecom": "E-commerce Team",
        "fintech": "Fintech Team",
    }

    for vertical, tags in cfg.buyer_tags.items():
        for tag in tags:
            buyers.append({
                "id": _generate_cuid(),
                "tag": tag,
                "name": f"{tag} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Davis', 'Miller', 'Wilson'])}",
                "team": team_names[vertical],
                "vertical": vertical,
                "is_active": tag != cfg.fired_buyer_tag,
            })

    return buyers
```

- [ ] **Step 4: Create ml/seeds/servers.py**

```python
"""Generate fake server data."""

import random
from decimal import Decimal
from typing import Any
from .config import GeneratorConfig
from .buyers import _generate_cuid


def generate_servers(cfg: GeneratorConfig) -> list[dict[str, Any]]:
    """Generate server records.

    Returns list of dicts with keys: id, ip, provider, location, monthly_cost, domain_count, status.
    """
    servers = []

    for i in range(cfg.total_servers):
        provider_cfg = random.choice(cfg.server_providers)
        location = random.choice(provider_cfg["locations"])
        cost_min, cost_max = provider_cfg["cost_range"]

        servers.append({
            "id": _generate_cuid(),
            "ip": f"10.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "provider": provider_cfg["name"],
            "location": location,
            "monthly_cost": Decimal(str(round(random.uniform(cost_min, cost_max), 2))),
            "domain_count": 0,  # updated after domain generation
            "status": "active",
        })

    return servers
```

- [ ] **Step 5: Create ml/seeds/domains.py**

```python
"""Generate fake domain data."""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from .config import GeneratorConfig
from .buyers import _generate_cuid

# Brandable word parts for domain generation
PREFIXES = [
    "cloud", "data", "swift", "bright", "peak", "nova", "flux", "core",
    "blue", "arc", "zen", "neo", "vibe", "pulse", "aero", "flow",
    "star", "bolt", "edge", "wave", "mint", "pixel", "sage", "frost",
]

SUFFIXES = [
    "hub", "lab", "net", "run", "box", "pad", "bay", "ify",
    "zone", "base", "dock", "spot", "link", "wire", "cast", "mark",
    "view", "path", "sync", "port", "lens", "grid", "forge", "nest",
]


def _generate_domain_name(used_names: set[str]) -> tuple[str, str]:
    """Generate a unique brandable domain name.

    Returns (full_domain_name, tld).
    """
    tlds = [".com", ".io", ".co", ".app", ".dev"]
    tld_weights = [0.40, 0.20, 0.15, 0.10, 0.15]

    for _ in range(100):  # max attempts
        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)
        name = f"{prefix}{suffix}"
        tld = random.choices(tlds, weights=tld_weights, k=1)[0]
        full = f"{name}{tld}"
        if full not in used_names:
            used_names.add(full)
            return full, tld

    raise RuntimeError("Could not generate unique domain name after 100 attempts")


def generate_domains(
    cfg: GeneratorConfig,
    buyers: list[dict[str, Any]],
    servers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate domain records distributed across buyers and servers.

    Returns list of dicts with all domain fields.
    """
    domains = []
    used_names: set[str] = set()
    active_buyers = [b for b in buyers if b["is_active"]]

    # Date range: 12 months back from now
    end_date = datetime(2026, 3, 1)
    start_date = end_date - timedelta(days=30 * cfg.months)

    # TLD cost mapping
    tld_costs = {
        ".com": Decimal("9.50"),
        ".io": Decimal("32.00"),
        ".co": Decimal("11.50"),
        ".app": Decimal("14.00"),
        ".dev": Decimal("12.00"),
    }

    for i in range(cfg.total_domains):
        domain_name, tld = _generate_domain_name(used_names)
        buyer = random.choice(active_buyers)
        server = random.choice(servers)

        # Random creation date within range
        days_offset = random.randint(0, (end_date - start_date).days)
        created = start_date + timedelta(days=days_offset)

        # ~5% banned
        status = "banned" if random.random() < 0.05 else "active"

        geo_options = []
        for offer_list in cfg.offers.values():
            for offer in offer_list:
                geo_options.extend(offer["geos"])
        geo = random.choice(list(set(geo_options)))

        domains.append({
            "id": _generate_cuid(),
            "domain_name": domain_name,
            "server_id": server["id"],
            "buyer_id": buyer["id"],
            "status": status,
            "geo": geo,
            "tld": tld,
            "registrar": random.choice(["Namecheap", "Spaceship"]),
            "monthly_cost": tld_costs.get(tld, Decimal("10.00")),
            "created_date": created,
        })

        # Update server domain count
        server["domain_count"] += 1

    return domains
```

- [ ] **Step 6: Run tests**

```bash
cd ml && python -m pytest tests/test_generator.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add ml/seeds/buyers.py ml/seeds/servers.py ml/seeds/domains.py ml/tests/test_generator.py
git commit -m "feat: buyer, server, domain generators with tests — 200 domains, 15 buyers, 15 servers"
```

---

### Task 5: Offer + Lead Generators

**Files:**
- Create: `ml/seeds/offers.py`
- Create: `ml/seeds/leads.py`
- Modify: `ml/tests/test_generator.py`

- [ ] **Step 1: Add tests for offers and leads**

Append to `ml/tests/test_generator.py`:

```python
from seeds.offers import generate_offers
from seeds.leads import generate_leads


def test_generate_offers_per_vertical():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    offers = generate_offers(cfg)
    verticals = {o["vertical"] for o in offers}
    assert verticals == {"saas", "ecom", "fintech"}
    assert len(offers) >= 12  # 4 per vertical


def test_generate_leads_count():
    cfg = GeneratorConfig(seed=42, total_leads=1000)  # smaller for test speed
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)
    assert len(leads) == 1000


def test_generate_leads_crm_status_distribution():
    cfg = GeneratorConfig(seed=42, total_leads=10000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)

    statuses = [l["crm_status"] for l in leads]
    success_rate = statuses.count("success") / len(statuses)
    assert 0.80 < success_rate < 0.90  # ~85% with variance


def test_generate_leads_seasonality():
    cfg = GeneratorConfig(seed=42, total_leads=10000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)

    # November (month 11) should have more leads than January (month 1)
    nov_count = sum(1 for l in leads if l["created_at"].month == 11)
    jan_count = sum(1 for l in leads if l["created_at"].month == 1)
    assert nov_count > jan_count


def test_generate_leads_fired_buyer_no_late_leads():
    cfg = GeneratorConfig(seed=42, total_leads=5000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)

    kendall = [b for b in buyers if b["tag"] == "Kendall"][0]
    kendall_leads = [l for l in leads if l["buyer_id"] == kendall["id"]]
    # Kendall fired in month 8 — no leads after month 8
    late_leads = [l for l in kendall_leads if l["created_at"].month > cfg.fired_buyer_month]
    assert len(late_leads) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ml && python -m pytest tests/test_generator.py -v -k "offer or lead"
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create ml/seeds/offers.py**

```python
"""Generate fake offer data."""

import random
from decimal import Decimal
from typing import Any
from .config import GeneratorConfig
from .buyers import _generate_cuid


def generate_offers(cfg: GeneratorConfig) -> list[dict[str, Any]]:
    """Generate offer records from config.

    Returns list of dicts with all offer fields.
    """
    offers = []

    for vertical, offer_configs in cfg.offers.items():
        conv_min, conv_max = cfg.conversion_rates[vertical]

        for offer_cfg in offer_configs:
            for geo in offer_cfg["geos"]:
                payout_min, payout_max = offer_cfg["payout_range"]
                lang = cfg.geo_lang.get(geo, "en")

                offers.append({
                    "id": _generate_cuid(),
                    "name": offer_cfg["name"],
                    "vertical": vertical,
                    "geo": geo,
                    "lang": lang,
                    "conversion_rate": Decimal(str(round(random.uniform(conv_min, conv_max), 4))),
                    "payout_amount": Decimal(str(round(random.uniform(payout_min, payout_max), 2))),
                    "payout_currency": "USD",
                    "type": offer_cfg["type"],
                })

    return offers
```

- [ ] **Step 4: Create ml/seeds/leads.py**

```python
"""Generate fake lead data with seasonality and realistic distribution."""

import random
from datetime import datetime, timedelta
from typing import Any
from faker import Faker
from .config import GeneratorConfig
from .buyers import _generate_cuid


def generate_leads(
    cfg: GeneratorConfig,
    buyers: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    offers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate lead records with seasonality, geo-appropriate names, CRM status distribution.

    Returns list of dicts with all lead fields.
    """
    leads = []
    fakers: dict[str, Faker] = {}

    # Build Faker instances per locale
    for geo, locale in cfg.geo_locale.items():
        if locale not in fakers:
            fakers[locale] = Faker(locale)
            Faker.seed(cfg.seed)

    # Default faker for unknown locales
    default_faker = Faker("en_US")

    # Build lookup structures
    active_buyers = [b for b in buyers if b["is_active"]]
    active_domains = [d for d in domains if d["status"] == "active"]

    # Map offers by geo for matching
    offers_by_geo: dict[str, list[dict]] = {}
    for offer in offers:
        offers_by_geo.setdefault(offer["geo"], []).append(offer)

    # Date range
    end_date = datetime(2026, 3, 1)
    start_date = end_date - timedelta(days=30 * cfg.months)

    # Calculate leads per month using seasonality
    total_weight = sum(cfg.seasonality[:cfg.months])
    leads_per_month = []
    remaining = cfg.total_leads
    for i in range(cfg.months):
        if i == cfg.months - 1:
            count = remaining
        else:
            count = round(cfg.total_leads * cfg.seasonality[i] / total_weight)
            remaining -= count
        leads_per_month.append(count)

    # CRM status choices
    statuses = list(cfg.crm_status_weights.keys())
    status_weights = list(cfg.crm_status_weights.values())

    # Source options
    sources = ["organic", "paid", "referral", "direct"]
    source_weights = [0.30, 0.45, 0.15, 0.10]

    for month_idx, month_count in enumerate(leads_per_month):
        month_num = (start_date.month + month_idx - 1) % 12 + 1
        year = start_date.year + (start_date.month + month_idx - 1) // 12

        # Filter out fired buyer after their fired month
        month_buyers = [
            b for b in active_buyers
        ]
        if month_num > cfg.fired_buyer_month or (month_num <= cfg.fired_buyer_month and year > start_date.year):
            # After fired month, also check year
            pass
        # Simpler: Kendall fired after absolute month index
        available_buyers = []
        for b in buyers:
            if b["tag"] == cfg.fired_buyer_tag and month_idx >= cfg.fired_buyer_month:
                continue
            if not b["is_active"] and b["tag"] != cfg.fired_buyer_tag:
                continue
            available_buyers.append(b)

        if not available_buyers:
            available_buyers = active_buyers

        for _ in range(month_count):
            buyer = random.choice(available_buyers)
            domain = random.choice(active_domains)
            geo = domain.get("geo") or random.choice(list(cfg.geo_locale.keys()))

            # Pick offer matching geo, fallback to random
            geo_offers = offers_by_geo.get(geo, offers)
            offer = random.choice(geo_offers)

            # Geo-appropriate fake name
            locale = cfg.geo_locale.get(geo, "en_US")
            faker = fakers.get(locale, default_faker)

            # Random datetime within this month
            month_start = datetime(year, month_num, 1)
            if month_num == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month_num + 1, 1) - timedelta(seconds=1)

            created = month_start + timedelta(
                seconds=random.randint(0, int((month_end - month_start).total_seconds()))
            )

            first_name = faker.first_name()
            last_name = faker.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'mail.com'])}"

            leads.append({
                "id": _generate_cuid(),
                "domain_id": domain["id"],
                "offer_id": offer["id"],
                "buyer_id": buyer["id"],
                "geo": geo,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": faker.phone_number(),
                "source": random.choices(sources, weights=source_weights, k=1)[0],
                "crm_status": random.choices(statuses, weights=status_weights, k=1)[0],
                "is_test": random.random() < 0.02,  # 2% test leads
                "created_at": created,
            })

    return leads
```

- [ ] **Step 5: Run tests**

```bash
cd ml && python -m pytest tests/test_generator.py -v
```

Expected: All 14 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add ml/seeds/offers.py ml/seeds/leads.py ml/tests/test_generator.py
git commit -m "feat: offer + lead generators — 30K leads with seasonality, geo names, CRM status distribution"
```

---

### Task 6: Financial Data Generator

**Files:**
- Create: `ml/seeds/financials.py`
- Modify: `ml/tests/test_generator.py`

- [ ] **Step 1: Add tests for financials**

Append to `ml/tests/test_generator.py`:

```python
from seeds.financials import generate_financials


def test_generate_financials_has_incomes_and_expenses():
    cfg = GeneratorConfig(seed=42, total_leads=1000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)
    incomes, expenses = generate_financials(cfg, buyers, leads, offers, domains, servers)

    assert len(incomes) > 0
    assert len(expenses) > 0


def test_generate_financials_income_types():
    cfg = GeneratorConfig(seed=42, total_leads=1000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)
    incomes, expenses = generate_financials(cfg, buyers, leads, offers, domains, servers)

    types = {i["type"] for i in incomes}
    assert types.issubset({"cpl", "cpa", "crg"})


def test_generate_financials_expense_categories():
    cfg = GeneratorConfig(seed=42, total_leads=1000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)
    incomes, expenses = generate_financials(cfg, buyers, leads, offers, domains, servers)

    categories = {e["category"] for e in expenses}
    assert categories.issubset({"domains", "servers", "tools", "advertising", "team"})


def test_generate_financials_positive_amounts():
    cfg = GeneratorConfig(seed=42, total_leads=1000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)
    incomes, expenses = generate_financials(cfg, buyers, leads, offers, domains, servers)

    for inc in incomes:
        assert inc["amount"] > 0
    for exp in expenses:
        assert exp["amount"] > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ml && python -m pytest tests/test_generator.py -v -k "financial"
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create ml/seeds/financials.py**

```python
"""Generate fake income and expense data from leads and infrastructure."""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from .config import GeneratorConfig
from .buyers import _generate_cuid


def generate_financials(
    cfg: GeneratorConfig,
    buyers: list[dict[str, Any]],
    leads: list[dict[str, Any]],
    offers: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    servers: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate income and expense records from leads and infrastructure costs.

    Returns (incomes, expenses) tuple.
    """
    incomes = []
    expenses = []

    # Build lookup maps
    offer_map = {o["id"]: o for o in offers}
    buyer_map = {b["id"]: b for b in buyers}

    # === INCOMES: from successful leads ===
    # Group leads by month + buyer + offer for aggregation
    lead_groups: dict[tuple, list] = {}
    for lead in leads:
        if lead["crm_status"] != "success":
            continue
        month_key = (lead["created_at"].year, lead["created_at"].month)
        group_key = (month_key, lead["buyer_id"], lead["offer_id"])
        lead_groups.setdefault(group_key, []).append(lead)

    for (month_key, buyer_id, offer_id), group_leads in lead_groups.items():
        offer = offer_map.get(offer_id)
        if not offer:
            continue

        year, month = month_key
        lead_count = len(group_leads)
        payout = offer["payout_amount"]
        total_amount = Decimal(str(lead_count)) * payout

        # Add some variance (+/- 10%)
        variance = Decimal(str(round(random.uniform(0.90, 1.10), 2)))
        total_amount = (total_amount * variance).quantize(Decimal("0.01"))

        incomes.append({
            "id": _generate_cuid(),
            "buyer_id": buyer_id,
            "offer_id": offer_id,
            "geo": offer["geo"],
            "type": offer.get("type", "cpl"),
            "amount": total_amount,
            "currency": "USD",
            "date": datetime(year, month, 15),  # mid-month
        })

    # === EXPENSES: monthly per buyer ===
    end_date = datetime(2026, 3, 1)
    start_date = end_date - timedelta(days=30 * cfg.months)

    active_buyer_ids = {b["id"] for b in buyers if b["is_active"] or b["tag"] == cfg.fired_buyer_tag}

    for month_idx in range(cfg.months):
        month_num = (start_date.month + month_idx - 1) % 12 + 1
        year = start_date.year + (start_date.month + month_idx - 1) // 12
        expense_date = datetime(year, month_num, 1)

        for buyer in buyers:
            # Skip fired buyer after fired month
            if buyer["tag"] == cfg.fired_buyer_tag and month_idx >= cfg.fired_buyer_month:
                continue
            if not buyer["is_active"] and buyer["tag"] != cfg.fired_buyer_tag:
                continue

            for category, (cost_min, cost_max) in cfg.expense_categories.items():
                # Not every buyer has every category every month
                if random.random() < 0.15:  # 15% chance to skip
                    continue

                amount = Decimal(str(round(random.uniform(cost_min, cost_max), 2)))

                expenses.append({
                    "id": _generate_cuid(),
                    "buyer_id": buyer["id"],
                    "category": category,
                    "amount": amount,
                    "currency": "USD",
                    "date": expense_date,
                })

    # === EXPENSES: server costs (monthly, not per buyer) ===
    for month_idx in range(cfg.months):
        month_num = (start_date.month + month_idx - 1) % 12 + 1
        year = start_date.year + (start_date.month + month_idx - 1) // 12
        expense_date = datetime(year, month_num, 1)

        for server in servers:
            expenses.append({
                "id": _generate_cuid(),
                "buyer_id": None,
                "category": "servers",
                "amount": server["monthly_cost"],
                "currency": "USD",
                "date": expense_date,
            })

    return incomes, expenses
```

- [ ] **Step 4: Run tests**

```bash
cd ml && python -m pytest tests/test_generator.py -v
```

Expected: All 18 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ml/seeds/financials.py ml/tests/test_generator.py
git commit -m "feat: financial generator — incomes from leads + expenses (domains, servers, tools, team)"
```

---

### Task 7: Main Generator Entry Point + Training Data

**Files:**
- Create: `ml/seeds/training_data.py`
- Create: `ml/seeds/generator.py`

- [ ] **Step 1: Create ml/seeds/training_data.py**

```python
"""Generate Q&A training pairs from dataset for fine-tuning."""

import json
import random
from decimal import Decimal
from typing import Any
from .buyers import _generate_cuid


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def generate_training_data(
    buyers: list[dict[str, Any]],
    leads: list[dict[str, Any]],
    offers: list[dict[str, Any]],
    incomes: list[dict[str, Any]],
    expenses: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    servers: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Generate Q&A pairs for model fine-tuning.

    Returns list of {"prompt": "...", "completion": "..."} dicts.
    """
    pairs = []
    buyer_map = {b["id"]: b for b in buyers}
    offer_map = {o["id"]: o for o in offers}

    # --- ROI per buyer ---
    for buyer in buyers:
        buyer_incomes = [i for i in incomes if i["buyer_id"] == buyer["id"]]
        buyer_expenses = [e for e in expenses if e["buyer_id"] == buyer["id"]]
        total_income = sum(float(i["amount"]) for i in buyer_incomes)
        total_expense = sum(float(e["amount"]) for e in buyer_expenses)
        roi = ((total_income - total_expense) / total_expense * 100) if total_expense > 0 else 0

        pairs.append({
            "prompt": f"What is the ROI for buyer {buyer['tag']}?",
            "completion": f"Buyer {buyer['tag']} ({buyer['team']}, {buyer['vertical']} vertical) has a total income of ${total_income:,.2f} and total expenses of ${total_expense:,.2f}, resulting in an ROI of {roi:.1f}%. {'This buyer is currently inactive.' if not buyer['is_active'] else ''}".strip(),
        })

    # --- Leads per geo ---
    geo_counts: dict[str, int] = {}
    for lead in leads:
        geo_counts[lead["geo"]] = geo_counts.get(lead["geo"], 0) + 1

    for geo, count in sorted(geo_counts.items(), key=lambda x: -x[1]):
        success = sum(1 for l in leads if l["geo"] == geo and l["crm_status"] == "success")
        rate = (success / count * 100) if count > 0 else 0
        pairs.append({
            "prompt": f"How many leads are there from {geo}?",
            "completion": f"There are {count:,} leads from {geo}, with a {rate:.1f}% success rate ({success:,} successful leads).",
        })

    # --- Top performing offers ---
    offer_leads: dict[str, int] = {}
    for lead in leads:
        if lead["crm_status"] == "success" and lead["offer_id"]:
            offer_leads[lead["offer_id"]] = offer_leads.get(lead["offer_id"], 0) + 1

    top_offers = sorted(offer_leads.items(), key=lambda x: -x[1])[:5]
    offer_lines = []
    for oid, count in top_offers:
        offer = offer_map.get(oid)
        if offer:
            offer_lines.append(f"  - {offer['name']} ({offer['geo']}, {offer['vertical']}): {count:,} successful leads")

    if offer_lines:
        pairs.append({
            "prompt": "What are the top performing offers?",
            "completion": "Top 5 offers by successful leads:\n" + "\n".join(offer_lines),
        })

    # --- Vertical comparison ---
    vertical_data: dict[str, dict] = {}
    for lead in leads:
        buyer = buyer_map.get(lead["buyer_id"])
        if not buyer:
            continue
        v = buyer["vertical"]
        if v not in vertical_data:
            vertical_data[v] = {"total": 0, "success": 0}
        vertical_data[v]["total"] += 1
        if lead["crm_status"] == "success":
            vertical_data[v]["success"] += 1

    vert_lines = []
    for v, data in vertical_data.items():
        rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
        vert_lines.append(f"  - {v.upper()}: {data['total']:,} leads, {rate:.1f}% conversion")

    if vert_lines:
        pairs.append({
            "prompt": "Compare lead conversion rates across verticals.",
            "completion": "Vertical comparison:\n" + "\n".join(vert_lines),
        })

    # --- Monthly trend ---
    monthly: dict[str, int] = {}
    for lead in leads:
        key = lead["created_at"].strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + 1

    trend_lines = [f"  - {m}: {c:,} leads" for m, c in sorted(monthly.items())]
    if trend_lines:
        pairs.append({
            "prompt": "Show me the monthly lead trend.",
            "completion": "Monthly lead distribution:\n" + "\n".join(trend_lines),
        })

    # --- Domain stats ---
    active_domains = sum(1 for d in domains if d["status"] == "active")
    banned_domains = sum(1 for d in domains if d["status"] == "banned")
    pairs.append({
        "prompt": "What is the current domain status?",
        "completion": f"There are {len(domains)} total domains: {active_domains} active and {banned_domains} banned. Domains are hosted across {len(servers)} servers.",
    })

    # --- Server infrastructure ---
    provider_counts: dict[str, int] = {}
    for s in servers:
        provider_counts[s["provider"]] = provider_counts.get(s["provider"], 0) + 1
    provider_lines = [f"  - {p}: {c} servers" for p, c in sorted(provider_counts.items(), key=lambda x: -x[1])]
    total_cost = sum(float(s["monthly_cost"]) for s in servers)
    pairs.append({
        "prompt": "Describe the server infrastructure.",
        "completion": f"Infrastructure: {len(servers)} servers, ${total_cost:,.2f}/month total.\n" + "\n".join(provider_lines),
    })

    return pairs
```

- [ ] **Step 2: Create ml/seeds/generator.py**

```python
"""Main seed generator — orchestrates all data generation and DB insertion."""

import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seeds.config import GeneratorConfig
from seeds.db import (
    get_session, clear_dataset,
    Dataset, DsBuyer, DsServer, DsDomain, DsOffer, DsLead, DsExpense, DsIncome,
)
from seeds.buyers import generate_buyers, _generate_cuid
from seeds.servers import generate_servers
from seeds.domains import generate_domains
from seeds.offers import generate_offers
from seeds.leads import generate_leads
from seeds.financials import generate_financials
from seeds.training_data import generate_training_data, DecimalEncoder


def run(cfg: GeneratorConfig) -> None:
    """Generate full dataset and insert into PostgreSQL."""
    print(f"\n{'='*60}")
    print(f"  AI OpsCtl — Synthetic Data Generator")
    print(f"  Version: {cfg.version} | Seed: {cfg.seed}")
    print(f"  ALL DATA IS 100% SYNTHETIC — FOR DEMONSTRATION ONLY")
    print(f"{'='*60}\n")

    random.seed(cfg.seed)
    session = get_session()

    try:
        # 1. Create dataset record
        dataset_id = _generate_cuid()
        end_date = datetime(2026, 3, 1)
        start_date = datetime(2026 - (cfg.months // 12), 3 - (cfg.months % 12), 1)

        dataset = Dataset(
            id=dataset_id,
            name=cfg.dataset_name,
            version=cfg.version,
            description=f"Synthetic affiliate marketing data: {cfg.months} months, {cfg.total_leads} leads, {cfg.total_buyers} buyers. 100% fake.",
            status="ACTIVE",
            date_range_start=start_date,
            date_range_end=end_date,
            generator_params={
                "months": cfg.months,
                "total_leads": cfg.total_leads,
                "total_domains": cfg.total_domains,
                "total_buyers": cfg.total_buyers,
                "seed": cfg.seed,
            },
        )
        session.add(dataset)
        session.flush()
        print(f"[1/8] Dataset record created: {dataset_id}")

        # 2. Generate buyers
        buyers_data = generate_buyers(cfg)
        for b in buyers_data:
            session.add(DsBuyer(dataset_id=dataset_id, **b))
        session.flush()
        print(f"[2/8] Buyers: {len(buyers_data)} generated")

        # 3. Generate servers
        servers_data = generate_servers(cfg)
        for s in servers_data:
            session.add(DsServer(dataset_id=dataset_id, **s))
        session.flush()
        print(f"[3/8] Servers: {len(servers_data)} generated")

        # 4. Generate domains
        domains_data = generate_domains(cfg, buyers_data, servers_data)
        for d in domains_data:
            session.add(DsDomain(dataset_id=dataset_id, **d))
        session.flush()
        print(f"[4/8] Domains: {len(domains_data)} generated")

        # 5. Generate offers
        offers_data = generate_offers(cfg)
        for o in offers_data:
            # Remove 'type' field — not in DB schema, used only for financials
            o_copy = {k: v for k, v in o.items() if k != "type"}
            session.add(DsOffer(dataset_id=dataset_id, **o_copy))
        session.flush()
        print(f"[5/8] Offers: {len(offers_data)} generated")

        # 6. Generate leads
        leads_data = generate_leads(cfg, buyers_data, domains_data, offers_data)
        # Batch insert for performance
        batch_size = 1000
        for i in range(0, len(leads_data), batch_size):
            batch = leads_data[i:i + batch_size]
            for l in batch:
                session.add(DsLead(dataset_id=dataset_id, **l))
            session.flush()
        print(f"[6/8] Leads: {len(leads_data)} generated")

        # 7. Generate financials
        incomes_data, expenses_data = generate_financials(
            cfg, buyers_data, leads_data, offers_data, domains_data, servers_data
        )
        for inc in incomes_data:
            session.add(DsIncome(dataset_id=dataset_id, **inc))
        for exp in expenses_data:
            session.add(DsExpense(dataset_id=dataset_id, **exp))
        session.flush()
        print(f"[7/8] Financials: {len(incomes_data)} incomes, {len(expenses_data)} expenses")

        # 8. Update dataset record count
        total_records = (
            len(buyers_data) + len(servers_data) + len(domains_data) +
            len(offers_data) + len(leads_data) + len(incomes_data) + len(expenses_data)
        )
        dataset.record_count = total_records

        session.commit()
        print(f"[8/8] Committed to PostgreSQL. Total records: {total_records}")

        # Export training data to JSONL
        export_dir = Path(__file__).resolve().parent.parent.parent / "data" / "datasets" / cfg.version
        export_dir.mkdir(parents=True, exist_ok=True)

        training_pairs = generate_training_data(
            buyers_data, leads_data, offers_data,
            incomes_data, expenses_data, domains_data, servers_data
        )
        jsonl_path = export_dir / "training.jsonl"
        with open(jsonl_path, "w") as f:
            for pair in training_pairs:
                f.write(json.dumps(pair, cls=DecimalEncoder) + "\n")
        print(f"\nExported {len(training_pairs)} training pairs to {jsonl_path}")

        # Export summary
        summary = {
            "dataset_id": dataset_id,
            "version": cfg.version,
            "seed": cfg.seed,
            "generated_at": datetime.now().isoformat(),
            "synthetic_data_disclaimer": "ALL DATA IS 100% SYNTHETIC — FOR DEMONSTRATION AND EDUCATIONAL PURPOSES ONLY",
            "counts": {
                "buyers": len(buyers_data),
                "servers": len(servers_data),
                "domains": len(domains_data),
                "offers": len(offers_data),
                "leads": len(leads_data),
                "incomes": len(incomes_data),
                "expenses": len(expenses_data),
                "training_pairs": len(training_pairs),
                "total": total_records,
            },
        }
        summary_path = export_dir / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Exported summary to {summary_path}")

        print(f"\n{'='*60}")
        print(f"  Generation complete!")
        print(f"  Dataset: {cfg.dataset_name} {cfg.version}")
        print(f"  Records: {total_records:,}")
        print(f"{'='*60}\n")

    except Exception as e:
        session.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="AI OpsCtl Synthetic Data Generator")
    parser.add_argument("--version", default="v1.0.0", help="Dataset version (semver)")
    parser.add_argument("--months", type=int, default=12, help="Months of data")
    parser.add_argument("--leads", type=int, default=30000, help="Total leads")
    parser.add_argument("--domains", type=int, default=200, help="Total domains")
    parser.add_argument("--buyers", type=int, default=15, help="Total buyers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--name", default="Affiliate Marketing Demo", help="Dataset name")

    args = parser.parse_args()

    cfg = GeneratorConfig(
        version=args.version,
        months=args.months,
        total_leads=args.leads,
        total_domains=args.domains,
        total_buyers=args.buyers,
        seed=args.seed,
        dataset_name=args.name,
    )

    run(cfg)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all tests**

```bash
cd ml && python -m pytest tests/test_generator.py -v
```

Expected: All 18 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add ml/seeds/training_data.py ml/seeds/generator.py
git commit -m "feat: main generator entry point + Q&A training data export to JSONL"
```

---

### Task 8: End-to-End Test — Generate Dataset v1.0.0

**Files:** None (integration test using existing code)

- [ ] **Step 1: Ensure infra is running**

```bash
cd ~/Projects/work/opsctl/ai-opsctl
make infra
```

Expected: PostgreSQL and ChromaDB containers running.

- [ ] **Step 2: Run Prisma migration**

```bash
cd backend && npx prisma migrate dev --name init
```

Expected: 13 tables created.

- [ ] **Step 3: Run the generator**

```bash
cd ~/Projects/work/opsctl/ai-opsctl/ml
source .venv/bin/activate
python seeds/generator.py --version v1.0.0 --months 12 --leads 30000 --seed 42
```

Expected output:
```
============================================================
  AI OpsCtl — Synthetic Data Generator
  Version: v1.0.0 | Seed: 42
  ALL DATA IS 100% SYNTHETIC — FOR DEMONSTRATION ONLY
============================================================

[1/8] Dataset record created: c...
[2/8] Buyers: 15 generated
[3/8] Servers: 15 generated
[4/8] Domains: 200 generated
[5/8] Offers: ... generated
[6/8] Leads: 30000 generated
[7/8] Financials: ... incomes, ... expenses
[8/8] Committed to PostgreSQL. Total records: ...

Exported ... training pairs to .../data/datasets/v1.0.0/training.jsonl
Exported summary to .../data/datasets/v1.0.0/summary.json

============================================================
  Generation complete!
  Dataset: Affiliate Marketing Demo v1.0.0
  Records: ...
============================================================
```

- [ ] **Step 4: Verify data in PostgreSQL**

```bash
docker exec -it ai-opsctl-postgres psql -U opsctl -d ai_opsctl -c "
  SELECT 'datasets' as t, count(*) FROM datasets
  UNION ALL SELECT 'buyers', count(*) FROM ds_buyers
  UNION ALL SELECT 'servers', count(*) FROM ds_servers
  UNION ALL SELECT 'domains', count(*) FROM ds_domains
  UNION ALL SELECT 'offers', count(*) FROM ds_offers
  UNION ALL SELECT 'leads', count(*) FROM ds_leads
  UNION ALL SELECT 'incomes', count(*) FROM ds_incomes
  UNION ALL SELECT 'expenses', count(*) FROM ds_expenses;
"
```

Expected: datasets=1, buyers=15, servers=15, domains=200, leads=30000, offers>12, incomes>0, expenses>0.

- [ ] **Step 5: Verify training data export**

```bash
wc -l data/datasets/v1.0.0/training.jsonl
cat data/datasets/v1.0.0/summary.json
```

Expected: training.jsonl with 20+ lines, summary.json with all counts.

- [ ] **Step 6: Verify determinism — regenerate with same seed**

```bash
cd ml
python seeds/generator.py --version v1.0.1 --months 12 --leads 1000 --seed 42
```

Then compare summary files — same seed should produce same buyer tags, same domain names, same distribution.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: Phase 1 complete — infrastructure + fake data generator producing 30K synthetic leads"
```

---

## Phase 1 Completion Checklist

- [ ] Docker Compose: PostgreSQL + ChromaDB running
- [ ] Prisma schema: 13 tables migrated
- [ ] Seed generator: deterministic, 30K leads, 12 months, 3 verticals
- [ ] Training data: JSONL exported for fine-tuning
- [ ] Tests: 18 unit tests passing
- [ ] All data marked as synthetic (generator output, summary.json, README)
- [ ] Git: clean history with atomic commits
