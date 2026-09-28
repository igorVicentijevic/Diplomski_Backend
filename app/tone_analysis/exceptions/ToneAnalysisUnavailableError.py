class ToneAnalysisUnavailableError(RuntimeError):
    """Raised when the provider cannot serve tone analyses.

    It signals an exhausted quota or a rate limit rather than a problem
    with a single article, so the whole batch must be skipped instead of
    retrying the remaining articles one by one.
    """
