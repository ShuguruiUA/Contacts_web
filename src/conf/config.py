from pydantic import ConfigDict, validator, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://user:password@domain:5432/db_name"
    #"postgresql+asyncpg://root:changeme@localhost:5432/contacts_db"
    POSTGRES_USER: str = "username"
    POSTGRES_DB: str = "db_name"
    POSTGRES_PASSWORD: str = "db_password"
    POSTGRES_DOMAIN: str = "db_server_domain"
    POSTGRES_PORT: int = 5432
    SECRET_KEY: str = "secret_key"
    ALGORITHM: str = "HS256"
    MAIL_USERNAME: str = "mail_username"
    MAIL_PASSWORD: str = "mail_password"
    MAIL_FROM: str = "email@mail.com"
    MAIL_FROM_NAME: str = "Displayed email name"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.mail_server_name"
    MAIL_SSL_TLS: bool = "True"
    REDIS_DOMAIN: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    CLD_NAME: str = "name"
    CLD_API_KEY: int = 123456789098765
    CLD_API_SECRET: str = "Cloudinary API secret"

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: any):
        """
        The validate_algorithm function is a custom validator that ensures the algorithm used to sign the JWT is either HS256 or HS512.
        The validate_algorithm function takes in one parameter, cls, which represents the class being validated. The second parameter, v,
        represents the value of algorithm being passed into our JWT payload.

        :param cls: Pass the class that is being validated
        :param v: any: Indicate that the value passed to the function can be of any type
        :return: The value of the algorithm
        :doc-author: Trelent
        """
        if v not in ["HS256", "HS512"]:
            raise ValueError("Algorithm must be HS256 or HS512")
        return v

    model_config = ConfigDict(exctra="ignore", env_file=".env", env_file_encoding="utf-8")  # noqa


config = Settings()
