from icecream import ic
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .routers import auth, files
from .models.models import Base
from .data.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    ic("Starting up the application...")
    Base.metadata.create_all(bind=engine)

    yield

    ic("Shutting down the application...")
    # Base.metadata.drop_all(bind=engine)


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(files.router)

app.mount(
    "/static",
    StaticFiles(directory="app/frontend/static"),
    name="static",
)


@app.get("/")
async def root():
    return RedirectResponse(
        url="/files",
        status_code=status.HTTP_302_FOUND,
    )
