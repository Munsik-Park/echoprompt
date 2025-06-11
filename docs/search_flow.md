# System Search Flow

This document describes the search and retrieval flow within the system, designed to provide relevant context to a Large Language Model (LLM) based on user queries. The flow utilizes a multi-stage approach involving different types of memory stored in Qdrant.

## Overview

The primary goal of the search flow is to gather the most relevant information from available knowledge sources to assist the LLM in generating an accurate and contextually appropriate response. This involves querying different memory collections in a specific order.

## Search Stages

The search process is sequential and conditional, prioritizing recency and summarized information before falling back to broader long-term knowledge.

```mermaid
graph TD
    A[User Query Input] --> B{1. Short-Term Memory Search};
    B -- Results Found --> E{Context Assembly};
    B -- Results Insufficient / Not Found --> C{2. Summary Memory Search};
    C -- Results Found --> E;
    C -- Results Insufficient / Not Found --> D{3. Long-Term Memory Search (Optional Fallback)};
    D -- Results Found --> E;
    D -- Results Insufficient / Not Found --> E;
    E --> F[LLM Prompt Generation];
    F --> G[LLM API Call];
    G --> H[Response to User];
```

### 1. User Query Input

The process begins when the user submits a query to the system.

### 2. Short-Term Memory Search

*   **Collection(s) Queried**: `short_term_memory` (or a filter on `memory_type: short_term` in a unified collection).
*   **Purpose**: To find information directly related to the current conversation or very recent interactions. This memory type typically stores raw conversational snippets or recent user-specific data.
*   **Logic**:
    *   The user's query is converted into an embedding vector.
    *   A semantic search is performed on the short-term memory collection(s) using this vector.
    *   A predefined number of top-k results are retrieved.
*   **Condition to Proceed**: If the number of relevant results from short-term memory is below a certain threshold (e.g., not enough contextually rich information found) or if this stage is explicitly bypassed, the flow proceeds to the next stage.

### 3. Summary Memory Search

*   **Collection(s) Queried**: `summary_memory` (or a filter on `memory_type: summary`).
*   **Purpose**: To find summarized information from past conversations or documents. Summaries provide a condensed overview and can be very effective for recalling key points from longer interactions or texts.
*   **Logic**:
    *   The user's query embedding is used to search the summary memory collection(s).
    *   Top-k summarized chunks are retrieved.
*   **Condition to Proceed**: If the combined results from short-term and summary memory are still insufficient, or if a deeper search is required, the system may proceed to search long-term memory. This step is crucial for bridging immediate context with broader, condensed knowledge.

### 4. Long-Term Memory Search (Optional Fallback)

*   **Collection(s) Queried**: `long_term_memory` (or a filter on `memory_type: long_term`).
*   **Purpose**: To access a broader knowledge base, such as general documentation, historical data, or less frequently accessed information.
*   **Logic**:
    *   The user's query embedding is used to search the long-term memory collection(s).
    *   Top-k results are retrieved.
*   **Note**: This stage acts as a fallback. The system might be configured to always query long-term memory in parallel or only if preceding stages yield poor results. The issue description implies a flow of `short_term → summary → long_term`.

### 5. Context Assembly

*   **Purpose**: To combine and rank the retrieved information from all search stages.
*   **Logic**:
    *   Results from different memory types are aggregated.
    *   A relevance scoring or re-ranking mechanism might be applied to prioritize the most pertinent information.
    *   Duplicates or highly redundant information might be filtered out.
    *   The final set of context snippets is selected, ensuring it fits within the LLM's context window limit.

### 6. LLM Prompt Generation

*   **Purpose**: To construct a well-formed prompt for the LLM.
*   **Logic**:
    *   The assembled context snippets are formatted and integrated into a prompt template.
    *   The original user query is included in the prompt.
    *   Task-specific instructions (e.g., "Answer the question based on the provided context") are added.

### 7. LLM API Call

*   **Purpose**: To send the generated prompt to the LLM and receive a response.
*   **Logic**:
    *   The prompt is sent to the configured LLM (e.g., OpenAI GPT, Anthropic Claude).
    *   The LLM processes the prompt and generates a response.

### 8. Response to User

*   **Purpose**: To deliver the LLM's generated response to the user.
*   **Logic**:
    *   The response from the LLM is relayed back to the user interface.

## Considerations

*   **Thresholds and k-values**: The number of results to retrieve (k) from each stage and the thresholds for proceeding to the next stage are configurable and critical for balancing relevance and context length.
*   **Re-ranking**: A re-ranking step after context assembly can significantly improve the quality of information fed to the LLM.
*   **Context Window Management**: The total size of the assembled context must not exceed the LLM's maximum context window. Strategies like truncation, summarization of context, or selective inclusion are important.

This search flow aims to be flexible and adaptable, allowing for tuning at each stage to optimize performance for specific use cases.
