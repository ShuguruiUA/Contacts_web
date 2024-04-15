# import os
# from dotenv import load_dotenv
#
# load_dotenv()

from pathlib import Path

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel



class EmailSchema(BaseModel):
    email: EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME="no-reply@fresenius.com.ua",
    MAIL_PASSWORD="d2W80qwTsWI7",
    MAIL_FROM="no-reply@fresenius.com.u",
    MAIL_PORT=465,
    MAIL_SERVER="mx1.mirohost.net",
    MAIL_FROM_NAME="Example email",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)

app = FastAPI()


@app.post("/send-email")
async def send_in_background(background_tasks: BackgroundTasks, body: EmailSchema):

    """
    The send_in_background function sends an email in the background.

    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param body: EmailSchema: Get the email address of the user
    :return: A dict with a message
    :doc-author: Trelent
    """
    message = MessageSchema(
        subject="Fastapi mail module",
        recipients=[body.email],
        template_body={"fullname": "Billy Jones"},
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    background_tasks.add_task(fm.send_message, message, template_name="example_email.html")

    return {"message": "email has been sent"}


if __name__ == '__main__':
    uvicorn.run('test:app', port=8000, reload=True)

