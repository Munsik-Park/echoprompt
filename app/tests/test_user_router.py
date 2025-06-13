import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, call
from qdrant_client.http import models as qdrant_models

# Assuming ErrorCode and ErrorResponse are importable for detailed error checking
# from app.models import ErrorCode, ErrorResponse

USER_ID_FOR_TESTS = "test_user_xyz"

def test_get_user_sessions_success(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test retrieving session IDs for a user successfully."""
    # 1. Mock get_collections response
    mock_collections_response = qdrant_models.CollectionsResponse(
        collections=[
            qdrant_models.CollectionDescription(name="session_1"), # User present
            qdrant_models.CollectionDescription(name="session_2"), # User not present
            qdrant_models.CollectionDescription(name="other_collection"), # Not a session collection
            qdrant_models.CollectionDescription(name="session_3"), # User present
            qdrant_models.CollectionDescription(name="session_malformed"), # Malformed session name
            qdrant_models.CollectionDescription(name="session_invalid_id"), # e.g. session_abc
        ]
    )
    mock_qdrant_client_wrapper.client.get_collections.return_value = mock_collections_response

    # 2. Mock scroll responses for each relevant collection
    # For "session_1": User found
    scroll_response_session1 = ([qdrant_models.ScoredPoint(id="p1", version=1, score=1.0, payload={"user_id": USER_ID_FOR_TESTS})], None)
    # For "session_2": User not found (empty points list)
    scroll_response_session2 = ([], None)
    # For "session_3": User found
    scroll_response_session3 = ([qdrant_models.ScoredPoint(id="p2", version=1, score=1.0, payload={"user_id": USER_ID_FOR_TESTS})], None)

    # scroll side_effect needs to map collection_name to its response
    def scroll_side_effect(collection_name, **kwargs):
        if collection_name == "session_1":
            return scroll_response_session1
        elif collection_name == "session_2":
            return scroll_response_session2
        elif collection_name == "session_3":
            return scroll_response_session3
        return ([], None) # Default for any other unexpected calls

    mock_qdrant_client_wrapper.client.scroll.side_effect = scroll_side_effect

    response = client.get(f"/api/v1/users/{USER_ID_FOR_TESTS}/sessions")

    assert response.status_code == 200
    session_ids = response.json()

    assert len(session_ids) == 2
    assert 1 in session_ids
    assert 3 in session_ids
    assert 2 not in session_ids # User was not in session_2

    # Verify mock calls
    mock_qdrant_client_wrapper.client.get_collections.assert_called_once()

    # Expected scroll calls for session_1, session_2, session_3
    # (other_collection, session_malformed, session_invalid_id should be skipped before scroll)
    expected_scroll_calls = [
        call(collection_name="session_1", scroll_filter=MagicMock(), limit=1, with_payload=False, with_vectors=False),
        call(collection_name="session_2", scroll_filter=MagicMock(), limit=1, with_payload=False, with_vectors=False),
        call(collection_name="session_3", scroll_filter=MagicMock(), limit=1, with_payload=False, with_vectors=False),
    ]

    # Check that scroll was called for the relevant session collections
    # We can't directly use assert_has_calls with MagicMock for the filter object easily,
    # so we check call_count and relevant collection names.
    assert mock_qdrant_client_wrapper.client.scroll.call_count == 3

    actual_collection_names_scrolled = [c.kwargs['collection_name'] for c in mock_qdrant_client_wrapper.client.scroll.call_args_list]
    assert "session_1" in actual_collection_names_scrolled
    assert "session_2" in actual_collection_names_scrolled
    assert "session_3" in actual_collection_names_scrolled


def test_get_user_sessions_no_sessions_found(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test when a user has no associated sessions."""
    mock_collections_response = qdrant_models.CollectionsResponse(
        collections=[
            qdrant_models.CollectionDescription(name="session_1"),
            qdrant_models.CollectionDescription(name="session_2"),
        ]
    )
    mock_qdrant_client_wrapper.client.get_collections.return_value = mock_collections_response
    mock_qdrant_client_wrapper.client.scroll.return_value = ([], None) # User not found in any collection

    response = client.get(f"/api/v1/users/{USER_ID_FOR_TESTS}/sessions")

    assert response.status_code == 200
    assert response.json() == []


def test_get_user_sessions_no_collections_exist(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test when there are no collections in Qdrant at all."""
    mock_collections_response = qdrant_models.CollectionsResponse(collections=[])
    mock_qdrant_client_wrapper.client.get_collections.return_value = mock_collections_response

    response = client.get(f"/api/v1/users/{USER_ID_FOR_TESTS}/sessions")

    assert response.status_code == 200
    assert response.json() == []
    mock_qdrant_client_wrapper.client.scroll.assert_not_called() # Scroll shouldn't be called if no collections


def test_get_user_sessions_qdrant_error_on_get_collections(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test error handling if Qdrant fails during get_collections."""
    mock_qdrant_client_wrapper.client.get_collections.side_effect = Exception("Qdrant connection error")

    response = client.get(f"/api/v1/users/{USER_ID_FOR_TESTS}/sessions")

    assert response.status_code == 500
    # data = response.json()
    # assert data["detail"]["error"] == ErrorCode.QDRANT_ERROR

def test_get_user_sessions_qdrant_error_on_scroll(client: TestClient, mock_qdrant_client_wrapper: MagicMock):
    """Test error handling if Qdrant fails during a scroll operation."""
    mock_collections_response = qdrant_models.CollectionsResponse(
        collections=[qdrant_models.CollectionDescription(name="session_1")]
    )
    mock_qdrant_client_wrapper.client.get_collections.return_value = mock_collections_response
    mock_qdrant_client_wrapper.client.scroll.side_effect = Exception("Qdrant scroll error")

    response = client.get(f"/api/v1/users/{USER_ID_FOR_TESTS}/sessions")

    assert response.status_code == 500
    # data = response.json()
    # assert data["detail"]["error"] == ErrorCode.QDRANT_ERROR
    # Ensure scroll was attempted for "session_1"
    mock_qdrant_client_wrapper.client.scroll.assert_called_once_with(
        collection_name="session_1",
        scroll_filter=MagicMock(), # Actual filter object is complex to match exactly with MagicMock
        limit=1,
        with_payload=False,
        with_vectors=False
    )
