import os

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
# Ensure SUPABASE_JWT_SECRET is added to your environment variables
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

supabase_client: Client = (
    create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if SUPABASE_URL and SUPABASE_ANON_KEY
    else None
)


async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        if JWT_SECRET:
            # Decode locally using the Supabase JWT secret (HS256)
            payload = jwt.decode(
                token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False}
            )
            return payload["sub"]
        else:
            # Fallback: verify via Supabase API if secret isn't provided
            if not supabase_client:
                raise HTTPException(
                    status_code=500, detail="Supabase client not configured"
                )
            user_response = supabase_client.auth.get_user(token)
            if not user_response.user:
                raise HTTPException(
                    status_code=401, detail="Invalid authentication credentials"
                )
            return user_response.user.id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


async def get_current_user(request: Request, user_id: str = Security(verify_jwt)):
    # Attach user_id to the request state
    request.state.user_id = user_id
    return user_id
