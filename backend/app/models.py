import os
from datetime import date
from sqlalchemy import create_engine, ForeignKey, String, Date, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///./finance.db'), connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, default='Демо-пользователь')

class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

class Transaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), default=1)
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(500))
    # Храним деньги в минимальных единицах, чтобы избежать ошибок float.
    amount_minor: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String)
    category_id: Mapped[int | None] = mapped_column(ForeignKey('categories.id'), nullable=True)
    source: Mapped[str] = mapped_column(String, default='pending')

class InsightCache(Base):
    __tablename__ = 'insight_cache'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    payload: Mapped[str] = mapped_column(Text)
