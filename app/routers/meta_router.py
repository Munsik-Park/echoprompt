from typing import List
from fastapi import APIRouter, Depends, Path
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.models import SessionModel, MessageTreeNode
from app.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["Meta"])

@router.get(
    "/collections",
    response_model=List[str],
    summary="List collections",
    description="Retrieve available vector collections from Qdrant.",
)
async def list_collections(
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
):
    """Return a list of collection names. Currently returns an empty list."""
    return []

@router.get(
    "/collections/{name}/users",
    response_model=List[str],
    summary="List users in collection",
    description="List user IDs stored within the specified collection.",
)
async def list_collection_users(name: str = Path(..., description="Collection name")):
    """Return a list of user IDs for a collection. Currently empty."""
    return []

@router.get(
    "/users/{user_id}/sessions",
    response_model=List[SessionModel],
    summary="List user sessions",
    description="Get all sessions belonging to the specified user.",
)
async def list_user_sessions(user_id: str = Path(..., description="User ID")):
    """Return a list of sessions for a user. Currently empty."""
    return []

@router.get(
    "/sessions/{session_id}/tree",
    response_model=MessageTreeNode,
    summary="Get message tree",
    description="Retrieve messages in a tree structure based on document_id order.",
)
async def get_session_tree(session_id: int = Path(..., description="Session ID")):
    """Return the message tree for a session. Currently returns an empty node."""
    return MessageTreeNode(id=0, parent_id=None, content="", role="user", children=[])
