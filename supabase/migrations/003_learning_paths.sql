CREATE TABLE generated_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    topic_context VARCHAR(100) NOT NULL,
    syllabus_structure JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS
ALTER TABLE generated_learning_paths ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own paths" ON generated_learning_paths FOR ALL USING (user_id = auth.uid());
