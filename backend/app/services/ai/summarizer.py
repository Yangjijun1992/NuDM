"""AI 摘要生成服务 — 使用 LLM 生成结构化摘要"""


import json
import logging
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.paper import Paper
from app.models.social import AISummary

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """你是一个粒子物理学研究助理。你需要根据论文标题和摘要，生成结构化的中文解读。

请严格按照以下 JSON 格式返回（不要包含 markdown 代码块标记）:

{
  "summary_cn": "2-3句中文概述，说明论文的研究背景、目的和核心发现",
  "contribution": "一句话说明论文的主要贡献或创新点",
  "method": "简述采用的研究方法或实验技术",
  "result": "简述关键结果或发现",
  "keywords": ["3-5个关键词"]
}
"""


async def generate_summary(paper_id: str) -> dict:
    """为指定论文生成 AI 摘要"""
    async with async_session_factory() as db:
        paper = (await db.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        text = paper.abstract or paper.abstract_en or paper.title
        if not text:
            return {"error": "No text available for summarization"}

        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"标题: {paper.title}\n\n摘要: {text[:2000]}"},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            content = response.choices[0].message.content or "{}"
            data = _parse_json_response(content)

            tokens_used = response.usage.total_tokens if response.usage else 0

            existing = (await db.execute(
                select(AISummary).where(AISummary.paper_id == paper_id)
            )).scalar_one_or_none()

            if existing:
                existing.summary_cn = data.get("summary_cn", "")
                existing.summary_en = None
                existing.contribution = data.get("contribution", "")
                existing.method = data.get("method", "")
                existing.result = data.get("result", "")
                existing.keywords_extracted = data.get("keywords", [])
                existing.model = settings.OPENAI_MODEL
                existing.tokens_used = tokens_used
                existing.quality_flag = "unreviewed"
                existing.generated_at = datetime.utcnow()
            else:
                db.add(AISummary(
                    paper_id=paper_id,
                    summary_cn=data.get("summary_cn", ""),
                    contribution=data.get("contribution", ""),
                    method=data.get("method", ""),
                    result=data.get("result", ""),
                    keywords_extracted=data.get("keywords", []),
                    model=settings.OPENAI_MODEL,
                    tokens_used=tokens_used,
                ))

            await db.commit()
            logger.info("AI summary generated for paper %s", paper.title[:60])
            return {"status": "ok", "paper_id": paper_id, **data}

        except Exception as e:
            logger.error("Failed to generate summary for %s: %s", paper_id, e)
            return {"status": "error", "error": str(e)}


def _parse_json_response(content: str) -> dict:
    """解析 LLM 返回的 JSON，处理不规范的格式"""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    import re
    m = re.search(r"\{[\s\S]*\}", content)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return {
        "summary_cn": content[:500],
        "contribution": "",
        "method": "",
        "result": "",
        "keywords": [],
    }


async def batch_generate_summaries(
    limit: int = 20,
    db: AsyncSession | None = None,
) -> dict:
    """批量为未生成摘要的论文生成 AI 摘要"""
    close_db = False
    if db is None:
        db = async_session_factory()
        close_db = True

    try:
        async with db if close_db else db as session:
            subquery = select(AISummary.paper_id)
            result = await session.execute(
                select(Paper)
                .where(Paper.is_hidden == False)
                .where(~Paper.id.in_(subquery))
                .order_by(Paper.created_at.desc())
                .limit(limit)
            )
            papers = result.scalars().all()

            success = 0
            failed = 0
            for paper in papers:
                r = await generate_summary(str(paper.id))
                if r.get("status") == "ok":
                    success += 1
                else:
                    failed += 1

            logger.info("Batch summary: %d success, %d failed", success, failed)
            return {"success": success, "failed": failed, "total": len(papers)}
    finally:
        if close_db:
            await db.close()


async def batch_regenerate_summaries(limit: int = 20) -> list[dict]:
    from app.models.social import AISummary

    async with async_session_factory() as db:
        result = await db.execute(
            select(Paper)
            .join(AISummary, AISummary.paper_id == Paper.id)
            .order_by(Paper.created_at.desc())
            .limit(limit)
        )
        papers = result.scalars().all()

        regenerated = []
        for paper in papers:
            r = await generate_summary(str(paper.id))
            if r.get("status") == "ok":
                regenerated.append({"paper_id": str(paper.id), "title": paper.title[:80]})

        logger.info("Regenerated %d summaries", len(regenerated))
        return regenerated
