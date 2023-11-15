# Copyright (c) 2023, Navari Limited and Contributors
# See license.txt


import frappe
import pymysql
import datetime
from frappe.tests.utils import FrappeTestCase

from ..csf_ke_custom_exceptions import (
    IncorrectStatusError,
    InsufficientPaymentAmountError,
    InvalidReceiverMobileNumberError,
)
from ..mpesa_b2c_payment.mpesa_b2c_payment import extract_transaction_values

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
                {"Key": "TransactionAmount", "Value": 11},
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
            "commandid": "SalaryPayment",
            "remarks": "test remarks",
            "status": "Not Initiated",
            "partyb": "254708993268",
            "amount": 10,
            "occassion": "Testing",
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
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "2547089932680",
                    "amount": 10,
                    "occassion": "Testing",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "25470899326",
                    "amount": 10,
                    "occassion": "Testing",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": 254103456789,
                    "amount": 10,
                    "occassion": "Testing",
                }
            ).insert()

            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": 254113456789,
                    "amount": 10,
                    "occassion": "Testing",
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
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "254708993268",
                    "amount": 9.9999999,
                    "occassion": "Testing",
                }
            ).insert()

    def test_incredibly_large_amount(self) -> None:
        """Tests when an incredibly large number has been supplied"""
        large_number = 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999
        with self.assertRaises(pymysql.err.DataError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Not Initiated",
                    "partyb": "254708993268",
                    "amount": large_number,
                    "occassion": "Testing",
                }
            ).insert()

    def test_valid_originator_conversation_id_length(self) -> None:
        """Test that the created b2c settings have valid length uuids"""
        new_mpesa_b2c_payment = frappe.get_doc(
            {
                "doctype": "MPesa B2C Payment",
                "commandid": "SalaryPayment",
                "remarks": "test remarks",
                "status": "Not Initiated",
                "partyb": "254708993268",
                "amount": 10,
                "occassion": "Testing",
            }
        ).insert()

        self.assertEqual(len(new_mpesa_b2c_payment.originatorconversationid), 36)

    def test_invalid_errored_status_no_code_or_error_description(self) -> None:
        """Tests when status is set to errored without a description or error code"""
        with self.assertRaises(IncorrectStatusError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Payment",
                    "commandid": "SalaryPayment",
                    "remarks": "test remarks",
                    "status": "Errored",
                    "partyb": "254708993268",
                    "amount": 10,
                    "occassion": "Testing",
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
                "commandid": "SalaryPayment",
                "remarks": "test remarks",
                "partyb": "254708993268",
                "amount": 10,
                "occassion": "Testing",
            }
        ).insert()

        self.assertEqual(new_doc.status, "Not Initiated")

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
