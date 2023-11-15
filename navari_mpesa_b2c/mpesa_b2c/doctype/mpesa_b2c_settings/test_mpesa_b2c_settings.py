# Copyright (c) 2023, Navari Limited and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from ..mpesa_b2c_payment.mpesa_b2c_payment import get_b2c_settings, get_certificate_file
from ..csf_ke_custom_exceptions import (
    InvalidAuthenticationCertificateFileError,
    InvalidURLError,
)


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
