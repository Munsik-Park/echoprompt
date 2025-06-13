import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, call # Import call for checking call arguments
from datetime import datetime, timedelta

from app.models import (
    SessionModel,
    MessageModel,
    MessageCreate,
    MessageResponse, # For asserting response structure
    MessagePairResponse,
    # ErrorCode - if you want to assert specific error codes
)
from app.models.tree import MessageNode, SessionMessageTreeResponse # For tree endpoint

# Test data
SESSION_ID = 1
USER_ID = "test_user_123"
DOCUMENT_ID = "doc_abc_789"
MEMORY_TYPE = "short_term"

@pytest.fixture(scope="function")
def test_session(db_session):
    """Creates a dummy session for tests that require a session_id."""
    session = SessionModel(id=SESSION_ID, name="Test Session")
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session

def test_create_message_with_new_fields(client: TestClient, mock_qdrant_client_wrapper: MagicMock, test_session):
    """Test successful message creation with user_id, document_id, and memory_type."""

    mock_qdrant_client_wrapper.search_similar.return_value = [
        {"id": "q_1", "score": 0.9, "payload": {"content": "retrieved chunk 1", "message_id": 100, "session_id": SESSION_ID}}
    ]

    message_payload = {
        "content": "Hello, world with new fields!",
        "role": "user",
        "user_id": USER_ID,
        "document_id": DOCUMENT_ID,
        "memory_type": MEMORY_TYPE
    }

    response = client.post(f"/api/v1/sessions/{SESSION_ID}/messages", json=message_payload)

    assert response.status_code == 201
    data = response.json()

    # Assert response structure (MessagePairResponse)
    assert "user_message" in data
    assert "message" in data # assistant_message
    assert "retrieved_chunks" in data

    # Assert user_message content
    assert data["user_message"]["content"] == message_payload["content"]
    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["user_id"] == USER_ID
    assert data["user_message"]["document_id"] == DOCUMENT_ID
    assert data["user_message"]["memory_type"] == MEMORY_TYPE

    # Assert retrieved_chunks
    assert len(data["retrieved_chunks"]) == 1
    assert data["retrieved_chunks"][0]["payload"]["content"] == "retrieved chunk 1"

    # Assert mock calls
    # Call to store_embedding for the user message
    mock_qdrant_client_wrapper.store_embedding.assert_called_once()
    store_args, _ = mock_qdrant_client_wrapper.store_embedding.call_args
    assert store_args[0] == data["user_message"]["id"] # message_id
    assert store_args[1] == SESSION_ID # session_id
    assert store_args[2] == message_payload["content"] # content
    # embedding is generated, so we can't easily assert its exact value unless we control get_embedding mock
    assert store_args[4] == USER_ID # user_id
    assert store_args[5] == DOCUMENT_ID # document_id
    assert store_args[6] == MEMORY_TYPE # memory_type

    # Call to search_similar
    mock_qdrant_client_wrapper.search_similar.assert_called_once()
    search_args, search_kwargs = mock_qdrant_client_wrapper.search_similar.call_args
    assert search_kwargs["query"] == message_payload["content"]
    assert search_kwargs["session_id"] == SESSION_ID
    assert search_kwargs["user_id"] == USER_ID
    assert search_kwargs["document_id"] == DOCUMENT_ID
    assert search_kwargs["memory_type"] == MEMORY_TYPE


def test_create_message_backward_compatibility(client: TestClient, mock_qdrant_client_wrapper: MagicMock, test_session):
    """Test message creation without optional fields (user_id, document_id, memory_type)."""
    mock_qdrant_client_wrapper.search_similar.return_value = [] # No chunks for this test

    message_payload = {
        "content": "Hello, old world!",
        "role": "user"
    }
    response = client.post(f"/api/v1/sessions/{SESSION_ID}/messages", json=message_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["user_message"]["content"] == message_payload["content"]
    assert data["user_message"]["user_id"] is None
    assert data["user_message"]["document_id"] is None
    assert data["user_message"]["memory_type"] is None
    assert data["retrieved_chunks"] == []

    # Assert mock calls for store_embedding
    mock_qdrant_client_wrapper.store_embedding.assert_called_once()
    store_args, _ = mock_qdrant_client_wrapper.store_embedding.call_args
    assert store_args[4] is None # user_id
    assert store_args[5] is None # document_id
    assert store_args[6] is None # memory_type

    # Assert mock calls for search_similar
    mock_qdrant_client_wrapper.search_similar.assert_called_once()
    search_args, search_kwargs = mock_qdrant_client_wrapper.search_similar.call_args
    assert search_kwargs["user_id"] is None
    assert search_kwargs["document_id"] is None
    assert search_kwargs["memory_type"] is None


# --- Tests for GET /sessions/{session_id}/tree ---

def test_get_session_tree_empty(client: TestClient, test_session):
    """Test getting a message tree for a session with no messages."""
    response = client.get(f"/api/v1/sessions/{SESSION_ID}/tree")
    assert response.status_code == 200
    assert response.json() == []

def test_get_session_tree_non_existent_session(client: TestClient):
    """Test getting a message tree for a non-existent session."""
    response = client.get(f"/api/v1/sessions/9999/tree") # Assuming 9999 doesn't exist
    assert response.status_code == 404
    # Optionally, assert error code if you have specific error model
    # assert response.json()["detail"]["error"] == ErrorCode.SESSION_NOT_FOUND

def test_get_session_tree_structure(client: TestClient, db_session, test_session):
    """Test the structure of the message tree with various message types."""
    now = datetime.utcnow()
    # Messages for the tree
    # Root message (no document_id)
    msg1 = MessageModel(id=1, session_id=SESSION_ID, content="Root message 1", role="user", created_at=now)
    # Messages for document "doc1"
    msg2 = MessageModel(id=2, session_id=SESSION_ID, content="Doc1 Message 1", role="user", document_id="doc1", created_at=now + timedelta(seconds=1))
    msg3 = MessageModel(id=3, session_id=SESSION_ID, content="Doc1 Message 2", role="assistant", document_id="doc1", created_at=now + timedelta(seconds=2))
    # Another root message
    msg4 = MessageModel(id=4, session_id=SESSION_ID, content="Root message 2", role="user", created_at=now + timedelta(seconds=3))
    # Messages for document "doc2"
    msg5 = MessageModel(id=5, session_id=SESSION_ID, content="Doc2 Message 1", role="user", document_id="doc2", created_at=now + timedelta(seconds=4))

    db_session.add_all([msg1, msg2, msg3, msg4, msg5])
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{SESSION_ID}/tree")
    assert response.status_code == 200
    tree_data = response.json()

    # Expected:
    # 1. msg1 (root)
    # 2. Conceptual parent for "doc1" (children: msg2, msg3)
    # 3. msg4 (root)
    # 4. Conceptual parent for "doc2" (children: msg5)
    # Order should be msg1, then "doc1" group, then msg4, then "doc2" group due to created_at of first child/self.

    assert len(tree_data) == 4 # Two root messages and two document groups

    # Check msg1 (direct root node)
    assert tree_data[0]["content"] == "Root message 1"
    assert tree_data[0]["id"] == msg1.id
    assert not tree_data[0]["children"]

    # Check "doc1" group
    assert tree_data[1]["document_id"] == "doc1"
    assert tree_data[1]["content"] == "Document Group: doc1" # Conceptual parent
    assert len(tree_data[1]["children"]) == 2
    assert tree_data[1]["children"][0]["content"] == "Doc1 Message 1"
    assert tree_data[1]["children"][0]["id"] == msg2.id
    assert tree_data[1]["children"][1]["content"] == "Doc1 Message 2"
    assert tree_data[1]["children"][1]["id"] == msg3.id

    # Check msg4 (direct root node)
    assert tree_data[2]["content"] == "Root message 2"
    assert tree_data[2]["id"] == msg4.id
    assert not tree_data[2]["children"]

    # Check "doc2" group
    assert tree_data[3]["document_id"] == "doc2"
    assert tree_data[3]["content"] == "Document Group: doc2" # Conceptual parent
    assert len(tree_data[3]["children"]) == 1
    assert tree_data[3]["children"][0]["content"] == "Doc2 Message 1"
    assert tree_data[3]["children"][0]["id"] == msg5.id

    # Verify overall sorting by created_at (conceptual parents use first child's created_at)
    # tree_data[0] (msg1) created_at should be earliest
    # tree_data[1] (doc1 group) effective created_at is msg2's
    # tree_data[2] (msg4) created_at
    # tree_data[3] (doc2 group) effective created_at is msg5's

    # Datetimes from JSON are strings, parse them for comparison
    assert datetime.fromisoformat(tree_data[0]["created_at"]) == now
    assert datetime.fromisoformat(tree_data[1]["created_at"]) == now + timedelta(seconds=1) # Effective time of doc1 group
    assert datetime.fromisoformat(tree_data[2]["created_at"]) == now + timedelta(seconds=3)
    assert datetime.fromisoformat(tree_data[3]["created_at"]) == now + timedelta(seconds=4) # Effective time of doc2 group

    # Check that the conceptual parent's `id` is 0 as per implementation
    assert tree_data[1]["id"] == 0
    assert tree_data[3]["id"] == 0
