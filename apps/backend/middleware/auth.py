"""Authentication for local single-user mode.

The multi-user Supabase JWT flow has been removed. A single hardcoded local
user ID is returned so every query stays scoped to one "user" without any
login step. The ID must match the frontend's hardcoded user
(see apps/frontend/src/contexts/AuthContext.jsx).
"""

import logging

logger = logging.getLogger(__name__)

# Synthetic local user. Must be a valid UUID because the Supabase schema types
# user_id as uuid in user_memories, job_tracking, plates, etc. Must match the
# frontend's hardcoded user (apps/frontend/src/contexts/AuthContext.jsx).
LOCAL_USER_ID = "00000000-0000-0000-0000-000000000000"


async def get_current_user():
    # Bypassing auth for local single-user mode
    return LOCAL_USER_ID
