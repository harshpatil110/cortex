CREATE TABLE job_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_id UUID REFERENCES user_memories(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    current_stage VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_jobs_user_status ON job_tracking(user_id, status);

-- RLS
ALTER TABLE job_tracking ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own jobs" ON job_tracking FOR ALL USING (user_id = auth.uid());
