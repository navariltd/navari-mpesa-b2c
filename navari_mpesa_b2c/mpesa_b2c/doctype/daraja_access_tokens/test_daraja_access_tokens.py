# Copyright (c) 2023, Navari Limited and Contributors
# See license.txt

import datetime
import json
from unittest.mock import MagicMock, patch

import frappe
import requests
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import get_decrypted_password

from ..custom_exceptions import InvalidTokenExpiryTimeError
from ..mpesa_b2c_payment import mpesa_b2c_payment
from ..mpesa_b2c_payment.mpesa_b2c_payment import (
    get_access_tokens,
    get_hashed_token,
    save_access_token_to_database,
)

TOKEN_ACCESS_TIME = datetime.datetime.now()


def create_access_token() -> None:
    """Creates a valid access token record for testing"""
    if frappe.flags.test_events_created:
        return

    frappe.set_user("Administrator")

    expiry_time = TOKEN_ACCESS_TIME + datetime.timedelta(hours=1)
    frappe.get_doc(
        {
            "doctype": "Daraja Access Tokens",
            "access_token": "123456789",
            "token_fetch_time": TOKEN_ACCESS_TIME,
            "expiry_time": expiry_time,
        }
    ).insert()

    frappe.flags.test_events_created = True


class TestDarajaAccessTokens(FrappeTestCase):
    """Testing the Daraja Access Tokens doctype"""

    def setUp(self) -> None:
        create_access_token()

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_valid_access_token(self) -> None:
        """Attempt to access an existing token"""
        token = frappe.db.get_value(
            "Daraja Access Tokens",
            {"token_fetch_time": TOKEN_ACCESS_TIME},
            ["name", "token_fetch_time", "expiry_time"],
            as_dict=True,
        )
        access_token = get_decrypted_password(
            "Daraja Access Tokens", token.name, "access_token"
        )

        self.assertEqual(access_token, "123456789")
        self.assertEqual(token.token_fetch_time, TOKEN_ACCESS_TIME)
        self.assertEqual(
            token.expiry_time, TOKEN_ACCESS_TIME + datetime.timedelta(hours=1)
        )

    def test_create_incomplete_access_token(self) -> None:
        """Attemp to create a record from incomplete data"""
        with self.assertRaises(frappe.exceptions.MandatoryError):
            frappe.get_doc(
                {
                    "doctype": "Daraja Access Tokens",
                    "access_token": "123456789",
                    "token_fetch_time": TOKEN_ACCESS_TIME,
                }
            ).insert()

    def test_incorrect_datetime_type(self) -> None:
        """Test passing strings to datetime fields"""
        with self.assertRaises(TypeError):
            frappe.get_doc(
                {
                    "doctype": "Daraja Access Tokens",
                    "access_token": TOKEN_ACCESS_TIME + datetime.timedelta(hours=1),
                    "token_fetch_time": TOKEN_ACCESS_TIME,
                    "expiry_time": "123456789",
                }
            ).insert()

    def test_expiry_time_earlier_than_fetch_time(self) -> None:
        """Test expiry time being early than fetch time"""
        with self.assertRaises(InvalidTokenExpiryTimeError):
            frappe.get_doc(
                {
                    "doctype": "Daraja Access Tokens",
                    "access_token": "123456789",
                    "token_fetch_time": TOKEN_ACCESS_TIME,
                    "expiry_time": TOKEN_ACCESS_TIME - datetime.timedelta(hours=1),
                }
            ).insert()

    def test_get_hashed_token(self) -> None:
        """Tests the get_hashed_token() function from the b2c_payment module"""
        hashed_token = get_hashed_token()
        token = frappe.db.get_value(
            "Daraja Access Tokens",
            {"token_fetch_time": TOKEN_ACCESS_TIME},
            ["name"],
        )

        self.assertEqual(hashed_token, token)

    @patch.object(mpesa_b2c_payment.requests, "get")
    def test_get_access_tokens(self, mock_response: MagicMock) -> None:
        """Tests the get_access_tokens() function from the b2c_payment module"""
        mock_response.return_value.status_code = 200
        mock_response.return_value.text = {
            "access_token": "987654321",
            "expires_in": "3599",
        }

        token, status_code = mpesa_b2c_payment.get_access_tokens(
            "123456789", "secret", "https://example.com/authorise"
        )
        self.assertIsInstance(token, dict)
        self.assertEqual(token["access_token"], "987654321")
        self.assertEqual(token["expires_in"], "3599")
        self.assertEqual(status_code, 200)

    @patch.object(mpesa_b2c_payment.requests, "get", side_effect=requests.HTTPError)
    def test_get_access_tokens_error_response(self, mock_request: MagicMock) -> None:
        """
        Tests instances the get_access_tokens() function from the b2c_payment receives an error response
        """
        response = None

        with self.assertRaises(requests.HTTPError):
            response = get_access_tokens(
                "123456789", "secret", "https://example.com/authorise"
            )

        self.assertIsNone(response)

    @patch.object(
        mpesa_b2c_payment.requests,
        "get",
        side_effect=requests.exceptions.ConnectionError,
    )
    def test_get_access_tokens_connection_error(self, mock_request: MagicMock) -> None:
        """
        Tests instances the get_access_tokens() function from the mpesa_b2c_payment fails to connect
        """
        response = None

        with self.assertRaises(requests.exceptions.ConnectionError):
            response = get_access_tokens(
                "123456789", "secret", "https://256.256.256.256/welcome"
            )

        self.assertIsNone(response)

    def test_save_access_token_to_database(self) -> None:
        """Tests saving access token to database"""
        response = json.dumps(
            {
                "access_token": "987abc321xyz",
                "expires_in": "600",
            }
        )
        saved_token = save_access_token_to_database(response)

        hashed_token = frappe.db.sql(
            """
            SELECT name
            FROM `tabDaraja Access Tokens`
            ORDER BY creation DESC
            LIMIT 1
            """,
            as_dict=True,
        )
        token = get_decrypted_password(
            "Daraja Access Tokens", hashed_token[0].name, "access_token"
        )

        self.assertEqual(saved_token, "987abc321xyz")
        self.assertEqual(token, "987abc321xyz")
