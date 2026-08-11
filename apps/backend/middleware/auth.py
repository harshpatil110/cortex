"""Authentication for local single-user mode.

The multi-user Supabase JWT flow has been removed. A single hardcoded local
user ID is returned so every query stays scoped to one "user" without any
login step. The ID must match the frontend's hardcoded user
(see apps/frontend/src/contexts/AuthContext.jsx).
"""

import logging

logger = logging.getLogger(__name__)

LOCAL_USER_ID = "local-cortex-user-001"


async def get_current_user():
    # Bypassing auth for local single-user mode
    return LOCAL_USER_ID
