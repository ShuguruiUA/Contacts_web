import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.repository.users import (
    get_user_by_email, create_user, update_token, confirmed_email, update_avatar_url
)
from src.schemas.user import UserSchema, UserResponseSchema, TokenSchema, LogoutResponse, RequestEmail


class TestAsyncUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = User(id=1, username="test_user", password="test_password", email="test_email")
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        email = "test_email"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_email(email, self.session)
        self.assertEqual(result, self.user)

    async def test_create_user(self):
        body = UserSchema(username="test_user", password="password", email="test@email.com")
        result = await create_user(body, self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.password, body.password)
        self.assertEqual(result.email, body.email)

    async def test_update_token(self):
        token = "test_token"
        result = await update_token(self.user, token, self.session)
        self.assertIsNone(result)

    async def test_confirmed_email(self):
        user = self.user
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await confirmed_email(user.email, self.session)
        self.assertIsNone(result)

    async def test_update_avatar_url(self):
        user = self.user
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        new_avatar_url = "path/to/avatar.png"
        result = await update_avatar_url(user.email, new_avatar_url, self.session)
        self.assertEqual(result.avatar, new_avatar_url)

if __name__ == '__main__':
    unittest.main()
