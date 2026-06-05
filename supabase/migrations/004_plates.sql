CREATE TABLE plates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    centroid_member_ids JSONB DEFAULT '[]'::jsonb,
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_plates_user ON plates(user_id);

-- RLS
ALTER TABLE plates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own plates" ON plates FOR ALL USING (user_id = auth.uid());
