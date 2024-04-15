from datetime import date, timedelta

from sqlalchemy import select, or_, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):

    """
    The get_contacts function returns a list of contacts for the user.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contacts
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):



    """
    The get_contact function returns a contact from the database.

    :param contact_id: int: Specify the id of the contact we want to get
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Ensure that the user is only able to get contacts they have created
    :return: The contact that matches the id and user
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):

    """
    The create_contact function creates a new contact in the database.

    :param body: ContactSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user id from the token
    :return: A contact object
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User):

    """
    The update_contact function updates a contact in the database.

    :param contact_id: int: Identify the contact to be deleted
    :param body: ContactUpdateSchema: Pass the data that will be used to update the contact
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Check if the contact belongs to the user
    :return: The contact object
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        contact.name = body.name
        contact.surname = body.surname
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.notes = body.notes
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):

    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the id of the contact to be deleted
    :param db: AsyncSession: Pass in the database session
    :param user: User: Get the user object from the database
    :return: The deleted contact if it exists, otherwise none
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def find_contacts(query: str, db: AsyncSession, user: User):

    """
    The find_contacts function takes in a query string, an async database session, and a user object.
    It then creates an SQLAlchemy statement that filters the Contact table by the query string.
    The function returns all contacts that match the filter.

    :param query: str: Search for contacts
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contact objects
    :doc-author: Trelent
    """
    # stmt = select(Contact).filter(or_(
    #     Contact.name.ilike(f"%{query}%"),
    #     Contact.surname.ilike(f"%{query}"),
    #     Contact.email.ilike(f"%{query}%"),
    #     Contact.phone.ilike(f"%{query}%")
    # ).filter_by(user=user)
    # )
    stmt = select(Contact).filter(
        or_(
            Contact.name.ilike(f"%{query}%"),
            Contact.surname.ilike(f"%{query}"),
            Contact.email.ilike(f"%{query}%"),
            Contact.phone.ilike(f"%{query}%")
            )
        ).filter(
            Contact.user == user
        )
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def upcoming_birthday(db: AsyncSession, user: User):

    """
    The upcoming_birthday function returns a list of contacts that have birthdays within the next week.

    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contacts that have a birthday in the next week
    :doc-author: Trelent
    """
    current_date = date.today()
    next_week = current_date + timedelta(days=7)
    stmt = (select(Contact).filter(and_(
        extract("month", Contact.birthday) >= current_date.month,
        extract("day", Contact.birthday) >= current_date.day,
        extract("month", Contact.birthday) <= next_week.month,
        extract("day", Contact.birthday) <= next_week.day
    )
    ).filter_by(user=user))
    contacts = await db.execute(stmt)
    return contacts.scalars().all()
