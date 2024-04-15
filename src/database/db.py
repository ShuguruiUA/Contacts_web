import contextlib

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.conf.config import config


class DBSessionManager:
    """
    The DBSessionManager class is a context manager that manages a database session.

    :param url: str: Specify the URL of the database
    """
    def __init__(self, url: str):

        """
        The __init__ function is the constructor for a class. It is called when an object of that class
        is instantiated, and it sets up the attributes of that object. In this case, we are creating a
        database connection engine and session maker using SQLAlchemy's create_engine() function.

        :param self: Represent the instance of the class
        :param url: str: Create the engine
        :return: A session_maker object
        :doc-author: Trelent
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(autoflush=False, autocommit=False,
                                                                     bind=self._engine)

    @contextlib.asynccontextmanager
    async def session(self):
        """
        The session function is a context manager that yields a session object and closes it when the
        context is exited. If the session is not initialized, it raises an exception.

        :param self: Represent the instance of the class
        :return: A session object
        :doc-author: Trelent
        """
        if self._session_maker is None:
            raise Exception("Session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except:
            await session.rollback()
        finally:
            await session.close()


session_manager = DBSessionManager(config.DB_URL)


async def get_db():
    """
    The get_db function is a context manager that yields a session object and closes it when the
    context is exited. If the session is not initialized, it raises an exception.
    :return: A session object
    :doc-author: Trelent
    """
    async with session_manager.session() as session:
        return session
