"""INSPIRE-HEP API 适配器 — 高能物理领域权威数据源"""

import logging
from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass, field
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

INSPIRE_API_URL = settings.INSPIRE_API_URL

INSPIRE_QUERY = (
    "(find ct dark matter) OR "
    "(find ct WIMP) OR "
    "(find ct axion) OR "
    "(find ct dark photon) OR "
    "(find ct light mediator) OR "
    "(find ct CEvNS) OR "
    "(find ct coherent elastic neutrino) OR "
    "(find ct neutrinoless double beta) OR "
    "(find ct sterile neutrino) OR "
    "(find exp XENON) OR "
    "(find exp PandaX) OR "
    "(find exp ADMX) OR "
    "(find exp COHERENT) OR "
    "(find exp LEGEND) OR "
    "(find exp CUORE) OR "
    "(find exp KamLAND) OR "
    "(find exp IceCube)"
)


@dataclass
class InspirePaper:
    inspire_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    author_affiliations: list[str] = field(default_factory=list)
    arxiv_eprint: Optional[str] = None
    doi: Optional[str] = None
    published: Optional[date] = None
    citation_count: int = 0
    source_url: Optional[str] = None


def _parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    return datetime.strptime(date_str[:10], "%Y-%m-%d").date()


def parse_hit(hit: dict) -> InspirePaper:
    metadata = hit.get("metadata", {})

    title = metadata.get("titles", [{}])
    title_str = title[0].get("title", "") if title else ""

    abstract_list = metadata.get("abstracts", [{"value": ""}])
    abstract_str = abstract_list[0].get("value", "") if abstract_list else ""

    authors = []
    affiliations = []
    for a in metadata.get("authors", []):
        name_parts = a.get("full_name", "")
        authors.append(name_parts)
        for aff in a.get("affiliations", []):
            affiliations.append(aff.get("value", ""))

    arxiv_eprint = None
    for eprint in metadata.get("arxiv_eprints", []):
        arxiv_eprint = eprint.get("value")
        break

    doi_val = metadata.get("dois", [{}])
    doi_str = doi_val[0].get("value") if doi_val else None

    pub_date = None
    date_str = metadata.get("preprint_date") or metadata.get("publication_info", [{}])
    if isinstance(date_str, str):
        pub_date = _parse_date(date_str)
    elif isinstance(date_str, list) and date_str:
        pub_date = _parse_date(date_str[0].get("year", ""))

    return InspirePaper(
        inspire_id=str(hit.get("id", "")),
        title=title_str,
        abstract=abstract_str,
        authors=authors,
        author_affiliations=affiliations,
        arxiv_eprint=arxiv_eprint,
        doi=doi_str,
        published=pub_date,
        citation_count=metadata.get("citation_count", 0),
        source_url=f"https://inspirehep.net/literature/{hit.get('id')}",
    )


async def search_inspire(
    query: str = INSPIRE_QUERY,
    max_results: int = 50,
    page: int = 1,
    http_client: Optional[httpx.AsyncClient] = None,
) -> list[InspirePaper]:
    """
    搜索 INSPIRE-HEP 论文。

    参数:
        query: INSPIRE 查询语法
        max_results: 每页最大返回数
        page: 页码
    """
    params = {
        "q": query,
        "size": min(max_results, 50),
        "page": page,
        "sort": "mostrecent",
    }
    headers = {"Accept": "application/json"}

    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=30)
        close_client = True

    try:
        resp = await http_client.get(
            f"{INSPIRE_API_URL}/literature",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        papers = [parse_hit(h) for h in hits]
        logger.info("Fetched %d papers from INSPIRE-HEP (page %d)", len(papers), page)
        return papers
    finally:
        if close_client:
            await http_client.aclose()
