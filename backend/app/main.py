
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.api import router
from services.database import mark_interrupted_jobs

app = FastAPI(
    title="AI Background Studio API",
    description="AI-powered video background removal API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*-3000\.app\.github\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AI Background Studio API",
        "status": "running"
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "background-studio-backend",
        "ai_model": "RVM MobileNetV3",
        "ffmpeg": "available"
    }


@app.on_event("startup")
async def recover_interrupted_jobs():
    count = mark_interrupted_jobs()
    print(f"Recovered {count} interrupted processing job(s).")


app.include_router(router)
