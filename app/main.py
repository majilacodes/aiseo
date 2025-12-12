from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.core.db import Base, engine
from app.api.routes import router


def create_tables():
    Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SEO Engine API",
    description="Backend service for generating SEO-optimized articles",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path("static")
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router, prefix="/api/v1", tags=["jobs"])


@app.on_event("startup")
async def startup_event():
    create_tables()


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "SEO Engine API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/ui", include_in_schema=False)
def ui():
    return RedirectResponse(url="/static/index.html", status_code=302)


@app.get("/health")
def health_check():
    return {"status": "healthy"}

