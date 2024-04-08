from http.client import HTTPException
from pathlib import Path

import redis.asyncio as redis
from fastapi import FastAPI, Depends, Request
from fastapi_limiter import FastAPILimiter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import config

app = FastAPI()

origins = ["http://localhost:8000",
           "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')

BASE_DIR = Path(".")

app.mount("/static", StaticFiles(directory=BASE_DIR / "src" / "static"), name="static")


@app.on_event("startup")
async def startup():
    r = await redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, password=config.REDIS_PASSWORD, db=0)
    await FastAPILimiter.init(r)


templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "our": "Contacts_web 1.0"}
    )


@app.get('/')
def index():
    return {"message": "Contact Application"}


@app.get('/api/healthchecker')
async def healthcheker(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connection to the DB")
