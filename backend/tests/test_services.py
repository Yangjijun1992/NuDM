import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.notification import generate_notifications_for_paper


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_generate_notifications_no_subscriptions(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))

        count = await generate_notifications_for_paper(
            db, uuid.uuid4(), "Test Paper Title", "Test abstract"
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_generate_notifications_topic_match(self):
        db = AsyncMock()
        paper_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        user_id = uuid.uuid4()

        from app.models.social import Subscription
        from app.models.topic import PaperTopic

        sub = Subscription(user_id=user_id, type="topic", target_id=topic_id, frequency="daily", is_active=True)

        pt = PaperTopic(paper_id=paper_id, topic_id=topic_id, confidence=1.0)

        def execute_side_effect(stmt, **kwargs):
            mock = MagicMock()
            from sqlalchemy import select
            from sqlalchemy.sql import Select
            str_stmt = str(stmt)

            if "notifications" in str_stmt:
                mock.scalar_one_or_none = lambda: None
            elif "subscriptions" in str_stmt:
                mock.scalars = lambda: MagicMock(all=lambda: [sub])
            elif "paper_topics" in str_stmt:
                mock.scalars = lambda: MagicMock(all=lambda: [pt])
            return mock

        db.execute = AsyncMock(side_effect=execute_side_effect)
        db.add = MagicMock()

        count = await generate_notifications_for_paper(
            db, paper_id, "WIMP Search Results", "We searched for WIMP dark matter"
        )
        assert count > 0

    @pytest.mark.asyncio
    async def test_generate_notifications_keyword_match(self):
        db = AsyncMock()
        paper_id = uuid.uuid4()
        user_id = uuid.uuid4()

        from app.models.social import Subscription

        sub = Subscription(user_id=user_id, type="keyword", keyword="neutrino", frequency="daily", is_active=True)

        def execute_side_effect(stmt, **kwargs):
            mock = MagicMock()
            str_stmt = str(stmt)

            if "notifications" in str_stmt:
                mock.scalar_one_or_none = lambda: None
            elif "subscriptions" in str_stmt:
                mock.scalars = lambda: MagicMock(all=lambda: [sub])
            elif "paper_topics" in str_stmt:
                mock.scalars = lambda: MagicMock(all=lambda: [])
            return mock

        db.execute = AsyncMock(side_effect=execute_side_effect)
        db.add = MagicMock()

        count = await generate_notifications_for_paper(
            db, paper_id, "Neutrino Oscillation Study", "Neutrino physics beyond SM"
        )
        assert count > 0
