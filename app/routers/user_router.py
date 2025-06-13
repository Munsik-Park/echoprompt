from typing import List, Set
from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client.http import models as qdrant_models
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.config import settings
from app.models import ErrorResponse, ErrorCode # Assuming ErrorResponse and ErrorCode are in app.models

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/users",
    tags=["Users"]
)

@router.get("/{user_id}/sessions", response_model=List[int])
async def get_user_sessions(user_id: str, qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)):
    """
    Retrieve a list of session IDs associated with a specific user ID.
    This involves checking all relevant collections.
    """
    try:
        # 1. Get all collection names
        collections_response = qdrant_client.client.get_collections()
        all_collection_names = [desc.name for desc in collections_response.collections]

        user_session_ids: Set[int] = set()

        # 2. For each collection that matches the "session_{id}" pattern
        for collection_name in all_collection_names:
            if not collection_name.startswith("session_"):
                continue # Skip collections not matching the expected pattern

            try:
                # Attempt to parse session_id from collection name
                parts = collection_name.split("_")
                if len(parts) < 2 or not parts[1].isdigit():
                    # Log this unexpected collection name format if necessary
                    continue
                current_session_id = int(parts[1])
            except ValueError:
                # Log error for malformed collection name
                continue

            # 3. Check if the user_id exists in this collection's messages
            # We only need to know if at least one point exists, so limit can be 1.
            # Using scroll for filter capabilities.
            # Note: search might also work with a dummy vector if preferred.
            scroll_response, _ = qdrant_client.client.scroll(
                collection_name=collection_name,
                scroll_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="user_id",
                            match=qdrant_models.MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1, # We only need to find if one such point exists
                with_payload=False, # No need for payload data
                with_vectors=False  # No need for vector data
            )

            if scroll_response: # If any points are returned
                user_session_ids.add(current_session_id)

        return sorted(list(user_session_ids))

    except Exception as e:
        # Log the exception details here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.QDRANT_ERROR, # Or a more specific error
                message=f"Failed to retrieve sessions for user '{user_id}'",
                details={"error": str(e)}
            ).dict() # Use .model_dump() if using Pydantic v2
        )
