from typing import List, Set
from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client.http import models as qdrant_models # Renamed to avoid conflict with app.models
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.config import settings
from app.models import ErrorResponse, ErrorCode # Assuming ErrorResponse and ErrorCode are in app.models

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/collections",
    tags=["Collections"]
)

@router.get("", response_model=List[str])
async def get_collections(qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)):
    """
    Retrieve a list of all collection names from Qdrant.
    """
    try:
        collections_response = qdrant_client.client.get_collections()
        collection_names = [desc.name for desc in collections_response.collections]
        return collection_names
    except Exception as e:
        # Log the exception details here if you have a logger configured
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.QDRANT_ERROR, # Assuming a QDRANT_ERROR code exists
                message="Failed to retrieve collections from Qdrant",
                details={"error": str(e)}
            ).dict() # Use .model_dump() if using Pydantic v2
        )

@router.get("/{name}/users", response_model=List[str])
async def get_collection_users(name: str, qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)):
    """
    Retrieve a list of unique user IDs from a specific collection.
    Note: This can be resource-intensive for very large collections.
    """
    try:
        # Check if collection exists first to provide a better error message
        try:
            qdrant_client.client.get_collection(collection_name=name)
        except Exception as e: # Catching generic exception from qdrant_client for collection not found
            # More specific exception handling based on qdrant_client's behavior is better
            if "not found" in str(e).lower() or "404" in str(e):
                 raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        error=ErrorCode.COLLECTION_NOT_FOUND, # Assuming this error code
                        message=f"Collection '{name}' not found."
                    ).dict() # Use .model_dump() if using Pydantic v2
                )
            raise # Re-raise if it's another error during get_collection

        user_ids: Set[str] = set()
        next_page_offset = None

        while True:
            points, next_page_offset = qdrant_client.client.scroll(
                collection_name=name,
                with_payload=["user_id"], # Request only the user_id field
                with_vectors=False, # No need for vectors
                limit=250, # Adjust limit as needed; consider making it a parameter
                offset=next_page_offset
            )

            for point in points:
                if point.payload and "user_id" in point.payload and point.payload["user_id"] is not None:
                    user_ids.add(str(point.payload["user_id"])) # Ensure user_id is string

            if not next_page_offset:
                break

        return list(user_ids)

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        # Log the exception details here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.QDRANT_ERROR,
                message=f"Failed to retrieve user IDs from collection '{name}'",
                details={"error": str(e)}
            ).dict() # Use .model_dump() if using Pydantic v2
        )
