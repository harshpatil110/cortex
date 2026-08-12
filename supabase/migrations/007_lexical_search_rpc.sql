-- Lexical (full-text) search over user_memories, exposed as an RPC so the
-- backend can call it via supabase.rpc("lexical_search_memories", ...).
-- The tsvector expression matches the GIN index from 001_user_memories.sql.
-- Idempotent.

CREATE OR REPLACE FUNCTION lexical_search_memories(
    query_text TEXT,
    p_user_id UUID,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0,
    p_content_type TEXT DEFAULT NULL,
    p_plate_id UUID DEFAULT NULL,
    p_date_from TIMESTAMPTZ DEFAULT NULL,
    p_date_to TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content_type VARCHAR,
    source_url TEXT,
    thumbnail_path TEXT,
    ai_summary JSONB,
    raw_transcript TEXT,
    ocr_extracted_text TEXT,
    creator_metadata JSONB,
    created_at TIMESTAMPTZ,
    snippet TEXT,
    rank REAL,
    total_count BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    search_tsv tsvector := plainto_tsquery('english', query_text);
    v_total BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM user_memories m
    WHERE m.user_id = p_user_id
      AND to_tsvector('english',
          COALESCE(m.raw_transcript, '') || ' ' || COALESCE(m.ocr_extracted_text, '')) @@ search_tsv
      AND (p_content_type IS NULL OR m.content_type = p_content_type)
      AND (p_plate_id IS NULL OR EXISTS (
          SELECT 1 FROM memory_plates mp
          WHERE mp.memory_id = m.id AND mp.plate_id = p_plate_id))
      AND (p_date_from IS NULL OR m.created_at >= p_date_from)
      AND (p_date_to IS NULL OR m.created_at <= p_date_to);

    RETURN QUERY
    SELECT
        m.id,
        m.content_type,
        m.source_url,
        m.thumbnail_storage_path,
        m.ai_summary,
        m.raw_transcript,
        m.ocr_extracted_text,
        m.creator_metadata,
        m.created_at,
        ts_headline('english',
            COALESCE(m.raw_transcript, '') || ' ' || COALESCE(m.ocr_extracted_text, ''),
            search_tsv,
            'StartSel=<mark>, StopSel=</mark>') AS snippet,
        ts_rank(to_tsvector('english',
            COALESCE(m.raw_transcript, '') || ' ' || COALESCE(m.ocr_extracted_text, '')),
            search_tsv)::real AS rank,
        v_total AS total_count
    FROM user_memories m
    WHERE m.user_id = p_user_id
      AND to_tsvector('english',
          COALESCE(m.raw_transcript, '') || ' ' || COALESCE(m.ocr_extracted_text, '')) @@ search_tsv
      AND (p_content_type IS NULL OR m.content_type = p_content_type)
      AND (p_plate_id IS NULL OR EXISTS (
          SELECT 1 FROM memory_plates mp
          WHERE mp.memory_id = m.id AND mp.plate_id = p_plate_id))
      AND (p_date_from IS NULL OR m.created_at >= p_date_from)
      AND (p_date_to IS NULL OR m.created_at <= p_date_to)
    ORDER BY rank DESC, m.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$;
