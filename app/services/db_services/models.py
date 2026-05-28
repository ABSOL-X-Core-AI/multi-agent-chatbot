import enum
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Index,
    ForeignKey,
    Boolean,
)


class Base(DeclarativeBase):
    pass


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "documents_embedding_idx",
            embedding,
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_with={"lists": 100},
        ),
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    thread_id = Column(Text, primary_key=True)
    session_id = Column(Text, nullable=False, index=True)
    title = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship(
        "ChatHistory",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatHistory.created_at",
    )


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(Text, ForeignKey("chat_sessions.thread_id"), nullable=False)
    session_id = Column(Text, nullable=False, index=True)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    thread = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_history_thread_created", "thread_id", "created_at"),
    )
