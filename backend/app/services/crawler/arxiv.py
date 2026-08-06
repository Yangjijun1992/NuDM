"""arXiv API 适配器 — 基于 arXiv OAI-PMH 格式解析"""

import logging
import re
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field
import httpx
import feedparser
from app.core.config import settings

logger = logging.getLogger(__name__)

ARXIV_API_URL = settings.ARXIV_API_URL

ARXIV_CATEGORY_MAP = {
    "hep-ex": "High Energy Physics - Experiment",
    "hep-ph": "High Energy Physics - Phenomenology",
    "hep-th": "High Energy Physics - Theory",
    "astro-ph.CO": "Astrophysics - Cosmology",
    "astro-ph.HE": "Astrophysics - High Energy Astrophysical Phenomena",
    "nucl-ex": "Nuclear Experiment",
    "physics.ins-det": "Physics - Instrumentation and Detectors",
}

SEARCH_KEYWORDS = [
    "dark matter",
    "WIMP",
    "axion",
    "dark photon",
    "light mediator",
    "CEvNS",
    "coherent elastic neutrino",
    "neutrinoless double beta",
    "0νββ",
    "sterile neutrino",
    "XENON",
    "LUX-ZEPLIN",
    "PandaX",
    "DarkSide",
    "SuperCDMS",
    "ADMX",
    "COHERENT",
    "LEGEND",
    "CUORE",
    "KamLAND-Zen",
    "MiniBooNE",
    "MicroBooNE",
    "IceCube neutrino",
    "DAMA/LIBRA",
    "Fermi-LAT dark matter",
]


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    published: Optional[date] = None
    updated: Optional[date] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    source_url: Optional[str] = None
    comment: Optional[str] = None


def _parse_arxiv_id(entry_id: str) -> str:
    """从 entry id 中提取纯 arXiv ID"""
    m = re.search(r"(?:arxiv:|abs/)([\w.\-]+)", entry_id)
    if m:
        return m.group(1)
    return entry_id.split("/")[-1]


def _parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    return datetime.strptime(date_str[:10], "%Y-%m-%d").date()


def _extract_doi(entry: dict) -> Optional[str]:
    """从 entry 中提取 DOI"""
    doi = entry.get("arxiv_doi")
    if doi:
        return doi
    for link in entry.get("links", []):
        href = link.get("href", "")
        m = re.search(r"doi\.org/(10\..+)", href)
        if m:
            return m.group(1)
    return None


def _extract_authors(entry: dict) -> list[str]:
    return [a.get("name", "").strip() for a in entry.get("authors", []) if a.get("name")]


def parse_entry(entry: dict) -> ArxivPaper:
    arxiv_id = _parse_arxiv_id(entry.get("id", ""))
    categories = [t.get("term", "") for t in entry.get("tags", [])]
    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=entry.get("title", "").strip().replace("\n", " "),
        abstract=entry.get("summary", "").strip().replace("\n", " "),
        authors=_extract_authors(entry),
        categories=categories,
        published=_parse_date(entry.get("published", "")),
        updated=_parse_date(entry.get("updated", "")),
        doi=_extract_doi(entry),
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None,
        source_url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
        comment=entry.get("arxiv_comment"),
    )


async def search_arxiv(
    query: str,
    max_results: int = 50,
    start: int = 0,
    sort_by: str = "submittedDate",
    http_client: Optional[httpx.AsyncClient] = None,
) -> list[ArxivPaper]:
    """
    搜索 arXiv 论文，返回解析后的 ArxivPaper 列表。

    参数:
        query: 搜索查询字符串
        max_results: 最大返回数量 (上限 2000)
        start: 起始偏移
        sort_by: 排序方式 (relevance / lastUpdatedDate / submittedDate)
    """
    params = {
        "search_query": query,
        "max_results": min(max_results, 2000),
        "start": start,
        "sortBy": sort_by,
    }

    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=30)
        close_client = True

    try:
        resp = await http_client.get(ARXIV_API_URL, params=params)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        if feed.bozo:
            logger.warning("arXiv feed parse warning: %s", feed.bozo_exception)

        papers = [parse_entry(entry) for entry in feed.entries]
        logger.info("Fetched %d papers from arXiv for query: %s", len(papers), query[:80])
        return papers
    finally:
        if close_client:
            await http_client.aclose()


async def search_arxiv_batch(
    keywords: list[str] = SEARCH_KEYWORDS,
    max_per_keyword: int = 50,
    http_client: Optional[httpx.AsyncClient] = None,
) -> list[ArxivPaper]:
    """
    批量搜索多个关键词，去重后返回。
    """
    seen_ids: set[str] = set()
    all_papers: list[ArxivPaper] = []

    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=30)
        close_client = True

    try:
        for keyword in keywords:
            try:
                papers = await search_arxiv(
                    f'all:"{keyword}"',
                    max_results=max_per_keyword,
                    http_client=http_client,
                )
                for p in papers:
                    if p.arxiv_id not in seen_ids:
                        seen_ids.add(p.arxiv_id)
                        all_papers.append(p)
            except Exception as e:
                logger.error("Failed to search arXiv for keyword '%s': %s", keyword, e)
    finally:
        if close_client:
            await http_client.aclose()

    logger.info("Total unique arXiv papers fetched: %d", len(all_papers))
    return all_papers
