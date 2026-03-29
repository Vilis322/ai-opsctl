"""Generate fake buyer data."""

import random
from typing import Any
from .config import GeneratorConfig


def _generate_cuid() -> str:
    """Generate a cuid-like ID."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "c" + "".join(random.choices(chars, k=24))


def generate_buyers(cfg: GeneratorConfig) -> list[dict[str, Any]]:
    """Generate buyer records from config.

    Returns list of dicts with keys: id, tag, name, team, vertical, is_active.
    """
    buyers = []

    team_names = {
        "saas": "SaaS Team",
        "ecom": "E-commerce Team",
        "fintech": "Fintech Team",
    }

    for vertical, tags in cfg.buyer_tags.items():
        for tag in tags:
            buyers.append({
                "id": _generate_cuid(),
                "tag": tag,
                "name": f"{tag} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Davis', 'Miller', 'Wilson'])}",
                "team": team_names[vertical],
                "vertical": vertical,
                "is_active": tag != cfg.fired_buyer_tag,
            })

    return buyers
