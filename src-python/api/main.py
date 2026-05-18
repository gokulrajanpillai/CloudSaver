from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, cleanup, duplicates, gdrive, icloud, optimize, scan, sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="CloudSaver Sidecar", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420", "http://127.0.0.1:1420"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/scan")
app.include_router(gdrive.router, prefix="/gdrive")
app.include_router(icloud.router, prefix="/icloud")
app.include_router(duplicates.router, prefix="/duplicates")
app.include_router(cleanup.router, prefix="/cleanup")
app.include_router(optimize.router, prefix="/optimize")
app.include_router(auth.router, prefix="/auth")
app.include_router(sources.router, prefix="/sources")


@app.get("/health")
async def health():
    return {"status": "ok"}
