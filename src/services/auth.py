from datetime import datetime, timedelta
from typing import Optional
import pickle

import redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.repository import users as rep_users
from src.conf.config import config


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    SECRET_KEY = config.SECRET_KEY
    ALGORITHM = config.ALGORITHM

    def verify_password(self, plain_password, hashed_password):

        """
        The verify_password function takes a plain-text password and a hashed password as arguments.
        It then uses the pwd_context object to verify that the plain-text password matches the hashed
        password.

        :param self: Make the method work for a specific instance of the class
        :param plain_password: Compare the password that is entered by the user to a hashed version of it
        :param hashed_password: Compare the hashed password stored in the database with the plain text password entered by a user
        :return: A boolean value
        :doc-author: Trelent
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):

        """
        The get_password_hash function takes a password as an argument and returns the hashed version of that password.
        The hash is generated using the pwd_context object's hash method, which uses bcrypt to generate a secure hash.

        :param self: Represent the instance of the class
        :param password: str: Pass in the password that we want to hash
        :return: A hash of the password
        :doc-author: Trelent
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):

        """
        The create_access_token function creates a JWT token that is used to authenticate the user.
        The function takes in two arguments: data and expires_delta. The data argument is a dictionary
        that contains information about the user, such as their username and password. The expires_delta
        argument specifies how long the access token will be valid for (in seconds). If no value is provided,
        the default value of 15 minutes will be used.

        :param self: Represent the instance of the class
        :param data: dict: Store the data that will be encoded in the jwt
        :param expires_delta: Optional[float]: Set the time limit for a token
        :return: A jwt token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def create_refresh_token(
        self, data: dict, expires_telta: Optional[float] = None
    ):

        """
        The create_refresh_token function creates a refresh token for the user.
            Args:
                data (dict): A dictionary containing the user's id and username.
                expires_telta (Optional[float]): The number of seconds until the token expires. Defaults to None, which sets it to 7 days from now.

        :param self: Represent the instance of the class
        :param data: dict: Pass the user information
        :param expires_telta: Optional[float]: Set the expiration time of the refresh token
        :return: An encoded refresh token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_telta:
            expire = datetime.utcnow() + timedelta(seconds=expires_telta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):

        """
        The get_current_user function is a dependency that will be used in the
            protected endpoints. It takes a token as an argument and returns the user
            associated with that token. If no user is found, it raises an exception.

        :param self: Refer to the class itself
        :param token: str: Get the token from the authorization header
        :param db: AsyncSession: Create a database session
        :return: A user object
        :doc-author: Trelent
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception
        user_hash = str(email)
        user = self.cache.get(user_hash)

        if user is None:
            user = await rep_users.get_user_by_email(email, db)
            print("from db")
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            user = pickle.loads(user)
            print("from cache")
        return user

    async def decode_refresh_token(self, refresh_token: str):

        """
        The decode_refresh_token function is used to decode the refresh token.
        It will raise an exception if the token is invalid or has expired.

        :param self: Represent the instance of the class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The email address of the user who requested a refresh token
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithm=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def create_email_token(self, data: dict):

        """
        The create_email_token function takes a dictionary of data and returns a token.
        The token is created using the JWT library, which uses the SECRET_KEY and ALGORITHM to create an encoded string.
        The data dictionary contains information about the user's email address, username, password reset code (if applicable),
        and expiration date for the token.

        :param self: Represent the instance of the class
        :param data: dict: Pass in the data that will be encoded into a token
        :return: A token that is used to verify the user's email address
        :doc-author: Trelent
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):

        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        It does this by decoding the JWT using our secret key and algorithm, then returning the subject (sub) field of the payload.

        :param self: Represent the instance of the class
        :param token: str: Pass the token that is sent to the user's email
        :return: An email address
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )

    async def create_reset_password_token(self, email: str, token: str, data: dict):

        """
        The create_reset_password_token function creates a token that will be sent to the user's email address.
        The token is created using the JWT library and contains information about when it was issued,
        when it expires, and what data should be used to reset the password.

        :param self: Represent the instance of the class
        :param email: str: Specify the email of the user who is requesting a password reset
        :param token: str: Pass in the token that was generated by the create_reset_password_token function
        :param data: dict: Pass in the user's email and token
        :return: A token that is encoded with the user's email, a secret key and an algorithm
        :doc-author: Trelent
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=[self.ALGORITHM])
        return token


auth_service = Auth()
