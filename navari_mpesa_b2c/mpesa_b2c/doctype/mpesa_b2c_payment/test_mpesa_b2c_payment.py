# Copyright (c) 2023, Navari Limited and Contributors
# See license.txt


import datetime
import random
import string
from unittest.mock import MagicMock, patch

import frappe
import pymysql
import requests
from frappe.model.document import Document
from frappe.tests.utils import FrappeTestCase

from ..custom_exceptions import (
    IncorrectStatusError,
    InformationMismatchError,
    InsufficientPaymentAmountError,
    InvalidReceiverMobileNumberError,
)
from ..mpesa_b2c_payment import mpesa_b2c_payment
from ..mpesa_b2c_payment.mpesa_b2c_payment import (
    extract_transaction_values,
    get_result_details,
    handle_successful_result_response,
    send_payload,
)

SUCCESSFUL_TEST_RESULTS = {
    "Result": {
        "ResultType": 0,
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "OriginatorConversationID": "1e0ee138-1398-4df9-aeb0-a44c1c9ee0af",
        "ConversationID": "e068d912-f16c-439f-9c31-6304f504d2db",
        "TransactionID": "NOD47HAY4AB",
        "ResultParameters": {
            "ResultParameter": [
                {"Key": "TransactionAmount", "Value": 10},
                {"Key": "TransactionReceipt", "Value": "NOD47HAY4AB"},
                {"Key": "B2CRecipientIsRegisteredCustomer", "Value": "Y"},
                {
                    "Key": "B2CChargesPaidAccountAvailableFunds",
                    "Value": -4510.00,
                },
                {
                    "Key": "ReceiverPartyPublicName",
                    "Value": "254708374149 - John Doe",
                },
                {
                    "Key": "TransactionCompletedDateTime",
                    "Value": "07.11.2023 11:45:50",
                },
                {"Key": "B2CUtilityAccountAvailableFunds", "Value": 10116.00},
                {"Key": "B2CWorkingAccountAvailableFunds", "Value": 900000.00},
            ]
        },
        "ReferenceData": {
            "ReferenceItem": {
                "Key": "QueueTimeoutURL",
                "Value": "https:\/\/internalsandbox.safaricom.co.ke\/mpesa\/b2cresults\/v1\/submit",
            }
        },
    }
}


def create_mpesa_b2c_payment() -> None:
    """Create a valid b2c payment"""
    if frappe.flags.test_events_created:
        return

    frappe.set_user("Administrator")

    frappe.get_doc(
        {
            "doctype": "MPesa B2C Payment",
            "commandid": "BusinessPayment",
            "remarks": "test remarks",
            "status": "Not Initiated",
            "partyb": "254708993268",
            "amount": 10,
            "occassion": "Testing",
            "party_type": "Supplier",
            "account_paid_from": "Cash - NVR",
            "account_paid_to": "Cash - NVR",
        }
    ).insert()

    frappe.flags.test_events_created = True


class TestMPesaB2CPayment(FrappeTestCase):
    """B2C Payment Tests"""

    def setUp(self) -> None:
        create_mpesa_b2c_payment()

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_invalid_receiver_number(self) -> None:
        """Tests invalid receivers"""
        with self.assertRaises(InvalidReceiverMobileNumberError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "2547089932680",
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "25470899326",
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": 254103456789,
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": 254113456789,
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

    def test_empty_mandatory_fields(self) -> None:
        """Tests when a mandatory field is not field"""
        with self.assertRaises(frappe.exceptions.MandatoryError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "status": "Not Initiated",
                    "partyb": "254708993268",
                    "amount": 10,
                    "occassion": "Testing",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "remarks": "testing remarks",
                    "status": "Not Initiated",
                    "partyb": "254708993268",
                    "amount": 10,
                    "occassion": "Testing",
                }
            ).insert()

    def test_insufficient_amount(self) -> None:
        """Tests when an insufficient payment amount has been supplied"""
        with self.assertRaises(InsufficientPaymentAmountError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "254708993268",
                    "amount": 9.99,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

    def test_arbitrarily_large_amount(self) -> None:
        """Tests when an incredibly large number has been supplied"""
        large_number = 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999
        with self.assertRaises(pymysql.err.DataError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "254708993268",
                    "amount": large_number,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

    def test_valid_originator_conversation_id_length(self) -> None:
        """Test that the created b2c settings have valid length uuids"""
        new_mpesa_b2c_payment = frappe.get_doc(
            {
                "doctype": "MPesa B2C Payment",
                "commandid": "BusinessPayment",
                "remarks": "test remarks",
                "status": "Not Initiated",
                "partyb": "254708993268",
                "amount": 10,
                "occassion": "Testing",
                "party_type": "Supplier",
                "account_paid_from": "Cash - NVR",
                "account_paid_to": "Debtors - NVR",
            }
        ).insert()

        self.assertEqual(len(new_mpesa_b2c_payment.originatorconversationid), 36)

    def test_invalid_errored_status_no_code_or_error_description(self) -> None:
        """Tests when status is set to errored without a description or error code"""
        with self.assertRaises(IncorrectStatusError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "status": "Errored",
                    "partyb": "254708993268",
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

    def test_status_set_to_not_initiated_when_not_supplied(self) -> None:
        """
        Tests when status is not given on creation of a record.
        Should be set to 'Not Initiated'
        """
        new_doc = frappe.get_doc(
            {
                "doctype": "MPesa B2C Payment",
                "commandid": "BusinessPayment",
                "remarks": "test remarks",
                "partyb": "254708993268",
                "amount": 10,
                "occassion": "Testing",
                "party_type": "Supplier",
                "account_paid_from": "Cash - NVR",
                "account_paid_to": "Debtors - NVR",
            }
        ).insert()

        self.assertEqual(new_doc.status, "Not Initiated")

    def test_mismatch_in_command_id_and_party_type(self) -> None:
        """Tests for mismatch between the party type and command id fields"""
        with self.assertRaises(InformationMismatchError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "partyb": "254708993268",
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Supplier",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "BusinessPayment",
                    "remarks": "test remarks",
                    "partyb": "254708993268",
                    "amount": 10,
                    "occassion": "Testing",
                    "party_type": "Employee",
                    "account_paid_from": "Cash - NVR",
                    "account_paid_to": "Debtors - NVR",
                }
            ).insert()

    def test_extract_transaction_values(self) -> None:
        """Tests extract_transaction_values() from the mpesa_b2c_payment module"""
        transaction_values = extract_transaction_values(
            SUCCESSFUL_TEST_RESULTS["Result"]["ResultParameters"]["ResultParameter"],
            SUCCESSFUL_TEST_RESULTS["Result"]["TransactionID"],
        )

        self.assertIsInstance(transaction_values, dict)
        self.assertEqual(len(transaction_values), 8)
        self.assertEqual(
            transaction_values["recipient_is_registered_customer"],
            SUCCESSFUL_TEST_RESULTS["Result"]["ResultParameters"]["ResultParameter"][2][
                "Value"
            ],
        )
        self.assertEqual(
            transaction_values["receiver_public_name"],
            SUCCESSFUL_TEST_RESULTS["Result"]["ResultParameters"]["ResultParameter"][4][
                "Value"
            ],
        )
        transaction_completed_datetime = datetime.datetime.strptime(
            transaction_values["transaction_completed_datetime"][:-4],
            "%Y-%m-%d %H:%M:%S",
        ).strftime("%d.%m.%Y %H:%M:%S")
        self.assertEqual(
            transaction_completed_datetime,
            SUCCESSFUL_TEST_RESULTS["Result"]["ResultParameters"]["ResultParameter"][5][
                "Value"
            ],
        )

    def test_get_result_details_function(self) -> None:
        """Tests the get_result_details() function from the mpesa_b2c_payment module"""
        output = get_result_details(SUCCESSFUL_TEST_RESULTS["Result"])

        self.assertIsInstance(output, tuple)
        self.assertEqual(len(output), 5)
        self.assertEqual(
            output[0], SUCCESSFUL_TEST_RESULTS["Result"]["OriginatorConversationID"]
        )
        self.assertEqual(output[4], SUCCESSFUL_TEST_RESULTS["Result"]["TransactionID"])

    @patch.object(mpesa_b2c_payment.requests, "post")
    def test_send_payload(self, mock_response: MagicMock) -> None:
        """Tests the send_payload() function from the b2c_payment module"""
        mock_response.return_value.status_code = 200
        mock_response.return_value.text = {"message": "Success"}

        response, status_code = send_payload(
            "123456789", "secret", "https://example.com/payment"
        )
        self.assertIsInstance(response, dict)
        self.assertEqual(response["message"], "Success")
        self.assertEqual(status_code, 200)

    @patch.object(mpesa_b2c_payment.requests, "post", side_effect=requests.HTTPError)
    def test_send_payload_error_response(self, mock_response: MagicMock) -> None:
        """Tests instances the send_payload() from the b2c_payment module receives an error response"""
        response, status_code = None, None

        with self.assertRaises(requests.HTTPError):
            response, status_code = send_payload(
                "123456789", "secret", "https://example.com/payment"
            )

        self.assertIsNone(response)
        self.assertIsNone(status_code)

    @patch.object(
        mpesa_b2c_payment.requests,
        "post",
        side_effect=requests.exceptions.ConnectionError,
    )
    def test_send_payload_error_connection_failure(
        self, mock_response: MagicMock
    ) -> None:
        """Tests instances the send_payload() from the b2c_payment fails due to a lack of connection"""
        response = None

        with self.assertRaises(requests.exceptions.ConnectionError):
            response = send_payload(
                "123456789", "secret", "https://example.com/payment"
            )

        self.assertIsNone(response)

    def test_handle_successful_result_response(self) -> None:
        """Tests the handle_successful_result_response() function from the mpesa b2c module"""
        payment = frappe.db.get_value(
            "MPesa B2C Payment",
            {"partyb": "254708993268"},
            ["originatorconversationid"],
            as_dict=True,
        )
        SUCCESSFUL_TEST_RESULTS["Result"][
            "OriginatorConversationID"
        ] = payment.originatorconversationid

        mock_transaction_id = f"{''.join([random.choice(string.ascii_letters) for _ in range(10)])}{random.randint(1000000, 100000000)}"
        SUCCESSFUL_TEST_RESULTS["Result"]["TransactionID"] = mock_transaction_id
        SUCCESSFUL_TEST_RESULTS["Result"]["ResultParameters"]["ResultParameter"][1][
            "Value"
        ] = mock_transaction_id

        result = handle_successful_result_response(SUCCESSFUL_TEST_RESULTS["Result"])

        self.assertIsInstance(result, Document)
        self.assertEqual(result.name, mock_transaction_id)
