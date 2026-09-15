from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router

app = FastAPI(
    title="Urban Land Record Management API",
    description="AI-Enabled Geospatial Integration Platform",
    version="0.1.0"
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Geospatial Integration Platform API is running"}

