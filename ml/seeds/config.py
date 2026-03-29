"""Seed generator configuration — all generation parameters."""

from dataclasses import dataclass, field


@dataclass
class GeneratorConfig:
    """Parameters for fake dataset generation."""
    version: str = "v1.0.0"
    months: int = 12
    total_leads: int = 30000
    total_domains: int = 200
    total_buyers: int = 15
    total_servers: int = 15
    seed: int = 42
    dataset_name: str = "Affiliate Marketing Demo"

    # Vertical distribution
    verticals: dict = field(default_factory=lambda: {
        "saas": 0.35,
        "ecom": 0.35,
        "fintech": 0.30,
    })

    # Buyer tags per vertical
    buyer_tags: dict = field(default_factory=lambda: {
        "saas": ["Maxwell", "Harper", "Quinn", "Reese", "Avery"],
        "ecom": ["Jordan", "Blake", "Cameron", "Morgan", "Riley"],
        "fintech": ["Spencer", "Emerson", "Parker", "Sloane", "Kendall"],
    })

    # Offers per vertical
    offers: dict = field(default_factory=lambda: {
        "saas": [
            {"name": "CloudSync Pro", "geos": ["US", "UK", "DE", "CA"], "payout_range": (40, 80), "type": "cpl"},
            {"name": "DataVault", "geos": ["US", "UK", "DE"], "payout_range": (50, 90), "type": "cpl"},
            {"name": "TaskFlow", "geos": ["US", "CA", "AU"], "payout_range": (35, 70), "type": "cpl"},
            {"name": "CodeMetrics", "geos": ["US", "UK", "DE", "FR"], "payout_range": (45, 85), "type": "cpl"},
        ],
        "ecom": [
            {"name": "ShopNest", "geos": ["US", "UK", "AU", "FR"], "payout_range": (8, 25), "type": "cpa"},
            {"name": "DealHunter", "geos": ["US", "UK", "DE", "JP"], "payout_range": (10, 22), "type": "cpa"},
            {"name": "PriceRadar", "geos": ["US", "UK", "AU"], "payout_range": (12, 28), "type": "cpa"},
            {"name": "StyleBox", "geos": ["US", "FR", "JP", "DE"], "payout_range": (15, 30), "type": "cpa"},
        ],
        "fintech": [
            {"name": "WealthBridge", "geos": ["UK", "DE", "CH", "SG"], "payout_range": (80, 200), "type": "cpa"},
            {"name": "PayStream", "geos": ["UK", "DE", "AU"], "payout_range": (90, 180), "type": "cpa"},
            {"name": "CryptoEdge", "geos": ["UK", "CH", "SG", "AU"], "payout_range": (100, 220), "type": "cpa"},
            {"name": "LoanFlex", "geos": ["UK", "DE", "AU", "SG"], "payout_range": (70, 160), "type": "cpa"},
        ],
    })

    # Geo to language mapping
    geo_lang: dict = field(default_factory=lambda: {
        "US": "en", "UK": "en", "CA": "en", "AU": "en",
        "DE": "de", "CH": "de", "FR": "fr", "JP": "ja", "SG": "en",
    })

    # Geo to Faker locale mapping
    geo_locale: dict = field(default_factory=lambda: {
        "US": "en_US", "UK": "en_GB", "CA": "en_CA", "AU": "en_AU",
        "DE": "de_DE", "CH": "de_CH", "FR": "fr_FR", "JP": "ja_JP", "SG": "en_US",
    })

    # Conversion rates per vertical (min, max)
    conversion_rates: dict = field(default_factory=lambda: {
        "saas": (0.02, 0.05),
        "ecom": (0.03, 0.08),
        "fintech": (0.01, 0.03),
    })

    # CRM status distribution
    crm_status_weights: dict = field(default_factory=lambda: {
        "success": 0.85,
        "fail": 0.10,
        "duplicate": 0.05,
    })

    # Seasonality multipliers (month 1-12)
    seasonality: list = field(default_factory=lambda: [
        0.75, 0.80, 0.90, 0.95, 1.00, 1.00,
        0.90, 0.95, 1.05, 1.15, 1.30, 1.25,
    ])

    # Domain TLD distribution
    tld_weights: dict = field(default_factory=lambda: {
        ".com": 0.40, ".io": 0.20, ".co": 0.15, ".app": 0.10, ".dev": 0.15,
    })

    # Server providers
    server_providers: list = field(default_factory=lambda: [
        {"name": "DigitalOcean", "locations": ["NYC", "AMS", "SIN"], "cost_range": (12, 24)},
        {"name": "Hetzner", "locations": ["FRA", "HEL"], "cost_range": (8, 18)},
        {"name": "Linode", "locations": ["FRA", "SIN", "SYD"], "cost_range": (10, 20)},
        {"name": "Vultr", "locations": ["NYC", "AMS", "SYD", "NRT"], "cost_range": (11, 22)},
    ])

    # Expense categories with monthly ranges per buyer
    expense_categories: dict = field(default_factory=lambda: {
        "domains": (200, 600),
        "servers": (150, 400),
        "tools": (50, 200),
        "advertising": (500, 3000),
        "team": (100, 500),
    })

    # Fired buyer config
    fired_buyer_month: int = 8
    fired_buyer_tag: str = "Kendall"
