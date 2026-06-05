CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    target_asset_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS
ALTER TABLE entity_relationships ENABLE ROW LEVEL SECURITY;
-- Note: Requires joining user_memories to verify ownership, or for simplicity in this migration:
CREATE POLICY "Users can manage their own relationships" ON entity_relationships FOR ALL USING (
    EXISTS (SELECT 1 FROM user_memories WHERE id = entity_relationships.source_asset_id AND user_id = auth.uid())
);
