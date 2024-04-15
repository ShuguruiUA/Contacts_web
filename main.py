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

BASE_DIR = Path(__file__).resolve().parent
static_ = BASE_DIR.joinpath("src").joinpath("static")
app.mount("/static", StaticFiles(directory=str(static_)), name="static")


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are needed by your app, such as databases or caches.

    :return: A coroutine
    :doc-author: Trelent
    """
    r = await redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, password=config.REDIS_PASSWORD, db=0)
    await FastAPILimiter.init(r)


templates_ = BASE_DIR.joinpath("src").joinpath("templates")
templates = Jinja2Templates(directory=str(templates_))


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    The index function is executed when someone visits the root URL of our site:
    http://localhost:8000/
    It returns a TemplateResponse, which contains all the information that Starlette needs to construct an HTTP response.
    The first argument passed to TemplateResponse is a path to an HTML template file.
    Starlette will render this template and return it as part of the HTTP response.

    :param request: Request: Pass the request object to the template
    :return: A templateresponse object, which is a special type of response that renders
    :doc-author: Trelent
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "our": "Contacts_web 1.0"}
    )


@app.get('/')
def index():
    """
    The index function is the default function for this application.
    It returns a dictionary with a message key and value of &quot;Contact Application&quot;.

    :return: A dictionary with the key &quot;message&quot; and value &quot;contact application&quot;
    :doc-author: Trelent
    """
    return {"message": "Contact Application"}


@app.get('/api/healthchecker')
async def healthcheker(db: AsyncSession = Depends(get_db)):
    """
    The healthcheker function is a simple endpoint that returns a welcome message.
    It also checks the database connection and raises an error if it fails.

    :param db: AsyncSession: Get the database session from the dependency
    :return: A dictionary with a message
    :doc-author: Trelent
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connection to the DB")
