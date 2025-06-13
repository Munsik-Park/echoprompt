import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.main import app  # Your FastAPI app
from app.database import Base, get_db
from app.qdrant_client import QdrantClientWrapper, get_qdrant_client
from app.openai_client import get_openai_client # If chat functionality is deeply tied

# --- Database Fixtures (In-memory SQLite for testing) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"  # Use in-memory SQLite for tests
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a new database session for a test.
    Rolls back any changes after the test.
    """
    Base.metadata.create_all(bind=engine)  # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback() # Ensure db is clean for next test
        db.close()
    Base.metadata.drop_all(bind=engine) # Drop tables after test

@pytest.fixture(scope="function")
def client(db_session, mock_qdrant_client_wrapper, mock_openai_client): # Add other mocks
    """
    Provides a TestClient instance with overridden dependencies.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant_client_wrapper
    app.dependency_overrides[get_openai_client] = lambda: mock_openai_client

    test_client = TestClient(app)
    yield test_client

    # Clean up overrides after tests if necessary, though FastAPI handles this for app.dependency_overrides
    app.dependency_overrides = {}


# --- Mock Fixtures ---
@pytest.fixture
def mock_qdrant_client_wrapper():
    """
    Mocks the QdrantClientWrapper.
    The internal 'client' attribute (actual QdrantSDK client) is also mocked.
    """
    mock_wrapper = MagicMock(spec=QdrantClientWrapper)
    mock_wrapper.client = MagicMock() # This mocks the actual Qdrant client SDK instance

    # Default behaviors for common Qdrant calls (can be overridden in tests)
    mock_wrapper.get_embedding = MagicMock(return_value=[0.1] * 1536) # Example embedding
    mock_wrapper._ensure_collection = MagicMock()
    mock_wrapper.store_embedding = MagicMock()
    mock_wrapper.search_similar = MagicMock(return_value=[]) # Default to no similar messages
    mock_wrapper.delete_embedding = MagicMock()
    mock_wrapper.delete_session_embeddings = MagicMock()

    # For collection_router and user_router tests
    mock_wrapper.client.get_collections = MagicMock()
    mock_wrapper.client.scroll = MagicMock(return_value=([], None)) # Default scroll returns no points
    mock_wrapper.client.get_collection = MagicMock() # To simulate collection existence checks

    return mock_wrapper

@pytest.fixture
def mock_openai_client():
    """Mocks the OpenAI client."""
    mock = AsyncMock() # Use AsyncMock if your OpenAI calls are async
    mock.chat = AsyncMock()
    mock.chat.completions = AsyncMock()
    # Example: mock.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Mocked AI response"))])
    # Adjust as per actual usage in your create_message_endpoint
    # For the current tests, we mostly care that Qdrant is called correctly; OpenAI mocking can be basic.
    # If create_message_endpoint is synchronous, use MagicMock instead of AsyncMock.
    # Based on session_router.py, openai_client is not async, so change to MagicMock

    sync_mock = MagicMock()
    sync_mock.chat = MagicMock()
    sync_mock.chat.completions = MagicMock()
    sync_mock.chat.completions.create = MagicMock(
        return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Mocked AI response"))])
    )
    return sync_mock

# If you have other dependencies to mock (e.g., specific settings objects if they change behavior),
# you can add more fixtures here.
