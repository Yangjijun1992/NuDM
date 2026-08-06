import uuid
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.social import AuditLog
from app.core.database import async_session_factory

logger = logging.getLogger("nudm.audit")


async def write_audit_log(
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    try:
        async with async_session_factory() as db:
            log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                detail=detail,
                ip_address=ip_address,
            )
            db.add(log)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


async def log_user_action(
    user_id: uuid.UUID,
    action: str,
    entity_type: str = "user",
    entity_id: uuid.UUID | None = None,
    ip_address: str | None = None,
):
    await write_audit_log(user_id, action, entity_type, entity_id, None, ip_address)


async def log_admin_action(
    admin_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
):
    await write_audit_log(admin_id, action, entity_type, entity_id, detail, ip_address)
