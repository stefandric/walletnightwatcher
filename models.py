from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    address = Column(String(42), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_balance = Column(Float, default=0.0)

    __table_args__ = (UniqueConstraint('address', 'user_id', name='_user_wallet_uc'),)