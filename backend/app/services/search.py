import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from elasticsearch import AsyncElasticsearch
    HAS_ES = True
except ImportError:
    HAS_ES = False
    logger.info("elasticsearch-py not installed, search will use database fallback")

PAPERS_INDEX = "papers"

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "default": {
                    "type": "standard",
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "title": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
            },
            "title_en": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
            },
            "abstract": {"type": "text"},
            "abstract_en": {"type": "text"},
            "doi": {"type": "keyword"},
            "arxiv_id": {"type": "keyword"},
            "publish_date": {"type": "date"},
            "citation_count": {"type": "integer"},
            "relevance_score": {"type": "float"},
            "hot_score": {"type": "float"},
            "language": {"type": "keyword"},
            "authors": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
            },
            "topic_ids": {"type": "keyword"},
            "topic_names": {"type": "keyword"},
            "experiment_ids": {"type": "keyword"},
            "experiment_names": {"type": "keyword"},
            "is_hidden": {"type": "boolean"},
            "created_at": {"type": "date"},
        }
    },
}


async def get_es_client() -> "AsyncElasticsearch":
    if not HAS_ES:
        raise RuntimeError("elasticsearch-py not installed")
    return AsyncElasticsearch(settings.ELASTICSEARCH_URL)


async def ensure_index(es: AsyncElasticsearch) -> None:
    exists = await es.indices.exists(index=PAPERS_INDEX)
    if not exists:
        await es.indices.create(index=PAPERS_INDEX, body=INDEX_MAPPING)
        logger.info(f"Created Elasticsearch index: {PAPERS_INDEX}")


async def index_paper(es: AsyncElasticsearch, paper_doc: dict) -> None:
    await es.index(index=PAPERS_INDEX, id=paper_doc["id"], document=paper_doc)


async def bulk_index_papers(es: AsyncElasticsearch, papers: list[dict]) -> None:
    if not papers:
        return
    operations = []
    for p in papers:
        operations.extend([
            {"index": {"_index": PAPERS_INDEX, "_id": p["id"]}},
            p,
        ])
    await es.bulk(operations=operations)
    logger.info(f"Indexed {len(papers)} papers to Elasticsearch")


async def sync_paper_to_es(paper_dict: dict) -> None:
    try:
        es = await get_es_client()
        await ensure_index(es)
        await index_paper(es, paper_dict)
        await es.close()
    except Exception as e:
        logger.error(f"Failed to sync paper to ES: {e}")


async def search_papers(
    q: str | None = None,
    topic_slug: str | None = None,
    author: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "date",
) -> tuple[list[str], int, dict[str, dict]]:
    try:
        es = await get_es_client()
        await ensure_index(es)
    except Exception as e:
        logger.warning(f"Elasticsearch unavailable, falling back to database: {e}")
        raise

    must_terms = [{"term": {"is_hidden": False}}]

    if q:
        must_terms.append({
            "multi_match": {
                "query": q,
                "fields": ["title^3", "title_en^3", "abstract^2", "abstract_en^2", "authors"],
                "type": "best_fields",
            }
        })

    if author:
        must_terms.append({"match": {"authors": author}})

    if topic_slug:
        must_terms.append({"term": {"topic_ids": topic_slug}})

    filters = []
    if date_from:
        filters.append({"range": {"publish_date": {"gte": date_from}}})
    if date_to:
        filters.append({"range": {"publish_date": {"lte": date_to}}})

    sort_list: list[dict] = []
    if sort == "relevance":
        sort_list.append({"relevance_score": {"order": "desc"}})
    elif sort == "citations":
        sort_list.append({"citation_count": {"order": "desc"}})
    elif sort == "hot":
        sort_list.append({"hot_score": {"order": "desc"}})
    else:
        sort_list.append({"publish_date": {"order": "desc"}})

    body: dict = {
        "query": {
            "bool": {
                "must": must_terms,
                "filter": filters,
            }
        },
        "sort": sort_list,
        "from": (page - 1) * page_size,
        "size": page_size,
        "highlight": {
            "fields": {
                "title": {"number_of_fragments": 0},
                "title_en": {"number_of_fragments": 0},
                "abstract": {"fragment_size": 200, "number_of_fragments": 1},
                "abstract_en": {"fragment_size": 200, "number_of_fragments": 1},
                "authors": {"number_of_fragments": 0},
            },
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
        },
    }

    try:
        response = await es.search(index=PAPERS_INDEX, body=body)
        await es.close()
    except Exception as e:
        logger.error(f"ES search failed: {e}")
        raise

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"] if isinstance(response["hits"]["total"], dict) else response["hits"]["total"]

    paper_ids = [hit["_id"] for hit in hits]
    highlights = {hit["_id"]: hit.get("highlight", {}) for hit in hits}
    return paper_ids, total, highlights


async def delete_paper_from_es(paper_id: str) -> None:
    try:
        es = await get_es_client()
        await es.delete(index=PAPERS_INDEX, id=paper_id, ignore=[404])
        await es.close()
    except Exception:
        pass


async def delete_index() -> None:
    try:
        es = await get_es_client()
        await es.indices.delete(index=PAPERS_INDEX, ignore=[404])
        await es.close()
    except Exception:
        pass
