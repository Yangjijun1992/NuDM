"""
Database-type adapters that work on both PostgreSQL and SQLite.
Use these types instead of importing directly from sqlalchemy.dialects.postgresql.
"""
import json
import uuid as _uuid
from typing import Any

from sqlalchemy import String, Text, event
from sqlalchemy.types import TypeDecorator, CHAR
from app.core.config import settings


DB_IS_SQLITE = settings.is_sqlite()


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type in PG, falls back to CHAR(36) on SQLite.
    """
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid: bool = True):
        super().__init__(length=36)
        self.as_uuid = as_uuid

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, _uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not self.as_uuid:
            return value
        if dialect.name == "postgresql":
            return value
        return _uuid.UUID(value)


class JSONB(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL's JSONB type in PG, falls back to TEXT on SQLite
    with JSON serialization/deserialization.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value


class ARRAY(TypeDecorator):
    """Platform-independent ARRAY type.

    Uses PostgreSQL's ARRAY type in PG, falls back to TEXT on SQLite
    with JSON serialization.
    """
    impl = Text
    cache_ok = True

    def __init__(self, item_type=None):
        super().__init__()
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
            return dialect.type_descriptor(PG_ARRAY(String))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(value, list):
            return value
        return []
