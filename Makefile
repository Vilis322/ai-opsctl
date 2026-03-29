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
