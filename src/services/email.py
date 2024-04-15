
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service
from src.conf.config import config

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates'
)


async def send_email(email: EmailStr, username: str, host: str):

    """
    The send_email function sends an email to the user with a link that they can click on to verify their email address.
    The function takes in three parameters:
        -email: The user's email address, which is used as the recipient of the message.
        -username: The username of the user, which is used in both the subject line and body of the message.  This helps personalize it for them!
        -host: The hostname (or IP) where this service is running, so that we can construct a valid URL for them to click on.

    :param email: EmailStr: Specify the email address of the recipient
    :param username: str: Pass the username of the user to be verified
    :param host: str: Pass the hostname of the server to the email template
    :return: A coroutine object
    :doc-author: Trelent
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Email confirmation service notification",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name='verify_email.html')
    except ConnectionErrors as e:
        print(e)