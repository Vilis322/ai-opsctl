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
