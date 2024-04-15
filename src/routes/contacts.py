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

    """
    The get_contacts function returns a list of contacts for the current user.

    :param limit: int: Specify the number of contacts to return
    :param ge: Specify the minimum value of a parameter
    :param le: Limit the number of contacts returned to 500
    :param offset: int: Specify the number of records to skip
    :param ge: Specify a minimum value for the parameter
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user from the database
    :param : Get the contact id from the url
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await rep_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponseSchema,
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):

    """
    The get_contact function returns a contact by its id.

    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user from the auth_service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await rep_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.post("/", response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):

    """
    The create_contact function creates a new contact in the database.

    :param body: ContactSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A contact object, which is the same as the one we defined in schemas
    :doc-author: Trelent
    """
    contact = await rep_contacts.create_contact(body, db, user)
    return contact


@router.put("/{contact_id}", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def update_contact(body: ContactUpdateSchema, contact_id: int = Path(ge=1),
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)
                         ):

    """
    The update_contact function updates a contact in the database.
        The function takes an id of the contact to be updated, and a body containing
        all fields that are to be updated. If any field is not provided, it will not
        be changed in the database.

    :param body: ContactUpdateSchema: Pass the data from the request body to the function
    :param contact_id: int: Specify the id of the contact to be deleted
    :param db: AsyncSession: Get the database session
    :param user: User: Check if the user is authenticated and has access to this route
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await rep_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.delete("/{contact_id}", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def delete_contact(
        contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
        user: User = Depends(auth_service.get_current_user)
):

    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user from the auth_service
    :return: The deleted contact
    :doc-author: Trelent
    """
    contact = await rep_contacts.delete_contact(contact_id, db, user)
    return contact


@router.get("/find/{query}", response_model=list[ContactResponseSchema],
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def find_contact(query: str, db: AsyncSession = Depends(get_db),
                       user: User = Depends(auth_service.get_current_user)):

    """
    The find_contact function is used to find a contact in the database.
        It takes a query string as an argument and returns all contacts that match the query.

    :param query: str: Search for a contact by name
    :param db: AsyncSession: Get the database connection from the dependency injection
    :param user: User: Get the current user
    :return: A list of dictionaries, where each dictionary represents a contact
    :doc-author: Trelent
    """
    contacts = await rep_contacts.find_contacts(query, db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts


@router.get("/upcoming_birthdays/", response_model=list[ContactResponseSchema],
            dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def upconming_birthday(db: AsyncSession = Depends(get_db),
                             user: User = Depends(auth_service.get_current_user)):

    """
    The upconming_birthday function returns a list of contacts with upcoming birthdays.
        The function takes in the database session and the current user as parameters.
        It then calls the upcoming_birthday method from rep_contacts to get a list of contacts with upcoming birthdays.
        If no contact is found, it raises an HTTPException 404 NOT FOUND error.

    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user
    :return: A list of contacts that have upcoming birthdays
    :doc-author: Trelent
    """
    contacts = await rep_contacts.upcoming_birthday(db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts
