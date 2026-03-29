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
        start_month = 3 - cfg.months
        start_year = 2026
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start_date = datetime(start_year, start_month, 1)

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

        # 6. Generate leads (batch insert for performance)
        leads_data = generate_leads(cfg, buyers_data, domains_data, offers_data)
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
