from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.repository import contacts as rep_contacts
from src.schemas.contact import ContactSchema, ContactUpdateSchema, ContactResponseSchema
from src.services.auth import auth_service

router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get("/", response_model=list[ContactResponseSchema],
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def get_contacts(
        limit: int = Query(10, ge=10, le=500),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        user: User = Depends(auth_service.get_current_user),
):
    contacts = await rep_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponseSchema,
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):
    contact = await rep_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.post("/", response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await rep_contacts.create_contact(body, db, user)
    return contact


@router.put("/{contact_id}", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def update_contact(body: ContactUpdateSchema, contact_id: int = Path(ge=1),
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)
                         ):
    contact = await rep_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.delete("/{contact_id}", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def delete_contact(
        contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
        user: User = Depends(auth_service.get_current_user)
):
    contact = await rep_contacts.delete_contact(contact_id, db, user)
    return contact


@router.get("/find/{query}", response_model=list[ContactResponseSchema],
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def find_contact(query: str, db: AsyncSession = Depends(get_db),
                       user: User = Depends(auth_service.get_current_user)):
    contacts = await rep_contacts.find_contacts(query, db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts


@router.get("/upcoming_birthdays/", response_model=list[ContactResponseSchema],
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def upconming_birthday(db: AsyncSession = Depends(get_db),
                             user: User = Depends(auth_service.get_current_user)):
    contacts = await rep_contacts.upcoming_birthday(db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts
