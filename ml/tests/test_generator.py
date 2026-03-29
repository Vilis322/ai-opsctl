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
