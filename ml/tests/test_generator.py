"""Tests for seed generator modules."""

import random
from seeds.config import GeneratorConfig
from seeds.buyers import generate_buyers
from seeds.servers import generate_servers
from seeds.domains import generate_domains


def test_generate_buyers_count():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    assert len(buyers) == 15


def test_generate_buyers_verticals():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    verticals = {b["vertical"] for b in buyers}
    assert verticals == {"saas", "ecom", "fintech"}


def test_generate_buyers_tags_unique():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    tags = [b["tag"] for b in buyers]
    assert len(tags) == len(set(tags))


def test_generate_buyers_fired():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    kendall = [b for b in buyers if b["tag"] == "Kendall"][0]
    assert kendall["is_active"] is False


def test_generate_servers_count():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    servers = generate_servers(cfg)
    assert len(servers) == 15


def test_generate_servers_providers():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    servers = generate_servers(cfg)
    providers = {s["provider"] for s in servers}
    assert providers.issubset({"DigitalOcean", "Hetzner", "Linode", "Vultr"})


def test_generate_domains_count():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    assert len(domains) == 200


def test_generate_domains_tlds():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    tlds = {d["tld"] for d in domains}
    assert tlds.issubset({".com", ".io", ".co", ".app", ".dev"})


def test_generate_domains_unique_names():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    names = [d["domain_name"] for d in domains]
    assert len(names) == len(set(names))


from seeds.offers import generate_offers
from seeds.leads import generate_leads


def test_generate_offers_per_vertical():
    cfg = GeneratorConfig(seed=42)
    random.seed(cfg.seed)
    offers = generate_offers(cfg)
    verticals = {o["vertical"] for o in offers}
    assert verticals == {"saas", "ecom", "fintech"}
    assert len(offers) >= 12


def test_generate_leads_count():
    cfg = GeneratorConfig(seed=42, total_leads=1000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)
    assert len(leads) == 1000


def test_generate_leads_crm_status_distribution():
    cfg = GeneratorConfig(seed=42, total_leads=10000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)

    statuses = [l["crm_status"] for l in leads]
    success_rate = statuses.count("success") / len(statuses)
    assert 0.80 < success_rate < 0.90


def test_generate_leads_seasonality():
    cfg = GeneratorConfig(seed=42, total_leads=10000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)

    nov_count = sum(1 for l in leads if l["created_at"].month == 11)
    jan_count = sum(1 for l in leads if l["created_at"].month == 1)
    assert nov_count > jan_count


def test_generate_leads_fired_buyer_no_late_leads():
    cfg = GeneratorConfig(seed=42, total_leads=5000)
    random.seed(cfg.seed)
    buyers = generate_buyers(cfg)
    servers = generate_servers(cfg)
    domains = generate_domains(cfg, buyers, servers)
    offers = generate_offers(cfg)
    leads = generate_leads(cfg, buyers, domains, offers)

    kendall = [b for b in buyers if b["tag"] == "Kendall"][0]
    kendall_leads = [l for l in leads if l["buyer_id"] == kendall["id"]]
    late_leads = [l for l in kendall_leads if l["created_at"].month > cfg.fired_buyer_month]
    assert len(late_leads) == 0
