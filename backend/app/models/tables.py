"""SQLAlchemy 2.0 schema for all 13 required tables.

Deletion rules (summary):
  - User-owned data (sessions, api_keys, conversations, messages) CASCADE on user delete.
  - Accounting/audit rows (inference_requests, usage_records, audit_logs) SET NULL on
    user/key delete so history and totals survive account removal.
  - Server -> models CASCADE; model -> permissions CASCADE.
"""
import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Index,
                        Integer, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, created_col, uuid_pk


class Role(str, enum.Enum):
    super_admin = "super_admin"
    user = "user"
    developer = "developer"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # Argon2id
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), default=Role.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    theme: Mapped[str] = mapped_column(String(10), default="system")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_col()
    sessions = relationship("Session", cascade="all, delete-orphan", passive_deletes=True)
    api_keys = relationship("ApiKey", cascade="all, delete-orphan", passive_deletes=True)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)  # SHA-256 of cookie value
    user_agent: Mapped[Optional[str]] = mapped_column(String(300))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_col()


class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    prefix: Mapped[str] = mapped_column(String(16))  # shown in UI, e.g. "amc_ab12cd34"
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)  # HMAC-SHA256(pepper, key)
    # Per-key permissions, e.g. {"endpoints": ["chat","embeddings"], "models": ["llama3.2:3b"]}
    permissions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    rate_limit_per_min: Mapped[Optional[int]] = mapped_column(Integer)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_col()


class OllamaServer(Base):
    __tablename__ = "ollama_servers"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True)
    base_url: Mapped[str] = mapped_column(String(300))  # admin-only; SSRF-validated
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown")  # healthy|unreachable|unknown
    last_health_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    resources: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)  # only what was measured
    created_at: Mapped[datetime] = created_col()
    models = relationship("AiModel", cascade="all, delete-orphan", passive_deletes=True)


class AiModel(Base):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("server_id", "name", name="uq_models_server_name"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    server_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ollama_servers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)  # e.g. llama3.2:3b
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    context_length: Mapped[Optional[int]] = mapped_column(Integer)
    # Raw metadata from Ollama /api/show; capabilities are only read from here or the catalogue
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    capabilities: Mapped[list[str]] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # visible to users
    max_concurrency: Mapped[Optional[int]] = mapped_column(Integer)
    installed_at: Mapped[datetime] = created_col()


class ModelPermission(Base):
    """Restricts a model to a role or a specific user. No rows => follows is_active only."""
    __tablename__ = "model_permissions"
    __table_args__ = (UniqueConstraint("model_id", "role", "user_id", name="uq_model_permissions_target"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), index=True)
    role: Mapped[Optional[Role]] = mapped_column(Enum(Role, name="role"))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = created_col()


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_user_updated", "user_id", "updated_at"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    model_name: Mapped[Optional[str]] = mapped_column(String(200))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # temperature, top_p...
    created_at: Mapped[datetime] = created_col()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    messages = relationship("Message", cascade="all, delete-orphan", passive_deletes=True, order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # system|user|assistant
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="complete")  # complete|interrupted|error
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_col()


class InferenceRequest(Base):
    __tablename__ = "inference_requests"
    __table_args__ = (Index("ix_inference_user_created", "user_id", "created_at"),)
    id: Mapped[uuid.UUID] = uuid_pk()  # also exposed as the request ID header
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("api_keys.id", ondelete="SET NULL"), index=True)
    server_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("ollama_servers.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(10))  # playground|api
    endpoint: Mapped[str] = mapped_column(String(40))
    model_name: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(20))  # success|error|timeout|cancelled|rate_limited
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    error_code: Mapped[Optional[str]] = mapped_column(String(60))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_col()


class UsageRecord(Base):
    """Daily rollup per user/model, so analytics never scan the raw request table."""
    __tablename__ = "usage_records"
    __table_args__ = (UniqueConstraint("user_id", "model_name", "day", name="uq_usage_user_model_day"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    model_name: Mapped[str] = mapped_column(String(200))
    day: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    requests: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    completion_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    total_latency_ms: Mapped[int] = mapped_column(BigInteger, default=0)


class RateLimitPolicy(Base):
    __tablename__ = "rate_limit_policies"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True)
    applies_to_role: Mapped[Optional[Role]] = mapped_column(Enum(Role, name="role"))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=30)
    monthly_token_quota: Mapped[Optional[int]] = mapped_column(BigInteger)  # None = unlimited
    max_concurrent: Mapped[int] = mapped_column(Integer, default=2)
    max_output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_col()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_created", "created_at"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)  # e.g. model.delete
    target_type: Mapped[Optional[str]] = mapped_column(String(40))
    target_id: Mapped[Optional[str]] = mapped_column(String(100))
    detail: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)  # never store secrets
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    created_at: Mapped[datetime] = created_col()


class PlatformSetting(Base):
    __tablename__ = "platform_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
