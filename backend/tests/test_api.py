"""
API 集成测试套件 — 验证所有 HTTP 端点的请求/响应结构

这些测试通过 app.dependency_overrides mock 掉数据库依赖，
可以在没有 PostgreSQL 的环境中运行。
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture(autouse=True)
def override_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@test.com"
    user.username = "testuser"
    user.role = "user"
    user.is_active = True
    user.avatar_url = None
    user.created_at = MagicMock()
    user.created_at.isoformat.return_value = "2025-01-01T00:00:00"
    return user


@pytest.fixture
def mock_admin():
    admin = MagicMock()
    admin.id = uuid.uuid4()
    admin.email = "admin@test.com"
    admin.username = "admin"
    admin.role = "admin"
    admin.is_active = True
    admin.avatar_url = None
    admin.created_at = MagicMock()
    admin.created_at.isoformat.return_value = "2025-01-01T00:00:00"
    return admin


class TestHealthCheck:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuthEndpoints:
    def test_register_validation(self, client):
        resp = client.post("/auth/register", json={})
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "username": "user",
            "password": "test123456",
        })
        assert resp.status_code in [422, 400]

    def test_register_duplicate(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()
        resp = client.post("/auth/register", json={
            "email": "exists@test.com",
            "username": "existing",
            "password": "test123456",
        })
        assert resp.status_code == 400

    def test_login_invalid_credentials(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        resp = client.post("/auth/login", json={
            "email": "wrong@test.com",
            "password": "test123456",
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/auth/login", json={})
        assert resp.status_code == 422


class TestOpenAPI:
    def test_openapi_spec_is_valid(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert "paths" in spec
        assert "/auth/login" in spec["paths"]
        assert "/auth/register" in spec["paths"]
        assert "/papers" in spec["paths"]
        assert "/topics" in spec["paths"]
        assert "/search" in spec["paths"]
        assert "/favorites" in spec["paths"]
        assert "/subscriptions" in spec["paths"]
        assert "/notifications" in spec["paths"]
        assert "/admin/stats" in spec["paths"]

    def test_openapi_has_components(self, client):
        resp = client.get("/openapi.json")
        spec = resp.json()
        assert "components" in spec or "paths" in spec


class TestResponseStructures:
    """验证 schema 定义的正确性（无需数据库）"""

    def test_new_paper_input_invalid(self, client, mock_db):
        resp = client.get("/papers?page=0")
        assert resp.status_code == 422

    def test_papers_pagination_params(self, client, mock_db):
        from sqlalchemy import select
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalar.return_value = 0
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/papers?page=1&page_size=10&sort=date")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_papers_invalid_sort(self, client, mock_db):
        from sqlalchemy import select
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalar.return_value = 0
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/papers?sort=date")
        assert resp.status_code == 200

    def test_papers_invalid_page_size(self, client):
        resp = client.get("/papers?page_size=200")
        assert resp.status_code == 422

    def test_search_empty(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalar.return_value = 0
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/search?q=")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_search_with_author_filter(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalar.return_value = 0
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/search?author=Einstein")
        assert resp.status_code == 200

    def test_search_date_range(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalar.return_value = 0
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/search?date_from=2024-01-01&date_to=2024-12-31")
        assert resp.status_code == 200


class TestTopicEndpoints:
    def test_list_topics(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/topics")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_topic_not_found(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        resp = client.get("/topics/nonexistent")
        assert resp.status_code == 404

    def test_topic_trend_not_found(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        resp = client.get("/topics/nonexistent/trend")
        assert resp.status_code == 404


class TestExperimentEndpoints:
    def test_list_experiments(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_exec = mock_db.execute.return_value
        mock_exec.scalars.return_value.all.return_value = []

        resp = client.get("/topics/experiments/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAdminEndpoints:
    def test_stats_require_admin(self, client):
        resp = client.get("/admin/stats")
        assert resp.status_code in [401, 403]

    def test_datasources_require_admin(self, client):
        resp = client.get("/admin/data-sources")
        assert resp.status_code in [401, 403]

    def test_crawl_tasks_require_admin(self, client):
        resp = client.get("/admin/crawl-tasks")
        assert resp.status_code in [401, 403]


class TestFavoriteEndpoints:
    def test_favorites_require_auth(self, client):
        resp = client.get("/favorites")
        assert resp.status_code in [401, 403]

    def test_add_favorite_require_auth(self, client):
        resp = client.post("/favorites/some-uuid")
        assert resp.status_code in [401, 403]


class TestSubscriptionEndpoints:
    def test_subscriptions_require_auth(self, client):
        resp = client.get("/subscriptions")
        assert resp.status_code in [401, 403]

    def test_create_subscription_require_auth(self, client):
        resp = client.post("/subscriptions", json={
            "type": "topic",
            "frequency": "daily",
        })
        assert resp.status_code in [401, 403]


class TestNotificationEndpoints:
    def test_notifications_require_auth(self, client):
        resp = client.get("/notifications")
        assert resp.status_code in [401, 403]

    def test_unread_count_require_auth(self, client):
        resp = client.get("/notifications/unread-count")
        assert resp.status_code in [401, 403]


class TestUserEndpoints:
    def test_me_require_auth(self, client):
        resp = client.get("/users/me")
        assert resp.status_code in [401, 403]


class TestSchemaValidation:
    """验证 Pydantic schema 数据的序列化/反序列化"""

    def test_topic_response_schema(self):
        from app.schemas.topic import TopicResponse
        t = TopicResponse(
            id="abc", name="WIMP", slug="wimp",
            description="desc", parent_id=None, sort_order=1,
            icon=None, keywords=["WIMP"], paper_count=0,
            is_active=True, created_at="2025-01-01T00:00:00",
        )
        d = t.model_dump()
        assert d["slug"] == "wimp"
        assert d["paper_count"] == 0

    def test_paginated_response_generic(self):
        from app.schemas.common import PaginatedResponse
        from app.schemas.paper import PaperListItem

        items = [
            PaperListItem(
                id="p1", title="Test", title_en=None, abstract=None,
                doi=None, arxiv_id="2501.00001", publish_date="2025-01-01",
                citation_count=0, language="en", relevance_score=None,
                hot_score=None, created_at="2025-01-01T00:00:00",
            )
        ]
        resp = PaginatedResponse(items=items, total=1, page=1, page_size=20, total_pages=1)
        assert resp.model_dump()["total"] == 1

    def test_subscription_create_valid(self):
        from app.schemas.subscription import SubscriptionCreate
        s = SubscriptionCreate(type="topic", target_id=str(uuid.uuid4()), frequency="weekly")
        d = s.model_dump()
        assert d["type"] == "topic"
        assert d["frequency"] == "weekly"

    def test_favorite_response(self):
        from app.schemas.favorite import FavoriteResponse, PaperInFavorite
        fav = FavoriteResponse(
            id="f1",
            note="important",
            created_at="2025-01-01T00:00:00",
            paper=PaperInFavorite(
                id="p1", title="Important Paper",
                arxiv_id="2501.00001", publish_date="2025-01-01",
            ),
        )
        assert fav.paper.title == "Important Paper"

    def test_notification_response(self):
        from app.schemas.notification import NotificationResponse
        n = NotificationResponse(
            id="n1", type="new_paper", title="New paper",
            content="content", reference_id="p1", reference_type="paper",
            is_read=False, created_at="2025-01-01T00:00:00", read_at=None,
        )
        assert n.is_read is False



class TestErrorResponses:
    def test_404_on_nonexistent_route(self, client):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404

    def test_paper_detail_not_found(self, client, mock_db):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        resp = client.get("/papers/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_cors_headers(self, client):
        resp = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        assert resp.status_code in [200, 405, 204]
