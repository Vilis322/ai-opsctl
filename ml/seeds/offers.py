"""Generate fake offer data."""

import random
from decimal import Decimal
from typing import Any
from .config import GeneratorConfig
from .buyers import _generate_cuid


def generate_offers(cfg: GeneratorConfig) -> list[dict[str, Any]]:
    """Generate offer records from config.

    Creates one offer record per (offer_name, geo) combination.
    Returns list of dicts with all offer fields.
    """
    offers = []

    for vertical, offer_configs in cfg.offers.items():
        conv_min, conv_max = cfg.conversion_rates[vertical]

        for offer_cfg in offer_configs:
            for geo in offer_cfg["geos"]:
                payout_min, payout_max = offer_cfg["payout_range"]
                lang = cfg.geo_lang.get(geo, "en")

                offers.append({
                    "id": _generate_cuid(),
                    "name": offer_cfg["name"],
                    "vertical": vertical,
                    "geo": geo,
                    "lang": lang,
                    "conversion_rate": Decimal(str(round(random.uniform(conv_min, conv_max), 4))),
                    "payout_amount": Decimal(str(round(random.uniform(payout_min, payout_max), 2))),
                    "payout_currency": "USD",
                    "type": offer_cfg["type"],
                })

    return offers
