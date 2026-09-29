from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routes import router

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables when the application starts.
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI fitness plan generator based on the FitBuddy project.",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(router)


# Browsers request /favicon.ico on pages without a <link rel="icon">,
# such as the built-in /docs page.
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.svg", media_type="image/svg+xml")
