# OpsCtl AI

ML/AI analytics platform for the OpsCtl ecosystem — predictive analytics, lead scoring, and automated reporting.

## Overview

OpsCtl AI processes data from all ecosystem services to generate actionable insights. Currently in active development — runs locally with Ollama for inference.

## Planned Features

- **Lead Scoring** — quality prediction based on source, geo, and behavioral signals
- **Financial Anomaly Detection** — automated flagging of unusual transactions
- **Report Generation** — AI-powered weekly/monthly summaries
- **Domain Performance Analytics** — conversion and uptime correlation
- **RAG Knowledge Base** — natural language queries over internal documentation

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| API | FastAPI |
| Inference | Ollama (local), Claude API (cloud) |
| Models | Llama 3.1 (local), Claude Sonnet (cloud) |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |

## Status

In development. Not yet deployed to demo infrastructure.

Demo placeholder: [ai.opsctl.tech](https://ai.opsctl.tech)

## Author

Kyrylo Pryiomyshev — [GitHub](https://github.com/Vilis322)

## License

All rights reserved.
