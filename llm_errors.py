from google.genai import errors

# These errors may succeed later; 5xx errors are also handled by ServerError below.
TRANSIENT_CODES = {408, 429}


def is_transient(error: errors.APIError) -> bool:
    """Return whether an API error is temporary rather than a request/setup issue."""
    # Gemini's ServerError represents 5xx responses, which may resolve later.
    if isinstance(error, errors.ServerError):
        return True

    # Timeouts and rate limits may pass after waiting; 400 and 401 should be fixed.
    return error.code in TRANSIENT_CODES