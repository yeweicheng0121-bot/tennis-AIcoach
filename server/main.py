from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Tennis AI Coach", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from server.api.auth import router as auth_router
from server.api.users import router as users_router
from server.api.videos import router as videos_router
from server.api.health import router as health_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(videos_router)
app.include_router(health_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
