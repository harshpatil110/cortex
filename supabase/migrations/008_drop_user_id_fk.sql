-- Drop user_id foreign-key constraints to auth.users.
--
-- The backend runs in single-user local mode and authenticates every request
-- as a synthetic user id (see apps/backend/middleware/auth.py LOCAL_USER_ID).
-- That id does not exist in auth.users, and FK constraints are enforced even
-- for the service-role key (it bypasses RLS, not FKs), so every INSERT into
-- these tables failed with a foreign-key violation and nothing could ingest.
-- user_id is kept as a plain UUID column for future multi-user support.
-- Idempotent.

ALTER TABLE user_memories
    DROP CONSTRAINT IF EXISTS user_memories_user_id_fkey;
ALTER TABLE generated_learning_paths
    DROP CONSTRAINT IF EXISTS generated_learning_paths_user_id_fkey;
ALTER TABLE plates
    DROP CONSTRAINT IF EXISTS plates_user_id_fkey;
ALTER TABLE job_tracking
    DROP CONSTRAINT IF EXISTS job_tracking_user_id_fkey;
