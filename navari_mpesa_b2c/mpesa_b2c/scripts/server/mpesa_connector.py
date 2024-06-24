from datetime import datetime, timedelta

import requests
from requests.auth import HTTPBasicAuth
from enum import Enum


class URLS(Enum):
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

    def authenticate(self) -> dict[str, str | datetime]:
        authenticate_uri = "/oauth/v1/generate?grant_type=client_credentials"
        authenticate_url = f"{self.base_url}{authenticate_uri}"

        response = requests.get(
            authenticate_url,
            auth=HTTPBasicAuth(self.app_key, self.app_secret),
            timeout=120,
        ).json()

        return {
            "access_token": response["access_token"],
            "expires_in": datetime.now()
            + timedelta(seconds=int(response["expires_in"])),
            "fetched_time": datetime.now(),
        }
