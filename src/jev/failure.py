"""TypeSafe/Jev execution failures are operational, never semantic judgments.

A transport, timeout, rate-limit, validation, or service failure means Jev did
not measure. It must never be converted into a negative Noul decision, a Choice
for "none", or a low Score. Callers surface the failure and preserve uncertainty.
"""

from src.jev.models import JevExecutionFailure, JevFailureCategory


class JevOperationalFailure(RuntimeError):
    """Raised when one or more Jev questions did not complete."""

    def __init__(self, failures: tuple[JevExecutionFailure, ...], *, decisions=(), metadata=None) -> None:
        if not failures:
            raise ValueError("a Jev operational failure requires at least one failed question")
        self.failures = tuple(failures)
        self.decisions = tuple(decisions)
        self.metadata = metadata
        categories = ", ".join(sorted({failure.category.value for failure in self.failures}))
        super().__init__(f"Jev failed for {len(self.failures)} question(s); no frontier judgment: {categories}")


def classify_jev_exception(error: BaseException) -> JevFailureCategory:
    """Map an arbitrary SDK exception to an operational category; never a judgment."""
    text = f"{type(error).__name__} {error}".lower()
    if "timeout" in text or "timed out" in text:
        return JevFailureCategory.TIMEOUT
    if ("rate" in text and "limit" in text) or "429" in text:
        return JevFailureCategory.RATE_LIMIT
    if any(token in text for token in ("connect", "transport", "network", "http", "ssl", "dns")):
        return JevFailureCategory.TRANSPORT
    if any(token in text for token in ("validation", "invalid", "missing", "schema")):
        return JevFailureCategory.VALIDATION
    return JevFailureCategory.SERVICE
