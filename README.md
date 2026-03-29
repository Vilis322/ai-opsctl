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
