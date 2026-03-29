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
    """Generate a unique brandable domain name. Returns (full_domain_name, tld)."""
    tlds = [".com", ".io", ".co", ".app", ".dev"]
    tld_weights = [0.40, 0.20, 0.15, 0.10, 0.15]

    for _ in range(100):
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
    """Generate domain records distributed across buyers and servers."""
    domains = []
    used_names: set[str] = set()
    active_buyers = [b for b in buyers if b["is_active"]]

    end_date = datetime(2026, 3, 1)
    start_date = end_date - timedelta(days=30 * cfg.months)

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

        days_offset = random.randint(0, (end_date - start_date).days)
        created = start_date + timedelta(days=days_offset)

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

        server["domain_count"] += 1

    return domains
