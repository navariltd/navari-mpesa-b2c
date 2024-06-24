# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document

from ...scripts.server.mpesa_connector import MpesaB2CConnector
from .. import app_logger
from ..custom_exceptions import InvalidTokenExpiryTimeError


class DarajaAccessTokens(Document):
    """Daraja Access Tokens controller class"""

    def validate(self) -> None:
        """Run validations before saving document"""
        if self.expiry_time and self.expiry_time <= self.token_fetch_time:
            self.error = (
                "Access Token Expiry time cannot be same or early than the fetch time"
            )
            app_logger.error(self.error)
            raise InvalidTokenExpiryTimeError(self.error)

    @frappe.whitelist()
    def trigger_authentication(self, *args, **kwargs) -> dict[str, str | datetime]:
        mpesa_setting: Document = frappe.get_doc(
            "Mpesa Settings", {"name": args[0]["mpesa_setting"]}, ["*"], as_dict=True
        )

        auth_response = MpesaB2CConnector(
            app_key=mpesa_setting.consumer_key,
            app_secret=mpesa_setting.get_password("consumer_secret"),
        ).authenticate(setting=mpesa_setting.name)

        return auth_response
