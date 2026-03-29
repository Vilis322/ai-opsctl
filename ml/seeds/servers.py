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
            "domain_count": 0,
            "status": "active",
        })

    return servers
