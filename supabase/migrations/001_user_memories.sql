CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    storage_path TEXT,
    thumbnail_storage_path TEXT,   
    creator_metadata JSONB DEFAULT '{}'::jsonb,
    raw_transcript TEXT,
    ocr_extracted_text TEXT,
    ai_summary JSONB DEFAULT '{}'::jsonb,
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Full-text search GIN index
CREATE INDEX idx_memories_text_search ON user_memories USING GIN(to_tsvector('english', COALESCE(raw_transcript,'') || ' ' || COALESCE(ocr_extracted_text,'')));
-- Performance indexes
CREATE INDEX idx_memories_user_created ON user_memories(user_id, created_at DESC);
CREATE INDEX idx_memories_content_type ON user_memories(content_type);
CREATE INDEX idx_memories_indexed ON user_memories(indexed);

-- RLS
ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own memories" ON user_memories FOR ALL USING (user_id = auth.uid());
