import logging
import os

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

logger = logging.getLogger(__name__)

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Use service role key for server-side auth verification
supabase_client: Client | None = (
    create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY)
    if SUPABASE_URL and (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY)
    else None
)


async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials

    # Strategy 1: Decode locally using SUPABASE_JWT_SECRET (fastest)
    if JWT_SECRET and JWT_SECRET != "your-supabase-jwt-secret-from-project-settings":
        try:
            payload = jwt.decode(
                token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False}
            )
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(
                f"Local JWT decode failed, falling back to Supabase API: {e}"
            )
            # Fall through to Strategy 2

    # Strategy 2: Verify via Supabase Auth API
    if not supabase_client:
        raise HTTPException(
            status_code=500,
            detail="Auth not configured: no JWT secret or Supabase client",
        )

    try:
        user_response = supabase_client.auth.get_user(token)
        user = getattr(user_response, "user", None)
        if not user or not getattr(user, "id", None):
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return getattr(user, "id")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supabase auth verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def get_current_user(request: Request, user_id: str = Security(verify_jwt)):
    request.state.user_id = user_id
    return user_id
