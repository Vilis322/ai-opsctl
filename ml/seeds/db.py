"""SQLAlchemy connection and table models for seed generator."""

from sqlalchemy import (
    create_engine, Column, String, Boolean, Integer, DateTime, Numeric,
    JSON, ForeignKey, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsctl:opsctl_dev@localhost:5433/ai_opsctl"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="DRAFT")
    record_count = Column(Integer, default=0)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    generator_params = Column(JSON)
    created_at = Column(DateTime, server_default=text("NOW()"))


class DsBuyer(Base):
    __tablename__ = "ds_buyers"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String, nullable=False)
    name = Column(String, nullable=False)
    team = Column(String, nullable=False)
    vertical = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class DsServer(Base):
    __tablename__ = "ds_servers"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    ip = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    location = Column(String, nullable=False)
    monthly_cost = Column(Numeric(10, 2), nullable=False)
    domain_count = Column(Integer, default=0)
    status = Column(String, default="active")


class DsDomain(Base):
    __tablename__ = "ds_domains"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    domain_name = Column(String, nullable=False)
    server_id = Column(String, ForeignKey("ds_servers.id", ondelete="SET NULL"))
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    status = Column(String, default="active")
    geo = Column(String)
    tld = Column(String, nullable=False)
    registrar = Column(String, default="Namecheap")
    monthly_cost = Column(Numeric(10, 2), nullable=False)
    created_date = Column(DateTime, nullable=False)


class DsOffer(Base):
    __tablename__ = "ds_offers"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    vertical = Column(String, nullable=False)
    geo = Column(String, nullable=False)
    lang = Column(String, nullable=False)
    conversion_rate = Column(Numeric(5, 4), nullable=False)
    payout_amount = Column(Numeric(10, 2), nullable=False)
    payout_currency = Column(String, default="USD")


class DsLead(Base):
    __tablename__ = "ds_leads"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(String, ForeignKey("ds_domains.id", ondelete="SET NULL"))
    offer_id = Column(String, ForeignKey("ds_offers.id", ondelete="SET NULL"))
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    geo = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    source = Column(String, default="organic")
    crm_status = Column(String, default="success")
    is_test = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)


class DsExpense(Base):
    __tablename__ = "ds_expenses"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    date = Column(DateTime, nullable=False)


class DsIncome(Base):
    __tablename__ = "ds_incomes"
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(String, ForeignKey("ds_buyers.id", ondelete="SET NULL"))
    offer_id = Column(String, ForeignKey("ds_offers.id", ondelete="SET NULL"))
    geo = Column(String, nullable=False)
    type = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    date = Column(DateTime, nullable=False)


def get_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def clear_dataset(session: Session, dataset_id: str) -> None:
    """Delete all records for a dataset (cascade handled by FK)."""
    session.query(Dataset).filter(Dataset.id == dataset_id).delete()
    session.commit()
