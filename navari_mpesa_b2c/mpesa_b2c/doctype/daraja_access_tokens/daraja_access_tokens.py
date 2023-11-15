# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from ..csf_ke_custom_exceptions import InvalidTokenExpiryTimeError
from .. import api_logger


class DarajaAccessTokens(Document):
    """Daraja Access Tokens controller class"""

    def validate(self) -> None:
        """Run validations before saving document"""
        if self.expiry_time and self.expiry_time <= self.token_fetch_time:
            api_logger.error(
                "Access Token Expiry time cannot be same or early than the fetch time"
            )
            raise InvalidTokenExpiryTimeError(
                "Access Token Expiry time cannot be same or early than the fetch time"
            )
