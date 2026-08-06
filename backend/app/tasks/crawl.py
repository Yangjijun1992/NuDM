"""Celery 抓取任务"""
import asyncio
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

RETRY_CONFIG = {
    "autoretry_for": (Exception,),
    "max_retries": 3,
    "retry_backoff": True,
    "retry_backoff_max": 600,
    "retry_jitter": True,
}


@celery_app.task(name="app.tasks.crawl.crawl_all", **RETRY_CONFIG)
def crawl_all():
    """执行全量抓取管道（arXiv + INSPIRE）"""
    logger.info("Starting full crawl pipeline...")
    try:
        from app.services.crawler.pipeline import run_crawl_pipeline
        result = asyncio.run(run_crawl_pipeline())
        logger.info(
            "Crawl complete: arxiv=%d inspire=%d new=%d errors=%d",
            result["arxiv_fetched"],
            result["inspire_fetched"],
            result["papers_new"],
            len(result["errors"]),
        )
        return result
    except Exception as e:
        logger.exception("Crawl pipeline failed: %s", e)
        raise


@celery_app.task(name="app.tasks.crawl.crawl_arxiv", **RETRY_CONFIG)
def crawl_arxiv():
    logger.info("Starting arXiv crawl task")
    result = asyncio.run(_run_arxiv_crawl())
    return result


@celery_app.task(name="app.tasks.crawl.crawl_inspire", **RETRY_CONFIG)
def crawl_inspire():
    logger.info("Starting INSPIRE crawl task")
    result = asyncio.run(_run_inspire_crawl())
    return result


async def _run_arxiv_crawl():
    from app.services.crawler.arxiv import search_arxiv_batch
    from app.core.database import async_session_factory
    from app.models.datasource import DataSource, CrawlTask
    from app.services.crawler.pipeline import _get_or_create_paper_from_arxiv
    from sqlalchemy import select
    from datetime import datetime

    async with async_session_factory() as db:
        ds = (await db.execute(select(DataSource).where(DataSource.api_type == "arxiv"))).scalar_one_or_none()
        if not ds:
            return {"status": "error", "error": "arXiv data source not configured"}

        task = CrawlTask(source_id=ds.id, keyword="arxiv_batch", status="running", started_at=datetime.utcnow())
        db.add(task)
        await db.flush()

        try:
            papers = await search_arxiv_batch()
            new_count = 0
            for p in papers:
                pid = await _get_or_create_paper_from_arxiv(db, p, ds.id)
                if pid:
                    new_count += 1

            task.status = "success"
            task.papers_fetched = len(papers)
            task.papers_new = new_count
            task.finished_at = datetime.utcnow()
            await db.commit()
            return {"status": "ok", "fetched": len(papers), "new": new_count}
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.finished_at = datetime.utcnow()
            await db.commit()
            raise


async def _run_inspire_crawl():
    from app.services.crawler.inspire import search_inspire
    from app.core.database import async_session_factory
    from app.models.datasource import DataSource, CrawlTask
    from app.services.crawler.pipeline import _import_from_inspire
    from sqlalchemy import select
    from datetime import datetime

    async with async_session_factory() as db:
        ds = (await db.execute(select(DataSource).where(DataSource.api_type == "inspire"))).scalar_one_or_none()
        if not ds:
            return {"status": "error", "error": "INSPIRE data source not configured"}

        task = CrawlTask(source_id=ds.id, keyword="inspire_search", status="running", started_at=datetime.utcnow())
        db.add(task)
        await db.flush()

        try:
            papers = await search_inspire()
            new_count = 0
            for p in papers:
                pid = await _import_from_inspire(db, p, ds.id)
                if pid:
                    new_count += 1

            task.status = "success"
            task.papers_fetched = len(papers)
            task.papers_new = new_count
            task.finished_at = datetime.utcnow()
            await db.commit()
            return {"status": "ok", "fetched": len(papers), "new": new_count}
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.finished_at = datetime.utcnow()
            await db.commit()
            raise
