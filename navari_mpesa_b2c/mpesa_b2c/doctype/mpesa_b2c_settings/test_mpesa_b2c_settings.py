# Copyright (c) 2023, Navari Limited and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from ..mpesa_b2c_payment.mpesa_b2c_payment import (
    get_b2c_settings,
    get_certificate_file,
    generate_payload,
)
from ..csf_ke_custom_exceptions import (
    InvalidAuthenticationCertificateFileError,
    InvalidURLError,
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


def create_b2c_settings():
    """Setup context for tests"""
    if frappe.flags.test_events_created:
        return

    frappe.set_user("Administrator")

    # Create a valid singles record during setUp context
    frappe.get_doc(
        {
            "doctype": "MPesa B2C Settings",
            "consumer_key": "1234567890",
            "initiator_name": "tester",
            "results_url": "https://example.com/api/method/handler",
            "authorization_url": "https://example.com/api/method/handler",
            "organisation_shortcode": "951753",
            "consumer_secret": "secret",
            "initiator_password": "password",
            "queue_timeout_url": "https://example.com/api/method/handler",
            "payment_url": "https://example.com/api/method/handler",
        }
    ).insert(ignore_mandatory=True)

    frappe.flags.test_events_created = True


class TestMPesaB2CSettings(FrappeTestCase):
    """MPesa B2C Settings Tests"""

    def setUp(self) -> None:
        create_b2c_settings()

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_invalid_urls_in_b2c_settings(self) -> None:
        """Tests for cases when an invalid url is supplied"""
        with self.assertRaises(InvalidURLError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Settings",
                    "consumer_key": "1234567890",
                    "initiator_name": "tester",
                    "results_url": "https://example.com/api/method/handler",
                    "authorization_url": "https://example.com/api/method/handler",
                    "organisation_shortcode": "951753",
                    "consumer_secret": "secret",
                    "initiator_password": "password",
                    "queue_timeout_url": "https://example.com/api/method/handler",
                    "payment_url": "jkl",
                }
            ).insert(ignore_mandatory=True)

    def test_override_b2c_settings(self) -> None:
        """Test instances where the B2C Settings have been overridden"""
        frappe.get_doc(
            {
                "doctype": "MPesa B2C Settings",
                "consumer_key": "987654321",
                "initiator_name": "tester2",
                "results_url": "https://example2.com/api/method/handler",
                "authorization_url": "https://example2.com/api/method/handler",
                "organisation_shortcode": "951753",
                "consumer_secret": "secret",
                "initiator_password": "password",
                "queue_timeout_url": "https://example2.com/api/method/handler",
                "payment_url": "https://example2.com/api/method/handler",
            }
        ).insert(ignore_mandatory=True)

        new_doc = frappe.db.get_singles_dict("MPesa B2C Settings")

        self.assertEqual(new_doc.initiator_name, "tester2")
        self.assertEqual(new_doc.payment_url, "https://example2.com/api/method/handler")
        self.assertEqual(new_doc.consumer_key, "987654321")

    def test_invalid_certificate_file(self) -> None:
        """Tests when a user uploads an invalid certificate file"""
        with self.assertRaises(InvalidAuthenticationCertificateFileError):
            frappe.get_doc(
                {
                    "doctype": "MPesa B2C Settings",
                    "consumer_key": "987654321",
                    "initiator_name": "tester2",
                    "results_url": "https://example2.com/api/method/handler",
                    "authorization_url": "https://example2.com/api/method/handler",
                    "organisation_shortcode": "951753",
                    "consumer_secret": "secret",
                    "initiator_password": "password",
                    "queue_timeout_url": "https://example2.com/api/method/handler",
                    "payment_url": "https://example2.com/api/method/handler",
                    "certificate_file": "/files/AuthorizationCertificate",
                }
            ).insert()

    def test_get_b2c_settings_function(self) -> None:
        """Tests the get_b2c_settings() function from the b2c payment module"""
        b2c_settings = frappe.db.get_singles_dict("MPesa B2C Settings")
        consumer_key, consumer_secret, authorization_url = get_b2c_settings(
            b2c_settings
        )

        self.assertEqual(consumer_key, "1234567890")
        self.assertEqual(authorization_url, "https://example.com/api/method/handler")
        self.assertEqual(consumer_secret, "secret")

    def test_get_certificate_file_function(self) -> None:
        """Tests the get_certificate_file() function from the b2c payment module"""
        certificate_file_path = "/files/AuthorizationCertificate.cer"
        frappe.get_doc(
            {
                "doctype": "MPesa B2C Settings",
                "consumer_key": "1234567890",
                "initiator_name": "tester",
                "results_url": "https://example.com/api/method/handler",
                "authorization_url": "https://example.com/api/method/handler",
                "organisation_shortcode": "951753",
                "consumer_secret": "secret",
                "initiator_password": "password",
                "queue_timeout_url": "https://example.com/api/method/handler",
                "payment_url": "https://example.com/api/method/handler",
                "certificate_file": certificate_file_path,
            }
        ).insert()

        certificate = get_certificate_file(certificate_file_path)

        self.assertTrue(certificate, certificate.endswith(certificate_file_path))

    def test_generate_payload(self) -> None:
        """Tests generate_payload() function in mpesa_b2c_payment module"""
        originator_conversation_id = "b4a300e2-e250-44b5-a41b-70fa4d3c3a69"
        partial_payload = {
            "name": "MPESA-B2C-999999999999999999",
            "OriginatorConversationID": originator_conversation_id,
            "CommandID": "SalaryPayment",
            "Amount": 10,
            "PartyB": "254712345678",
            "Remarks": "testing remarks",
            "Occassion": "testing",
        }
        security_credentials = "abcdefghijklmnop"
        b2c_settings = frappe.db.get_singles_dict("MPesa B2C Settings")

        payload = generate_payload(b2c_settings, partial_payload, security_credentials)

        self.assertIsInstance(payload, str)
        self.assertTrue('"name": "MPESA-B2C-999999999999999999"' in payload)
        self.assertTrue(
            '"OriginatorConversationID": "b4a300e2-e250-44b5-a41b-70fa4d3c3a69"'
            in payload
        )
        self.assertTrue('"PartyB": "254712345678"' in payload)
        self.assertTrue(
            '"ResultURL": "https://example.com/api/method/handler"' in payload
        )
        self.assertTrue(
            '"QueueTimeOutURL": "https://example.com/api/method/handler"' in payload
        )
        self.assertTrue('"InitiatorName": "tester"' in payload)
