"""Short-lived, per-session Stack Overflow search history.

No global database access. A later account system can add private persistence.
"""


def add_search(entries, query, language, count, limit=15):
    """Newest first, dedupe by (query, language), with a bounded list."""
    clean = (query or "").strip()[:180]
    if not clean:
        return list(entries or [])
    record = {"query": clean, "language": str(language), "count": max(0, int(count))}
    other = [
        dict(entry) for entry in (entries or [])
        if (entry.get("query"), entry.get("language")) != (clean, str(language))
    ]
    return ([record] + other)[:max(1, int(limit))]
