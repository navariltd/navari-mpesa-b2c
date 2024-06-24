from datetime import datetime, timedelta
from enum import Enum

import frappe
import requests
from requests.auth import HTTPBasicAuth

from ...utils.definitions import B2CRequestDefinition
from ...utils.doctype_names import DARAJA_ACCESS_TOKENS_DOCTYPE
from ...utils.helpers import save_access_token


class URLS(Enum):
    """URLS Constant Exporting class"""

    SANDBOX = "https://sandbox.safaricom.co.ke"
    PRODUCTION = "https://api.safaricom.co.ke"


class MpesaB2CConnector:
    def __init__(
        self,
        env: str = "sandbox",
        app_key: bytes | str | None = None,
        app_secret: bytes | str | None = None,
    ):
        """Setup configuration for Mpesa connector and generate new access token."""
        self.authentication_token = None
        self.expires_in = None

        self.env = env
        self.app_key = app_key
        self.app_secret = app_secret

        if env == "sandbox":
            self.base_url = URLS.SANDBOX.value
        else:
            self.base_url = URLS.PRODUCTION.value

    def authenticate(self, setting: str) -> dict[str, str | datetime] | None:
        authenticate_uri = "/oauth/v1/generate?grant_type=client_credentials"
        authenticate_url = f"{self.base_url}{authenticate_uri}"

        r = requests.get(
            authenticate_url,
            auth=HTTPBasicAuth(self.app_key, self.app_secret),
            timeout=120,
        )

        if r.status_code < 400:
            # Success state
            response = r.json()

            self.authentication_token = response["access_token"]
            self.expires_in = datetime.now() + timedelta(
                seconds=int(response["expires_in"])
            )
            fetch_time = datetime.now()

            # Save access token details
            save_access_token(
                token=self.authentication_token,
                expiry_time=self.expires_in,
                fetch_time=fetch_time,
                associated_setting=setting,
            )

            return {
                "access_token": self.authentication_token,
                "expires_in": self.expires_in,
                "fetched_time": fetch_time,
            }

        # Failure State
        frappe.throw(
            f"Can't get token with provided Credentials for setting: <b>{setting}</b>",
            title="Error",
        )

    def make_b2c_payment_request(
        self, request_data: B2CRequestDefinition
    ) -> dict[str, str]:
        # Check if valid Access Token exists
        token = frappe.db.get_value(
            DARAJA_ACCESS_TOKENS_DOCTYPE,
            {
                "associated_settings": request_data.Setting,
                "expiry_time": [">", datetime.now()],
            },
            ["name", "access_token"],
        )

        if not token:
            # If no valid token is present in DB
            self.app_key = request_data.ConsumerKey
            self.app_secret = request_data.ConsumerSecret

            # Fetch and save credentials
            self.authentication_token = self.authenticate(request_data.Setting)[
                "access_token"
            ]

        else:
            pass
