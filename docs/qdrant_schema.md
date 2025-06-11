# Qdrant Vector Schema Definition

This document outlines the structure of the vector schema used in our Qdrant collections.

## Schema Fields

The schema is designed to support efficient semantic search and retrieval for a Retrieval Augmented Generation (RAG) system. Each vector stored in Qdrant will adhere to the following structure:

| Field Name    | Data Type        | Description                                                                 | Example                                           | Notes                                                                      |
|---------------|------------------|-----------------------------------------------------------------------------|---------------------------------------------------|----------------------------------------------------------------------------|
| `id`          | UUID/Integer     | Unique identifier for the vector point.                                     | `6a2f4b8e-9c3d-1e7f-b0a5-3d2c1e7f0b9a`            | Qdrant automatically assigns an ID if not provided.                        |
| `vector`      | Array of Float   | The embedding vector representing the semantic meaning of the text.         | `[0.123, -0.456, 0.789, ...]`                     | The dimension of the vector depends on the embedding model used.           |
| `payload`     | Object           | A JSON object containing the metadata and actual content associated with the vector. | See Payload Fields section below.                 | This is where all queryable and retrievable data, apart from the vector itself, is stored. |

## Payload Fields

The `payload` object contains the following fields:

| Field Name      | Data Type     | Description                                                                                      | Example                                  | Notes                                                                                                |
|-----------------|---------------|--------------------------------------------------------------------------------------------------|------------------------------------------|------------------------------------------------------------------------------------------------------|
| `text`          | String        | The original text chunk that was vectorized.                                                     | "This is a sample text for the vector."  | This is the content that will be used in the context for the LLM.                                    |
| `document_id`   | String        | Identifier for the source document from which the text was extracted.                            | "doc_001"                                | Useful for tracing back the origin of the information.                                               |
| `chunk_id`      | String/Integer| Identifier for the specific chunk within the source document.                                    | "chunk_003" or `3`                       | Helps in uniquely identifying parts of a larger document.                                            |
| `memory_type`   | String        | Indicates the type of memory this vector represents.                                             | "short_term", "long_term", "summary"     | Crucial for implementing the tiered search flow (short_term → summary → long_term).                  |
| `user_id`       | String        | Identifier for the user associated with this memory (if applicable).                             | "user_abc_123"                           | For personalization or multi-tenant scenarios. Can be optional.                                      |
| `session_id`    | String        | Identifier for the session during which this memory was created (if applicable).                 | "session_xyz_789"                        | For tracking conversation context. Can be optional.                                                  |
| `message_id`    | String        | Identifier for the specific message that generated this vector (if applicable).                  | "msg_1a2b3c"                             | For fine-grained tracking. Can be optional.                                                          |
| `token_count`   | Integer       | The number of tokens in the `text` field, calculated using the tokenizer (e.g., tiktoken).       | `42`                                     | Useful for managing context window limits and for analytics.                                       |
| `created_at`    | Timestamp     | The timestamp when the vector was created/inserted.                                              | "2023-10-27T10:30:00Z"                   | For time-based filtering or sorting.                                                                 |
| `source`        | String        | The original source of the information (e.g., file name, URL, application module).             | "internal_docs/feature_x.md"             | Provides context about where the information came from. Can be optional.                             |
| `metadata`      | Object        | A flexible field for any other relevant metadata not covered by the above fields.                | `{"custom_tag": "urgent", "version": 1.2}` | Allows for extensibility without altering the core schema.                                           |

## Collections

We will utilize distinct collections based on the `memory_type` or manage different memory types within a single collection using filtering on the `memory_type` payload field. The specific strategy will depend on the querying requirements and performance considerations.

Common collections might include:

*   `short_term_memory`: Stores recent interactions or volatile data.
*   `long_term_memory`: Stores persistent knowledge base or historical data.
*   `summary_memory`: Stores summaries of conversations or documents.

Alternatively, a single collection (e.g., `unified_memory`) could be used with a filter on `payload.memory_type`.

## Indexing

Payload fields that are frequently used in filtering queries (e.g., `memory_type`, `user_id`, `document_id`) should be indexed in Qdrant to ensure fast and efficient retrieval.

This schema provides a comprehensive framework for storing and querying vectorized content along with its associated metadata, enabling a sophisticated semantic search system.
