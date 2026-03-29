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

    offer_map = {o["id"]: o for o in offers}

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
            "date": datetime(year, month, 15),
        })

    # === EXPENSES: monthly per buyer ===
    end_date = datetime(2026, 3, 1)
    start_date = end_date - timedelta(days=30 * cfg.months)

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
                if random.random() < 0.15:
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

        # Server costs (not per buyer)
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
