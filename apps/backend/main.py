import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from middleware.auth import get_current_user

app = FastAPI(title="Cortex API")

# Configure CORS
origins = [
    os.getenv("VITE_FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Cortex FastAPI backend running"}


@app.get("/api/me")
async def get_me(request: Request, user_id: str = Depends(get_current_user)):
    # Testing the authentication middleware
    return {"message": "Authentication successful", "user_id": request.state.user_id}
