# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt

import re

from frappe.model.document import Document

from ..custom_exceptions import InvalidURLError

from .. import app_logger
from ..custom_exceptions import (
    InvalidAuthenticationCertificateFileError,
)


class MPesaB2CSettings(Document):
    """MPesa B2C Settings Doctype"""

    def validate(self) -> None:
        """Validate upon creating a record of the B2C Settings"""
        self.errors = ""

        if (
            self.results_url
            and self.queue_timeout_url
            and self.authorization_url
            and self.payment_url
        ):
            if not (
                validate_url(self.results_url)
                and validate_url(self.queue_timeout_url)
                and validate_url(self.authorization_url)
                and validate_url(self.payment_url)
            ):
                self.errors = "The URLs Registered are not valid. Please review them"
                app_logger.error(self.errors)
                raise InvalidURLError(self.errors)

        if self.certificate_file:
            if not (
                self.certificate_file.endswith(".cer")
                or self.certificate_file.endswith(".pem")
            ):
                self.errors = "Invalid Authentication Certificate file uploaded"
                app_logger.error(self.errors)
                raise InvalidAuthenticationCertificateFileError(self.errors)


def validate_url(url: str) -> bool:
    """
    Validates the input parameter to a valid URL.
    """
    pattern = re.compile(
        r"^((https?|ftp|file):\/\/)?"
        + r"((([a-zA-Z\d]([a-zA-Z\d-]*[a-zA-Z\d])*)\.)+[a-zA-Z]{2,}|"
        + r"((\d{1,3}\.){3}\d{1,3}))"
        + r"(:\d+)?(\/[-a-zA-Z\d%_.~+]*)*"
        + r"(\?[;&a-z\d%_.~+=-]*)?"
        + r"(\#[-a-z\d_]*)?$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))
