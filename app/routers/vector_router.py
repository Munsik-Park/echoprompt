from typing import List
from fastapi import APIRouter, Depends
from datetime import datetime

from app.qdrant_client import get_qdrant_client, insert_vector, search_vectors
from app.models import VectorPayload
from app.utils.token_utils import count_tokens
from app.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/vectors", tags=["Vector"])


@router.post("/{collection_name}")
def add_vector(
    collection_name: str,
    vector: List[float],
    payload: VectorPayload,
    qdrant_client=Depends(get_qdrant_client),
):
    if payload.token_count <= 0:
        payload.token_count = count_tokens(payload.content)
    if not payload.timestamp:
        payload.timestamp = datetime.utcnow()
    insert_vector(qdrant_client.client, collection_name, vector, payload)
    return {"status": "inserted"}


@router.post("/{collection_name}/search")
def search_vector(
    collection_name: str,
    query_vector: List[float],
    qdrant_client=Depends(get_qdrant_client),
):
    results = search_vectors(qdrant_client.client, collection_name, query_vector)
    return {"results": results}
