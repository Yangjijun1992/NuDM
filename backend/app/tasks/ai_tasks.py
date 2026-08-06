"""Celery AI 任务 — 摘要生成 + 分类评分"""

import asyncio
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

RETRY_CONFIG = {
    "autoretry_for": (Exception,),
    "max_retries": 2,
    "retry_backoff": True,
    "retry_backoff_max": 300,
    "retry_jitter": True,
}


@celery_app.task(name="app.tasks.ai.generate_summaries", **RETRY_CONFIG)
def generate_summaries(limit: int = 20):
    """批量生成 AI 摘要"""
    logger.info("Starting batch summary generation (limit=%d)...", limit)
    try:
        from app.services.ai.summarizer import batch_generate_summaries
        result = asyncio.run(batch_generate_summaries(limit=limit))
        logger.info("Summaries: %d/%d success", result["success"], result["total"])
        return result
    except Exception as e:
        logger.exception("Batch summary failed: %s", e)
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.tasks.ai.classify_and_score", **RETRY_CONFIG)
def classify_and_score(limit: int = 50):
    """批量分类 + 评分"""
    logger.info("Starting batch classification and scoring (limit=%d)...", limit)
    try:
        from app.services.ai.classifier import batch_classify_and_score
        result = asyncio.run(batch_classify_and_score(limit=limit))
        logger.info("Classified %d, scored %d of %d", result["classified"], result["scored"], result["total"])
        return result
    except Exception as e:
        logger.exception("Batch classification failed: %s", e)
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.tasks.ai.process_new_papers", **RETRY_CONFIG)
def process_new_papers():
    """处理新入库论文：分类 + 评分 + 摘要"""
    logger.info("Processing new papers...")

    classify_result = asyncio.run(_classify_unscored())
    summary_result = asyncio.run(_summarize_unsynopsized())

    return {
        "classification": classify_result,
        "summary": summary_result,
    }


async def _classify_unscored():
    from app.services.ai.classifier import batch_classify_and_score
    return await batch_classify_and_score(limit=30)


async def _summarize_unsynopsized():
    from app.services.ai.summarizer import batch_generate_summaries
    return await batch_generate_summaries(limit=10)


@celery_app.task(name="app.tasks.ai.regenerate_summaries", **RETRY_CONFIG)
def regenerate_summaries(limit: int = 20):
    """批量重新生成已有论文的 AI 摘要（覆盖旧的）"""
    logger.info("Starting batch summary regeneration (limit=%d)...", limit)
    try:
        from app.services.ai.summarizer import batch_regenerate_summaries
        result = asyncio.run(batch_regenerate_summaries(limit=limit))
        logger.info("Regeneration done: %d summaries regenerated", len(result))
        return {"status": "ok", "regenerated": len(result)}
    except Exception as e:
        logger.exception("Regeneration failed: %s", e)
        raise
