import pytest
from datetime import date
import uuid
from app.models.paper import Paper
from app.models.user import User
from app.models.topic import Topic
from app.models.datasource import DataSource
from app.models.social import Favorite, Subscription, Notification


class TestPaperModel:
    def test_create_paper(self):
        paper = Paper(
            id=uuid.uuid4(),
            title="Test Paper Title",
            arxiv_id="2501.00001",
            doi="10.1234/test",
            publish_date=date(2025, 1, 1),
            citation_count=0,
            language="en",
            is_hidden=False,
            relevance_score=0.85,
            hot_score=2.5,
        )
        assert paper.title == "Test Paper Title"
        assert paper.arxiv_id == "2501.00001"

    def test_paper_defaults(self):
        paper = Paper(
            title="Minimal Paper",
            citation_count=0,
            language="en",
            is_hidden=False,
        )
        assert paper.language == "en"
        assert paper.citation_count == 0
        assert paper.is_hidden is False


class TestUserModel:
    def test_create_user(self):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            role="user",
            is_active=True,
        )
        assert user.email == "test@example.com"

    def test_admin_user(self):
        user = User(
            email="admin@nudm.dev",
            username="admin",
            password_hash="hashed",
            role="admin",
            is_active=True,
        )
        assert user.role == "admin"


class TestTopicModel:
    def test_create_topic(self):
        topic = Topic(
            name="Dark Matter Direct Detection",
            slug="dark-matter-direct",
            description="Direct detection of dark matter",
            sort_order=1,
            keywords=["WIMP", "nuclear recoil", "liquid xenon"],
            paper_count=0,
            is_active=True,
        )
        assert topic.name == "Dark Matter Direct Detection"
        assert topic.slug == "dark-matter-direct"
        assert len(topic.keywords) == 3


class TestDataSourceModel:
    def test_create_data_source(self):
        ds = DataSource(
            name="arXiv",
            base_url="https://export.arxiv.org/api/query",
            api_type="arxiv",
            rate_limit=60,
            is_active=True,
        )
        assert ds.name == "arXiv"
        assert ds.api_type == "arxiv"


class TestFavoriteModel:
    def test_create_favorite(self):
        uid = uuid.uuid4()
        pid = uuid.uuid4()
        fav = Favorite(user_id=uid, paper_id=pid)
        assert fav.user_id == uid
        assert fav.paper_id == pid
        assert fav.note is None


class TestSubscriptionModel:
    def test_topic_subscription(self):
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        sub = Subscription(
            user_id=uid,
            type="topic",
            target_id=tid,
            frequency="daily",
            is_active=True,
        )
        assert sub.type == "topic"
        assert sub.frequency == "daily"

    def test_keyword_subscription(self):
        uid = uuid.uuid4()
        sub = Subscription(
            user_id=uid,
            type="keyword",
            keyword="dark matter",
            frequency="weekly",
            is_active=True,
        )
        assert sub.type == "keyword"
        assert sub.keyword == "dark matter"


class TestNotificationModel:
    def test_create_notification(self):
        uid = uuid.uuid4()
        pid = uuid.uuid4()
        notif = Notification(
            user_id=uid,
            type="new_paper",
            title="New paper published",
            reference_id=pid,
            reference_type="paper",
            is_read=False,
        )
        assert notif.type == "new_paper"
        assert notif.is_read is False
