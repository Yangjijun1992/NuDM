import pytest
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.schemas.common import PaginatedResponse
from app.schemas.paper import PaperListItem, PaperDetail, AISummaryBrief
from app.schemas.topic import TopicResponse, TopicDetail
from app.schemas.favorite import FavoriteResponse
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.schemas.admin import AdminStatsResponse, CrawlTaskResponse, DataSourceResponse


class TestAuthSchemas:
    def test_user_create_validation(self):
        data = UserCreate(email="test@test.com", username="test", password="secret123")
        assert data.email == "test@test.com"
        assert data.username == "test"

    def test_user_response_from_attributes(self):
        user = UserResponse(
            id="uuid",
            email="a@b.com",
            username="user",
            avatar_url=None,
            role="user",
            created_at="2024-01-01T00:00:00",
        )
        assert user.role == "user"
        assert user.avatar_url is None

    def test_token_response(self):
        token = TokenResponse(
            access_token="abc123",
            user=UserResponse(
                id="u1", email="a@b.com", username="u",
                avatar_url=None, role="user", created_at="2024-01-01T00:00:00",
            ),
        )
        assert token.token_type == "bearer"
        assert token.user.username == "u"


class TestPaginatedResponse:
    def test_generic_paginated(self):
        resp = PaginatedResponse[PaperListItem](
            items=[], total=0, page=1, page_size=20, total_pages=0
        )
        assert resp.total == 0
        assert resp.page == 1

    def test_paginated_with_items(self):
        item = PaperListItem(
            id="p1",
            title="Test Paper",
            title_en=None,
            abstract=None,
            doi=None,
            arxiv_id="2301.00001",
            publish_date="2024-01-01",
            citation_count=10,
            language="en",
            relevance_score=0.85,
            hot_score=None,
            created_at="2024-01-01T00:00:00",
        )
        resp = PaginatedResponse[PaperListItem](
            items=[item], total=1, page=1, page_size=20, total_pages=1
        )
        assert len(resp.items) == 1
        assert resp.items[0].arxiv_id == "2301.00001"


class TestPaperSchemas:
    def test_paper_list_item(self):
        p = PaperListItem(
            id="p1",
            title="A Paper on Dark Matter",
            title_en=None,
            abstract="Abstract text...",
            doi="10.1234/foo",
            arxiv_id="2401.00001",
            publish_date="2024-01-01",
            citation_count=5,
            language="en",
            relevance_score=0.9,
            hot_score=3.2,
            created_at="2024-01-01T00:00:00",
        )
        assert p.relevance_score == 0.9
        assert p.citation_count == 5

    def test_paper_detail_with_authors(self):
        from app.schemas.paper import AuthorOnPaper
        ai_summary = AISummaryBrief(
            summary_cn="中文摘要",
            summary_en="English summary",
            contribution="Main contribution",
            method="Method description",
            result="Results",
            keywords_extracted=["dark matter", "WIMP"],
        )
        p = PaperDetail(
            id="p1",
            title="Test", title_en=None,
            abstract="abs", abstract_en="abs",
            doi=None, arxiv_id="2401.00001",
            publish_date="2024-01-01",
            citation_count=0,
            pdf_url=None, source_url=None,
            language="en",
            relevance_score=None, hot_score=None,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            authors=[
                AuthorOnPaper(
                    id="a1", name="John Doe", name_normalized="john doe",
                    affiliation="MIT", orcid=None, order=0,
                )
            ],
            topics=[],
            ai_summary=ai_summary,
        )
        assert len(p.authors) == 1
        assert p.authors[0].name == "John Doe"
        assert p.ai_summary.contribution == "Main contribution"


class TestNotificationSchema:
    def test_unread_count(self):
        c = UnreadCountResponse(count=5)
        assert c.count == 5

    def test_notification_response(self):
        n = NotificationResponse(
            id="n1",
            type="new_paper",
            title="New paper: Test",
            content="Paper content",
            reference_id="p1",
            reference_type="paper",
            is_read=False,
            created_at="2024-01-01T00:00:00",
            read_at=None,
        )
        assert n.type == "new_paper"
        assert not n.is_read


class TestAdminSchemas:
    def test_admin_stats(self):
        s = AdminStatsResponse(paper_count=100, user_count=10, source_count=2)
        assert s.paper_count == 100

    def test_crawl_task(self):
        t = CrawlTaskResponse(
            id="t1", source_id="s1", keyword="test",
            status="success", papers_fetched=50, papers_new=10,
            error_message=None,
            started_at="2024-01-01T00:00:00",
            finished_at="2024-01-01T00:05:00",
            created_at="2024-01-01T00:00:00",
        )
        assert t.status == "success"
        assert t.papers_new == 10


class TestSubscriptionSchemas:
    def test_subscription_create(self):
        s = SubscriptionCreate(type="topic", target_id="t1", frequency="daily")
        assert s.type == "topic"

    def test_subscription_response(self):
        s = SubscriptionResponse(
            id="s1", type="keyword", target_id=None,
            keyword="dark matter", frequency="daily",
            is_active=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert s.keyword == "dark matter"
