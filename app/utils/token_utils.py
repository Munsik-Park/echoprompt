import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Return the number of tokens in the given text using tiktoken."""
    try:
        encoding = tiktoken.get_encoding(model)
    except Exception:
        encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
