import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.repository.contacts import (
    get_contacts, get_contact, create_contact, update_contact, delete_contact, find_contacts, upcoming_birthday
)
from src.schemas.contact import ContactSchema, ContactUpdateSchema


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = User(id=1, username="test_user", password="test_password", email="test_email", confirm=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [Contact(id=1, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                            birthday="test_birthday", notes="test_notes", user=self.user),
                    Contact(id=2, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                            birthday="test_birthday", notes="test_notes", user=self.user)]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, user=self.user)
        self.assertEqual(result, contacts)

    async def test_get_contact(self):
        contact = Contact(id=1, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                          birthday="test_birthday", notes="test_notes", user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await get_contact(1, self.session, user=self.user)
        self.assertEqual(result, contact)

    async def test_create_contact(self):
        body = ContactSchema(name="test_name", surname="test_surname", email="test@email.com", phone="9876543210",
                             birthday="1986-01-01", notes="test_notes")
        result = await create_contact(body, self.session, user=self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.notes, body.notes)

    async def test_update_contact(self):
        body = ContactUpdateSchema(name="test_name", surname="test_surname", email="test@email.com", phone="9876543210",
                                   birthday="1986-01-01", notes="test_notes")
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=1, name="test_name", surname="test_surname",
                                                                 email="test_email", phone="1023456789",
                                                                 birthday="1986-01-01", notes="test_notes",
                                                                 user=self.user)

        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, user=self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.notes, body.notes)

    async def test_delete_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=1, name="test_name", surname="test_surname",
                                                                 email="test_email", phone="1023456789",
                                                                 birthday="1986-01-01", notes="test_notes",
                                                                 user=self.user)
        self.session.execute.return_value = mocked_contact
        result = await delete_contact(1, self.session, user=self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

    async def test_find_contacts(self):
        query = "test"
        contacts = [Contact(id=1, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                            birthday="test_birthday", notes="test_notes", user=self.user),
                    Contact(id=2, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                            birthday="test_birthday", notes="test_notes", user=self.user)]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await find_contacts(query, self.session, user=self.user)
        self.assertEqual(result, contacts)

    async def test_upcoming_birthday(self):
        contacts = [Contact(id=1, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                            birthday="2022-01-01", notes="test_notes", user=self.user),
                    Contact(id=2, name="test_name", surname="test_surname", email="test_email", phone="test_phone",
                            birthday="2022-01-01", notes="test_notes", user=self.user),]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await upcoming_birthday(self.session, user=self.user)
        self.assertEqual(result, contacts)

    # async def tearDown(self) -> None:
    #     await self.session.close()
    #     await self.tearDown()


if __name__ == '__main__':
    unittest.main()
