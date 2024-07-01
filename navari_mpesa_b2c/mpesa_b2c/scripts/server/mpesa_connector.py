from datetime import datetime, timedelta
from enum import Enum

import frappe
import requests
import json
from requests.auth import HTTPBasicAuth

from ...utils.definitions import B2CRequestDefinition
from ...utils.doctype_names import DARAJA_ACCESS_TOKENS_DOCTYPE, MPESA_B2C_PAYMENT_DOCTYPE
from ...utils.helpers import save_access_token
from frappe.utils.password import get_decrypted_password
from frappe.utils import get_request_site_address
from frappe.integrations.utils import create_request_log


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
            hashed_token = token[0]

            bearer_token = get_decrypted_password(DARAJA_ACCESS_TOKENS_DOCTYPE, hashed_token, 'access_token')

            saf_url = "{}{}".format(self.base_url,'/mpesa/b2c/v3/paymentrequest')

            callback_url = (get_request_site_address()
                            + "/api/method/navari_mpesa_b2c.mpesa_b2c.scripts.server.mpesa_connector.results_callback_url")

            payload = {
                "OriginatorConversationID": request_data.OriginatorConversationID,
                "InitiatorName": request_data.InitiatorName,
                "SecurityCredential": request_data.SecurityCredential,
                "CommandID": request_data.CommandID,
                "Amount": request_data.Amount,
                "PartyA": request_data.PartyA,
                "PartyB": request_data.PartyB,
                "Remarks": request_data.Remarks,
                "QueueTimeOutURL":"https://example.com",
                "ResultURL": callback_url,
                "Occassion": request_data.Occassion
            }

            payload = json.dumps(payload)
            try:
                response = requests.post(
                    saf_url,
                    data=payload,
                    headers={
                    "Authorization": f"Bearer {bearer_token}",
                    "Content-Type": "application/json",
                    },
                    timeout=60
                )
                
                response.raise_for_status()
                    
            except requests.HTTPError:
                frappe.throw("Exception encountered when sending payment request")

            except requests.ConnectionError:
                frappe.throw("Exception encountered when sending payment request")
    
            except Exception as e:
                frappe.throw("An error occurred")

            frappe.msgprint('Payment Request accepted for processing', title="Successful", indicator="green" )

            response_dict = json.loads(response.text)

            response = frappe._dict(response_dict)

             # Use ConversationID as the request name
            if getattr(response, "ConversationID"):
                req_name = getattr(response, "ConversationID", None)
                error = None
            else:
                # Check error response
                req_name = getattr(response, "requestId")
                error = response

            if not frappe.db.exists("Integration Request", req_name):
                create_request_log(payload, "Host", "Mpesa", req_name, error)
                
            return response
        
@frappe.whitelist(allow_guest=True)
def results_callback_url(**kwargs) -> None:
    frappe.msg_print("Callback received")
    