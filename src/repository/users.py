from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):

    """
    The get_user_by_email function takes in an email and returns the user associated with that email.
        If no user is found, it will return None.

    :param email: str: Specify the email of the user to be searched for
    :param db: AsyncSession: Pass in the database session
    :return: A user object if a user with the given email exists in the database, otherwise it returns none
    :doc-author: Trelent
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):

    """
    The create_user function creates a new user in the database.

    :param body: UserSchema: Validate the request body
    :param db: AsyncSession: Create a database session
    :return: A user object
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):

    """
    The update_token function updates the refresh token for a user.

    :param user: User: Specify the user that we are updating
    :param token: str | None: Set the refresh token of the user to a new value
    :param db: AsyncSession: Pass the database session into the function
    :return: A boolean value
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:

    """
    The confirmed_email function takes in an email and a database session,
    and sets the confirm field of the user with that email to True.


    :param email: str: Get the email of the user
    :param db: AsyncSession: Pass the database connection to the function
    :return: None
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirm = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:

    """
    The update_avatar_url function updates the avatar url of a user.

    :param email: str: Identify the user whose avatar url is to be updated
    :param url: str | None: Specify that the url parameter can either be a string or none
    :param db: AsyncSession: Pass in the database session
    :return: A user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
