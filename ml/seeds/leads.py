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
    """Generate lead records with seasonality, geo-appropriate names, CRM status distribution."""
    leads = []
    fakers: dict[str, Faker] = {}

    # Build Faker instances per locale
    for geo, locale in cfg.geo_locale.items():
        if locale not in fakers:
            fakers[locale] = Faker(locale)
            Faker.seed(cfg.seed)

    default_faker = Faker("en_US")

    active_buyers = [b for b in buyers if b["is_active"]]
    active_domains = [d for d in domains if d["status"] == "active"]

    # Map offers by geo
    offers_by_geo: dict[str, list[dict]] = {}
    for offer in offers:
        offers_by_geo.setdefault(offer["geo"], []).append(offer)

    # Date range
    end_date = datetime(2026, 3, 1)
    start_date = end_date - timedelta(days=30 * cfg.months)

    # Build list of calendar months covered by the generation window
    month_calendar = []
    for i in range(cfg.months):
        m = (start_date.month + i - 1) % 12 + 1
        month_calendar.append(m)

    # Calculate leads per month using seasonality keyed by calendar month
    season_weights = [cfg.seasonality[m - 1] for m in month_calendar]
    total_weight = sum(season_weights)
    leads_per_month = []
    remaining = cfg.total_leads
    for i in range(cfg.months):
        if i == cfg.months - 1:
            count = remaining
        else:
            count = round(cfg.total_leads * season_weights[i] / total_weight)
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

        # Filter out fired buyer after their month (calendar month comparison)
        available_buyers = []
        for b in buyers:
            if b["tag"] == cfg.fired_buyer_tag and month_num > cfg.fired_buyer_month:
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
                "is_test": random.random() < 0.02,
                "created_at": created,
            })

    return leads
