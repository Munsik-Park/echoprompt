# Test Scenarios for Semantic Search

This document outlines various test scenarios to validate the functionality and effectiveness of the Qdrant-based semantic search system. These use cases cover different query types and expected behaviors across the multi-stage search flow (short-term, summary, long-term memory).

## 1. Basic Functionality Tests

These tests ensure the fundamental search mechanics are working.

| Test Case ID | Description                                      | Steps                                                                                                | Expected Outcome                                                                                                | Memory Focus       |
|--------------|--------------------------------------------------|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|--------------------|
| UC-001       | Simple keyword query matching existing content   | 1. Insert a known text chunk into short-term memory. <br> 2. Query with a keyword from that chunk.     | The known text chunk is retrieved with high relevance.                                                          | Short-Term         |
| UC-002       | Semantic similarity query                        | 1. Insert a text chunk. <br> 2. Query with a semantically similar phrase (not exact keywords).         | The original text chunk is retrieved.                                                                           | Short-Term/Summary |
| UC-003       | Query with no matching results                   | 1. Query with obscure terms not present in any memory.                                                 | No results (or very low relevance results) are returned. System handles empty results gracefully.               | All                |
| UC-004       | Query for content in long-term memory            | 1. Ensure a specific document is only in long-term memory. <br> 2. Query for content from this document. | The document is retrieved, indicating fallback to long-term memory occurred.                                    | Long-Term          |
| UC-005       | Query for summarized content                     | 1. Have a long conversation summarized into summary memory. <br> 2. Query for a key point from the summary. | The relevant summary chunk is retrieved.                                                                        | Summary            |

## 2. Search Flow Logic Tests

These tests validate the staged search flow (short_term → summary → long_term).

| Test Case ID | Description                                              | Steps                                                                                                                                                              | Expected Outcome                                                                                                                                  | Memory Focus       |
|--------------|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|
| UC-006       | Prioritization of Short-Term Memory                      | 1. Insert relevant content for a query in both short-term and long-term memory. <br> 2. Execute query.                                                               | Results from short-term memory are prioritized (e.g., appear first, have higher scores).                                                          | Short-Term first   |
| UC-007       | Fallback from Short-Term to Summary Memory             | 1. Insert content A into short-term, content B (relevant to query) into summary. <br> 2. Query in a way that content A is insufficient/less relevant.                | Content B from summary memory is retrieved after short-term memory search yields insufficient results.                                            | Short-Term, Summary|
| UC-008       | Fallback from Summary to Long-Term Memory                | 1. Insert content A (less relevant) into short-term/summary. <br> 2. Insert content B (most relevant) into long-term. <br> 3. Query for content B.                  | Content B from long-term memory is retrieved if short-term and summary searches are configured to be insufficient.                                | All stages         |
| UC-009       | Sufficient results from early stage prevent fallback     | 1. Insert highly relevant content for a query in short-term memory. <br> 2. Ensure other memories have less relevant info. <br> 3. Execute query.                   | Only results from short-term memory are used for context; no unnecessary search in summary/long-term. (Depends on threshold settings)           | Short-Term         |

## 3. Payload and Filtering Tests (Based on Schema)

These tests ensure metadata in the payload can be effectively used.

| Test Case ID | Description                                       | Steps                                                                                                     | Expected Outcome                                                                  | Schema Fields Used    |
|--------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|-----------------------|
| UC-010       | Filter by `user_id`                               | 1. Insert memories for different `user_id`s. <br> 2. Query with a specific `user_id` filter.              | Only results matching the specified `user_id` are returned.                       | `user_id`             |
| UC-011       | Filter by `session_id`                            | 1. Insert memories for different `session_id`s. <br> 2. Query with a specific `session_id` filter.          | Only results matching the specified `session_id` are returned.                    | `session_id`          |
| UC-012       | Filter by `memory_type` (if using unified collection) | 1. Insert data with various `memory_type` tags. <br> 2. Query specifically for `memory_type: "summary"`. | Only summary vectors are retrieved.                                               | `memory_type`         |
| UC-013       | Query involving `document_id`                     | 1. Insert chunks from various `document_id`s. <br> 2. Search for content expected to be in a specific doc. | Retrieved chunks correctly show the `document_id`.                                | `document_id`         |
| UC-014       | Retrieval of `text` and `token_count`             | 1. Insert a vector. <br> 2. Perform a search that retrieves this vector.                                  | The payload correctly includes the original `text` and its `token_count`.         | `text`, `token_count` |

## 4. Context Assembly and LLM Prompt Tests

These tests focus on how the retrieved context is used.

| Test Case ID | Description                                       | Steps                                                                                                                          | Expected Outcome                                                                                                |
|--------------|---------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| UC-015       | Context truncation for LLM window                 | 1. Retrieve a large amount of relevant text exceeding LLM context window. <br> 2. Observe context assembly.                     | The assembled context is truncated appropriately to fit the LLM's limits, prioritizing more relevant info.      |
| UC-016       | Correct information order in prompt               | 1. Retrieve multiple chunks. <br> 2. Examine the assembled context for the LLM prompt.                                         | Information is ordered logically (e.g., by relevance or chronological order if applicable).                   |
| UC-017       | LLM response quality with retrieved context       | 1. Ask a question requiring specific information present in the vector store. <br> 2. System retrieves context and queries LLM. | LLM provides an accurate answer based on the retrieved context.                                                 |
| UC-018       | LLM response when context is insufficient         | 1. Ask a question where relevant context is sparse or missing from vector store. <br> 2. System queries LLM.                  | LLM indicates inability to answer definitively or provides a general answer, not hallucinating specifics.       |

## 5. Edge Cases and Error Handling

| Test Case ID | Description                                       | Steps                                                                                             | Expected Outcome                                                                  |
|--------------|---------------------------------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| UC-019       | Query with special characters or empty string     | 1. Submit a query containing various special characters. <br> 2. Submit an empty query string.        | System handles gracefully, either by sanitizing, returning an error, or no results. |
| UC-020       | Qdrant connection issues                          | 1. Simulate Qdrant being unavailable during a search.                                             | System returns a meaningful error message; does not crash.                        |
| UC-021       | Embedding model failure                           | 1. Simulate failure during query embedding generation.                                            | System returns a meaningful error message.                                        |

These use cases provide a starting point for testing. Specific implementations may require additional, more detailed test scenarios.
