-- CreateEnum
CREATE TYPE "DatasetStatus" AS ENUM ('DRAFT', 'ACTIVE', 'ARCHIVED');

-- CreateEnum
CREATE TYPE "TrainingStatus" AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');

-- CreateEnum
CREATE TYPE "RagStatus" AS ENUM ('INDEXING', 'READY', 'FAILED');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "login" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "language" TEXT NOT NULL DEFAULT 'en',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "conversations" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "title" TEXT NOT NULL DEFAULT 'New conversation',
    "model_version" TEXT,
    "dataset_version" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "conversations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "messages" (
    "id" TEXT NOT NULL,
    "conversation_id" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "tokens_in" INTEGER,
    "tokens_out" INTEGER,
    "latency_ms" INTEGER,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "messages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "datasets" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "description" TEXT,
    "status" "DatasetStatus" NOT NULL DEFAULT 'DRAFT',
    "record_count" INTEGER NOT NULL DEFAULT 0,
    "date_range_start" TIMESTAMP(3),
    "date_range_end" TIMESTAMP(3),
    "generator_params" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "datasets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "dataset_metadata" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "value" JSONB NOT NULL,

    CONSTRAINT "dataset_metadata_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_buyers" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "tag" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "team" TEXT NOT NULL,
    "vertical" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "ds_buyers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_servers" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "ip" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "location" TEXT NOT NULL,
    "monthly_cost" DECIMAL(10,2) NOT NULL,
    "domain_count" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL DEFAULT 'active',

    CONSTRAINT "ds_servers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_domains" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "domain_name" TEXT NOT NULL,
    "server_id" TEXT,
    "buyer_id" TEXT,
    "status" TEXT NOT NULL DEFAULT 'active',
    "geo" TEXT,
    "tld" TEXT NOT NULL,
    "registrar" TEXT NOT NULL DEFAULT 'Namecheap',
    "monthly_cost" DECIMAL(10,2) NOT NULL,
    "created_date" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ds_domains_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_offers" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "vertical" TEXT NOT NULL,
    "geo" TEXT NOT NULL,
    "lang" TEXT NOT NULL,
    "conversion_rate" DECIMAL(5,4) NOT NULL,
    "payout_amount" DECIMAL(10,2) NOT NULL,
    "payout_currency" TEXT NOT NULL DEFAULT 'USD',

    CONSTRAINT "ds_offers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_leads" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "domain_id" TEXT,
    "offer_id" TEXT,
    "buyer_id" TEXT,
    "geo" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone" TEXT NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'organic',
    "crm_status" TEXT NOT NULL DEFAULT 'success',
    "is_test" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ds_leads_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_expenses" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "buyer_id" TEXT,
    "category" TEXT NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "date" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ds_expenses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ds_incomes" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "buyer_id" TEXT,
    "offer_id" TEXT,
    "geo" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "date" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ds_incomes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "training_runs" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "model_base" TEXT NOT NULL,
    "adapter_name" TEXT NOT NULL,
    "hyperparams" JSONB NOT NULL,
    "metrics" JSONB,
    "status" "TrainingStatus" NOT NULL DEFAULT 'PENDING',
    "started_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "duration_sec" INTEGER,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "training_comparisons" (
    "id" TEXT NOT NULL,
    "run_a_id" TEXT NOT NULL,
    "run_b_id" TEXT NOT NULL,
    "comparison_notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_comparisons_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "rag_collections" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "doc_count" INTEGER NOT NULL DEFAULT 0,
    "embedding_model" TEXT NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    "status" "RagStatus" NOT NULL DEFAULT 'INDEXING',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "rag_collections_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_login_key" ON "users"("login");

-- CreateIndex
CREATE INDEX "conversations_user_id_created_at_idx" ON "conversations"("user_id", "created_at");

-- CreateIndex
CREATE INDEX "messages_conversation_id_created_at_idx" ON "messages"("conversation_id", "created_at");

-- CreateIndex
CREATE UNIQUE INDEX "datasets_name_version_key" ON "datasets"("name", "version");

-- CreateIndex
CREATE UNIQUE INDEX "dataset_metadata_dataset_id_key_key" ON "dataset_metadata"("dataset_id", "key");

-- CreateIndex
CREATE INDEX "ds_buyers_dataset_id_idx" ON "ds_buyers"("dataset_id");

-- CreateIndex
CREATE INDEX "ds_servers_dataset_id_idx" ON "ds_servers"("dataset_id");

-- CreateIndex
CREATE INDEX "ds_domains_dataset_id_idx" ON "ds_domains"("dataset_id");

-- CreateIndex
CREATE INDEX "ds_domains_buyer_id_idx" ON "ds_domains"("buyer_id");

-- CreateIndex
CREATE INDEX "ds_offers_dataset_id_idx" ON "ds_offers"("dataset_id");

-- CreateIndex
CREATE INDEX "ds_leads_dataset_id_created_at_idx" ON "ds_leads"("dataset_id", "created_at");

-- CreateIndex
CREATE INDEX "ds_leads_buyer_id_idx" ON "ds_leads"("buyer_id");

-- CreateIndex
CREATE INDEX "ds_leads_geo_idx" ON "ds_leads"("geo");

-- CreateIndex
CREATE INDEX "ds_leads_crm_status_idx" ON "ds_leads"("crm_status");

-- CreateIndex
CREATE INDEX "ds_expenses_dataset_id_date_idx" ON "ds_expenses"("dataset_id", "date");

-- CreateIndex
CREATE INDEX "ds_expenses_buyer_id_idx" ON "ds_expenses"("buyer_id");

-- CreateIndex
CREATE INDEX "ds_incomes_dataset_id_date_idx" ON "ds_incomes"("dataset_id", "date");

-- CreateIndex
CREATE INDEX "ds_incomes_buyer_id_idx" ON "ds_incomes"("buyer_id");

-- CreateIndex
CREATE INDEX "ds_incomes_geo_idx" ON "ds_incomes"("geo");

-- CreateIndex
CREATE INDEX "training_runs_dataset_id_idx" ON "training_runs"("dataset_id");

-- CreateIndex
CREATE INDEX "training_runs_status_idx" ON "training_runs"("status");

-- CreateIndex
CREATE INDEX "rag_collections_dataset_id_idx" ON "rag_collections"("dataset_id");

-- AddForeignKey
ALTER TABLE "conversations" ADD CONSTRAINT "conversations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "messages" ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "dataset_metadata" ADD CONSTRAINT "dataset_metadata_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_buyers" ADD CONSTRAINT "ds_buyers_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_servers" ADD CONSTRAINT "ds_servers_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_domains" ADD CONSTRAINT "ds_domains_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_domains" ADD CONSTRAINT "ds_domains_server_id_fkey" FOREIGN KEY ("server_id") REFERENCES "ds_servers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_domains" ADD CONSTRAINT "ds_domains_buyer_id_fkey" FOREIGN KEY ("buyer_id") REFERENCES "ds_buyers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_offers" ADD CONSTRAINT "ds_offers_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_leads" ADD CONSTRAINT "ds_leads_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_leads" ADD CONSTRAINT "ds_leads_domain_id_fkey" FOREIGN KEY ("domain_id") REFERENCES "ds_domains"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_leads" ADD CONSTRAINT "ds_leads_offer_id_fkey" FOREIGN KEY ("offer_id") REFERENCES "ds_offers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_leads" ADD CONSTRAINT "ds_leads_buyer_id_fkey" FOREIGN KEY ("buyer_id") REFERENCES "ds_buyers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_expenses" ADD CONSTRAINT "ds_expenses_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_expenses" ADD CONSTRAINT "ds_expenses_buyer_id_fkey" FOREIGN KEY ("buyer_id") REFERENCES "ds_buyers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_incomes" ADD CONSTRAINT "ds_incomes_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_incomes" ADD CONSTRAINT "ds_incomes_buyer_id_fkey" FOREIGN KEY ("buyer_id") REFERENCES "ds_buyers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ds_incomes" ADD CONSTRAINT "ds_incomes_offer_id_fkey" FOREIGN KEY ("offer_id") REFERENCES "ds_offers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "training_runs" ADD CONSTRAINT "training_runs_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "training_comparisons" ADD CONSTRAINT "training_comparisons_run_a_id_fkey" FOREIGN KEY ("run_a_id") REFERENCES "training_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "training_comparisons" ADD CONSTRAINT "training_comparisons_run_b_id_fkey" FOREIGN KEY ("run_b_id") REFERENCES "training_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "rag_collections" ADD CONSTRAINT "rag_collections_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;
