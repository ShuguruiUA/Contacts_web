from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
    Response,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.database.db import get_db
from src.repository import users as rep_users
from src.schemas.user import (
    UserSchema,
    TokenSchema,
    UserResponseSchema,
    LogoutResponse,
    RequestEmail,
)
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post(
    "/signup",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(times=1, seconds=15))],
)
async def signup(

    body: UserSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    """
    The signup function creates a new user in the database.
    It takes an email, username and password as input.
    The function then checks if the email is already taken by another user. If it is,
    it returns a 409 Conflict error message to indicate that this account already exists.

    :param body: UserSchema: Get the data from the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the request
    :param db: AsyncSession: Get the database session
    :param : Get the user id from the path
    :return: A userschema object
    :doc-author: Trelent
    """
    exist_user = await rep_users.get_user_by_email(body.email, db)
    if exist_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXIST
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await rep_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post(
    "/login",
    response_model=TokenSchema, dependencies=[Depends(RateLimiter(times=1, seconds=15))],
)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):

    """
    The login function is used to authenticate a user.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: AsyncSession: Get a database connection
    :return: A dict with the access_token, refresh_token and token type
    :doc-author: Trelent
    """
    user = await rep_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_CREDENTIALS
        )
    if not user.confirm:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.NOT_CONFIRM  # "Not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_CREDENTIALS
        )
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await rep_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", dependencies=[Depends(RateLimiter(times=1, hours=24))]
            )
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):

    """
    The refresh_token function is used to refresh the access token.
        The function takes in a refresh token and returns a new access_token,
        refresh_token, and the type of bearer.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the request header
    :param db: AsyncSession: Get the database session
    :param : Get the user from the database
    :return: A new access token and refresh token
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await rep_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await rep_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await rep_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/logout", response_model=LogoutResponse, status_code=status.HTTP_202_ACCEPTED
)
async def logout(
    user=Depends(auth_service.get_current_user),
    db=Depends(get_db),
):

    """
    The logout function will logout the user by removing their refresh token from the database.

    :param user: Get the current user
    :param db: Access the database
    :param : Get the current user from the database
    :return: A dictionary with the result
    :doc-author: Trelent
    """
    user.refresh_token = None
    await db.commit()

    return {"result": "Logout success"}


@router.get(
    "/confirmed_email/{token}", dependencies=[Depends(RateLimiter(times=1, hours=24))]
)
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):

    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        Then, it checks if that user exists in our database, and if they do not exist,
        an error message is returned. If they do exist but their account has already been confirmed,
        another error message is returned. Otherwise (if they exist and their account has not yet been confirmed),
        we update their record in our database so that 'confirm' = True.

    :param token: str: Get the token from the url
    :param db: AsyncSession: Get the database session
    :return: A message that the email is already confirmed if the user has already confirmed their email
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await rep_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirm:
        return {"message": "Your email is already confirmed"}
    await rep_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email", # dependencies=[Depends(RateLimiter(times=1, hours=24))]
             )
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    """
    The request_email function is used to send an email to the user with a link that will confirm their account.
        The function takes in a RequestEmail object, which contains the user's email address.
        It then checks if there is already a confirmed account associated with that email address, and returns an error message if so.
        If not, it sends an email containing a confirmation link.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add tasks to the background task queue
    :param request: Request: Get the base url of the server
    :param db: AsyncSession: Pass the database connection to the function
    :param : Get the user's email address
    :return: A message to the user when they request an email
    :doc-author: Trelent
    """
    user = await rep_users.get_user_by_email(body.email, db)

    if user.confirm:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}
