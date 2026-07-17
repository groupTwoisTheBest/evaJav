"""main.py"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import init_db
from app.routes import router

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    init_db()