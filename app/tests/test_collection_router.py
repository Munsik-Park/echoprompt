import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from qdrant_client.http import models as qdrant_models # For CollectionDescription

# Assuming ErrorCode and ErrorResponse are importable for detailed error checking
# from app.models import ErrorCode, ErrorResponse

COLLECTION_NAME = "session_123" # Example collection name

def test_get_collections(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test retrieving a list of all collection names."""
    mock_collections_response = qdrant_models.CollectionsResponse(
        collections=[
            qdrant_models.CollectionDescription(name="session_1"),
            qdrant_models.CollectionDescription(name="session_2"),
            qdrant_models.CollectionDescription(name="another_collection"),
        ]
    )
    mock_qdrant_client_wrapper.client.get_collections.return_value = mock_collections_response

    response = client.get("/api/v1/collections")

    assert response.status_code == 200
    expected_names = ["session_1", "session_2", "another_collection"]
    assert response.json() == expected_names
    mock_qdrant_client_wrapper.client.get_collections.assert_called_once()

def test_get_collections_qdrant_error(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test error handling when Qdrant fails to get collections."""
    mock_qdrant_client_wrapper.client.get_collections.side_effect = Exception("Qdrant connection error")

    response = client.get("/api/v1/collections")

    assert response.status_code == 500
    # Optionally check error content if ErrorResponse/ErrorCode is used consistently
    # data = response.json()
    # assert data["detail"]["error"] == ErrorCode.QDRANT_ERROR

def test_get_collection_users_success(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test retrieving unique user IDs from a collection."""
    # Mock get_collection to simulate collection existence
    mock_qdrant_client_wrapper.client.get_collection.return_value = MagicMock() # Just needs to not raise error

    # Mock scroll to return points
    points_batch1 = [
        qdrant_models.ScoredPoint(id="1", version=1, score=1.0, payload={"user_id": "user1"}),
        qdrant_models.ScoredPoint(id="2", version=1, score=1.0, payload={"user_id": "user2"}),
        qdrant_models.ScoredPoint(id="3", version=1, score=1.0, payload={"user_id": "user1"}), # Duplicate user1
    ]
    points_batch2 = [
        qdrant_models.ScoredPoint(id="4", version=1, score=1.0, payload={"user_id": "user3"}),
        qdrant_models.ScoredPoint(id="5", version=1, score=1.0, payload={}), # No user_id
        qdrant_models.ScoredPoint(id="6", version=1, score=1.0, payload={"user_id": None}), # user_id is None
    ]

    # Simulate pagination: first call returns points_batch1 and an offset, second call returns points_batch2 and no offset
    mock_qdrant_client_wrapper.client.scroll.side_effect = [
        (points_batch1, "next_offset_dummy_1"), # First call to scroll
        (points_batch2, None)                   # Second call to scroll
    ]

    response = client.get(f"/api/v1/collections/{COLLECTION_NAME}/users")

    assert response.status_code == 200
    user_ids = response.json()
    assert len(user_ids) == 3
    assert "user1" in user_ids
    assert "user2" in user_ids
    assert "user3" in user_ids

    # Check that get_collection was called to verify existence
    mock_qdrant_client_wrapper.client.get_collection.assert_called_once_with(collection_name=COLLECTION_NAME)

    # Check scroll calls
    assert mock_qdrant_client_wrapper.client.scroll.call_count == 2
    first_call_args = mock_qdrant_client_wrapper.client.scroll.call_args_list[0]
    second_call_args = mock_qdrant_client_wrapper.client.scroll.call_args_list[1]

    assert first_call_args[1]["collection_name"] == COLLECTION_NAME
    assert first_call_args[1]["with_payload"] == ["user_id"]
    assert first_call_args[1]["limit"] == 250 # Default limit in implementation
    assert first_call_args[1]["offset"] is None

    assert second_call_args[1]["collection_name"] == COLLECTION_NAME
    assert second_call_args[1]["offset"] == "next_offset_dummy_1"


def test_get_collection_users_collection_not_found(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test retrieving users from a non-existent collection."""
    # Mock get_collection to simulate collection not found
    # The specific exception type and message might depend on the Qdrant client version
    # A common way is to raise an exception that includes "not found" or a 404 status code hint
    mock_qdrant_client_wrapper.client.get_collection.side_effect = Exception("Collection not found 404")

    response = client.get(f"/api/v1/collections/non_existent_collection/users")

    assert response.status_code == 404
    # data = response.json()
    # assert data["detail"]["error"] == ErrorCode.COLLECTION_NOT_FOUND

def test_get_collection_users_empty_collection(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test retrieving users from a collection with no points or no user_ids."""
    mock_qdrant_client_wrapper.client.get_collection.return_value = MagicMock()
    mock_qdrant_client_wrapper.client.scroll.return_value = ([], None) # No points

    response = client.get(f"/api/v1/collections/{COLLECTION_NAME}/users")

    assert response.status_code == 200
    assert response.json() == []

def test_get_collection_users_qdrant_scroll_error(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test error handling if Qdrant scroll fails for other reasons."""
    mock_qdrant_client_wrapper.client.get_collection.return_value = MagicMock()
    mock_qdrant_client_wrapper.client.scroll.side_effect = Exception("Qdrant scroll failed")

    response = client.get(f"/api/v1/collections/{COLLECTION_NAME}/users")
    assert response.status_code == 500
    # data = response.json()
    # assert data["detail"]["error"] == ErrorCode.QDRANT_ERROR
