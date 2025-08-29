from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import gumroad, creator, download

app = FastAPI(title="Gumstamp Pro", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gumroad.router, prefix="/api/gumroad", tags=["gumroad"])
app.include_router(creator.router, prefix="/api/creator", tags=["creator"])
app.include_router(download.router, tags=["download"])

@app.get("/")
def root():
    return {"name": "Gumstamp Pro", "health": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
