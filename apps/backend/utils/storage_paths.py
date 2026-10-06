"""Helpers for Supabase storage paths stored in the database.

Storage path columns (e.g. ``thumbnail_storage_path``) are stored with the
bucket name as a prefix, e.g. ``"thumbnails/<user_id>/<memory_id>.webp"``.
``supabase.storage.from_(bucket).create_signed_url(...)`` expects the
*in-bucket* object key without that prefix, so it must be stripped first.
"""


def strip_bucket_prefix(stored_path: str | None, bucket: str) -> str | None:
    """Return the in-bucket object key for a stored ``"<bucket>/<key>"`` path.

    Returns ``None`` when ``stored_path`` is falsy; returns the path unchanged
    when it does not start with the bucket prefix.
    """
    if not stored_path:
        return None
    prefix = f"{bucket}/"
    if stored_path.startswith(prefix):
        return stored_path[len(prefix) :]
    return stored_path
