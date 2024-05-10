# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt

import ast
import base64
import datetime
import json
import re
from typing import Literal, Final
from uuid import uuid4

import frappe
import requests
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path
from frappe.utils.password import get_decrypted_password

from .. import app_logger
from .encoding_credentials import openssl_encrypt_encode

from ..custom_exceptions import (
    IncorrectStatusError,
    InsufficientPaymentAmountError,
    InvalidReceiverMobileNumberError,
    InformationMismatchError,
)

MPESA_B2C_SETTINGS_DOCTYPE: Final[str] = "MPesa B2C Settings"
MPESA_B2C_PAYMENT_DOCTYPE: Final[str] = "MPesa B2C Payment"
DARAJA_ACCESS_TOKENS_DOCTYPE: Final[str] = "Daraja Access Tokens"
MPESA_B2C_PAYMENTS_TRANSACTIONS_DOCTYPE: Final[str] = "MPesa B2C Payments Transactions"


class MPesaB2CPayment(Document):
    """MPesa B2C Payment Class"""

    def validate(self) -> None:
        """Validations"""
        self.error = ""

        if not self.originatorconversationid:
            # Generate random UUID4
            self.originatorconversationid = str(uuid4())

        if not self.status:
            self.status = "Not Initiated"

        if self.status == "Errored":
            if not (self.error_description and self.error_code):
                self.error = "Status 'Errored' needs to have a corresponding error_code and error_description for payment: %s"

                app_logger.error(self.error, self.name)
                raise IncorrectStatusError(self.error, self.name)

        if self.party_type == "Employee":
            if self.commandid != "SalaryPayment":
                self.error = "Party Type 'Employee' requires Command ID 'SalaryPayment'"
                app_logger.error(self.error)
                raise InformationMismatchError(self.error)

        if self.party_type == "Supplier":
            if self.commandid != "BusinessPayment":
                self.error = (
                    "Party Type 'Supplier' requires Command ID 'BusinessPayment'"
                )
                app_logger.error(self.error)
                raise InformationMismatchError(self.error)


@frappe.whitelist(methods="POST")
def initiate_payment(partial_payload: str) -> None:
    """
    This endpoint initiates the payment process.
    The endpoint first checks if a valid (meaning un-expired) access token is available.
    If none is found, it fetches one from the authorization url provided in the MPesa B2C Settings and
    proceeds to initiate a payment request to the payment url also specified in the MPesa B2C Settings.
    If a valid token is found, a payment initialization request is placed immediately.
    """
    partial_payload = json.loads(frappe.form_dict.partial_payload)
    b2c_settings = frappe.db.get_singles_dict(MPESA_B2C_SETTINGS_DOCTYPE)

    payment_document = frappe.db.get_value(
        MPESA_B2C_PAYMENT_DOCTYPE,
        {"name": partial_payload.get("name")},
        ["name", "status"],
        as_dict=True,
    )
    hashed_token = get_hashed_token()

    if not hashed_token:
        consumer_key, consumer_secret, authorization_url = get_b2c_settings(
            b2c_settings
        )
        response, status_code = get_access_tokens(
            consumer_key, consumer_secret, authorization_url
        )

        if status_code == requests.codes.ok:
            # If response code is 200, proceed
            bearer_token = save_access_token_to_database(response)
            make_payment(bearer_token, b2c_settings, partial_payload, payment_document)
    else:
        bearer_token = get_decrypted_password(
            DARAJA_ACCESS_TOKENS_DOCTYPE, hashed_token, "access_token"
        )

        make_payment(bearer_token, b2c_settings, partial_payload, payment_document)


@frappe.whitelist(allow_guest=True)
def results_callback_url(Result: dict) -> None:
    """
    Handles results response from Safaricom after successful B2C Payment request.
    For a complete description of the response parameters: https://developer.safaricom.co.ke/APIs/BusinessToCustomer
    """
    results = ast.literal_eval(json.dumps(Result))
    (
        originator_conversation_id,
        result_type,
        result_code,
        results_description,
        transaction_id,
    ) = get_result_details(results)

    if result_type == 0:
        if result_code == 0:
            handle_successful_result_response(results)
        else:
            handle_unsuccessful_result_response(
                transaction_id,
                originator_conversation_id,
                result_code,
                results_description,
            )
    else:
        handle_duplicate_request(originator_conversation_id)


@frappe.whitelist(allow_guest=True)
def queue_timeout_url(response):
    """Handles timeout responses from Safaricom"""
    # TODO: Properly handle timeout responses. Not clearly specified in Safaricom's documentations
    frappe.msgprint(f"{response}")


def get_hashed_token() -> str | list[None]:
    """
    Checks if a valid (read un-expired) token is present in the database,
    fetches and returns it. Otherwise, returns an empty list
    """
    current_time = datetime.datetime.now()
    hashed_token = frappe.db.sql(
        f"""
            SELECT name, access_token
            FROM `tabDaraja Access Tokens`
            WHERE expiry_time > '{current_time.strftime("%Y-%m-%d %H:%M:%S")}'
            ORDER BY creation DESC
            LIMIT 1
        """,
        as_dict=True,
    )

    if hashed_token:
        return hashed_token[0].name

    return []


def get_b2c_settings(b2c_settings: Document) -> tuple[str, str, str]:
    """Gets the consumer key, secret, and authorization url from the MPesa B2C Settings doctype"""
    consumer_key = b2c_settings.get("consumer_key")
    authorization_url = b2c_settings.get("authorization_url")
    consumer_secret = get_decrypted_password(
        MPESA_B2C_SETTINGS_DOCTYPE, MPESA_B2C_SETTINGS_DOCTYPE, "consumer_secret"
    )
    return consumer_key, consumer_secret, authorization_url


def get_access_tokens(
    consumer_key: str, consumer_secret: str, url: str
) -> tuple[str, int]:
    """
    Gets the access token from the authorization url specified in the MPesa B2C Settings doctype.
    """
    keys = f"{consumer_key}:{consumer_secret}"
    encoded_credentials = base64.b64encode(keys.encode()).decode()

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

        response.raise_for_status()  # Raise HTTPError if status code >= 400

    except requests.HTTPError:
        app_logger.exception("Exception Encountered when fetching access token")
        raise

    except requests.exceptions.ConnectionError:
        app_logger.exception("Exception Encountered when fetching access token")
        raise

    except Exception:
        app_logger.exception("Exception Encountered")
        raise

    return response.text, response.status_code


def save_access_token_to_database(response: str) -> str:
    """
    Deserialises the response object and saves the access token to the database,
    returning the access token
    """
    token_fetch_time = datetime.datetime.now()
    response = json.loads(response)

    expiry_time = datetime.datetime.now() + datetime.timedelta(
        seconds=int(response.get("expires_in"))
    )
    access_token = response.get("access_token")

    new_token = frappe.new_doc(DARAJA_ACCESS_TOKENS_DOCTYPE)
    new_token.access_token = access_token
    new_token.expiry_time = expiry_time
    new_token.token_fetch_time = token_fetch_time
    new_token.save()

    app_logger.info(
        "Access token fetched and saved successfully at %s expiring at %s",
        token_fetch_time,
        expiry_time,
    )
    return access_token


def get_certificate_file(certificate_path: str) -> str | Literal[-1]:
    """
    Gets the specified certificate's file path in the server.
    This is the path of the file attached under the Authorisation Certificate File
    in the MPesa B2C Settings field.
    """
    if certificate_path:
        certificate: str | None = get_file_path(certificate_path)

        return certificate

    app_logger.error(
        "No valid Authentication Certificate file (*.cer or *.pem) found in the server."
    )
    return -1


def generate_payload(
    b2c_settings: Document,
    partial_payload: dict[str, str | int],
    security_credentials: str,
) -> str:
    """Generates an MPesa B2C API conforming payload to send in order to initiate payment"""
    partial_payload_from_settings = {
        "PartyA": b2c_settings.organisation_shortcode,
        "InitiatorName": b2c_settings.initiator_name,
        "SecurityCredential": security_credentials,
        "QueueTimeOutURL": b2c_settings.queue_timeout_url,
        "ResultURL": b2c_settings.results_url,
    }

    partial_payload.update(partial_payload_from_settings)

    return json.dumps(partial_payload)


def get_result_details(results: dict) -> tuple[str, str, str | int, str, str | int]:
    """
    Takes the results callback's result object and returns the
    Originator Conversation ID, the Result Type, Result Code,
    Result Description, and Transaction ID respectively
    """
    originator_conversation_id = results.get("OriginatorConversationID")
    result_type = int(results.get("ResultType"))
    result_code = int(results.get("ResultCode"))
    results_description = results.get("ResultDesc")
    transaction_id = results.get("TransactionID")

    return (
        originator_conversation_id,
        result_type,
        result_code,
        results_description,
        transaction_id,
    )


def handle_successful_result_response(results: dict) -> Document:
    """
    Handles the results callback's responses with a successful ResultCode, i.e. ResultCode of 0
    """
    mpesa_b2c_payment_document = frappe.db.get_value(
        MPESA_B2C_PAYMENT_DOCTYPE,
        {"originatorconversationid": results.get("OriginatorConversationID")},
        ["name", "account_paid_from", "account_paid_to"],
        as_dict=True,
    )

    result_parameters = results.get("ResultParameters").get("ResultParameter")
    transaction_values = extract_transaction_values(
        result_parameters, results.get("TransactionID")
    )
    transaction_values.update(
        {
            "b2c_payment_name": mpesa_b2c_payment_document.name,
            "account_paid_from": mpesa_b2c_payment_document.account_paid_from,
            "account_paid_to": mpesa_b2c_payment_document.account_paid_to,
        }
    )

    update_doctype_single_values(
        MPESA_B2C_PAYMENT_DOCTYPE, mpesa_b2c_payment_document, "status", "Paid"
    )

    transaction = save_transaction_to_database(
        MPESA_B2C_PAYMENTS_TRANSACTIONS_DOCTYPE, transaction_values
    )

    frappe.response["transaction"] = transaction
    return transaction


def handle_unsuccessful_result_response(
    transaction_id: str,
    originator_conversation_id: str,
    result_code: int,
    results_description: str,
) -> None:
    """
    Handles the results callback's responses with an unsuccessful ResultCode, i.e. ResultCode != 0
    """
    mpesa_b2c_payment_document = frappe.db.get_value(
        MPESA_B2C_PAYMENT_DOCTYPE,
        {"originatorconversationid": originator_conversation_id},
        ["name"],
        as_dict=True,
    )

    app_logger.info(
        "Transaction %s from B2C Payment %s Errored with code: %s, description: %s",
        transaction_id,
        mpesa_b2c_payment_document.name,
        result_code,
        results_description,
    )
    update_doctype_single_values(
        MPESA_B2C_PAYMENT_DOCTYPE, mpesa_b2c_payment_document, "status", "Errored"
    )
    update_doctype_single_values(
        MPESA_B2C_PAYMENT_DOCTYPE, mpesa_b2c_payment_document, "error_code", result_code
    )
    update_doctype_single_values(
        MPESA_B2C_PAYMENT_DOCTYPE,
        mpesa_b2c_payment_document,
        "error_description",
        results_description,
    )


def handle_duplicate_request(originator_conversation_id: str) -> None:
    """
    Logs instances where multiple requests from same B2C payment record are initiated.
    Normally, only one payment can be initiated from the client.
    """
    mpesa_b2c_payment = frappe.db.get_value(
        MPESA_B2C_PAYMENT_DOCTYPE,
        {"originatorconversationid": originator_conversation_id},
        ["name"],
        as_dict=True,
    )
    frappe.msgprint(
        "Duplicate request encountered!",
        title="Duplicate Request Error",
        indicator="orange",
    )
    app_logger.info(
        "Duplicate Request Encountered for B2C Payment record: %s",
        mpesa_b2c_payment.name,
    )


def extract_transaction_values(
    result_parameters: dict, transaction_id: str
) -> dict[str, str | int]:
    """
    Parses the ResultParameters of successful responses to the results callback endpoint
    and returns the values as a dictionary.
    Fields parsed include: TransactionAmount, TransactionReceipt, B2CRecipientIsRegisteredCustomer,
    B2CChargesPaidAccountAvailableFunds, ReceiverPartyPublicName, TransactionCompletedDateTime,
    B2CUtilityAccountAvailableFunds, B2CWorkingAccountAvailableFunds
    """
    transaction_values = {}

    for item in result_parameters:
        if item["Key"] == "TransactionAmount":
            transaction_values["transaction_amount"] = item["Value"]

        elif item["Key"] == "TransactionReceipt" and item["Value"] == transaction_id:
            transaction_values["transaction_id"] = item["Value"]

        elif item["Key"] == "B2CRecipientIsRegisteredCustomer":
            transaction_values["recipient_is_registered_customer"] = item["Value"]

        elif item["Key"] == "B2CChargesPaidAccountAvailableFunds":
            transaction_values["charges_paid_acct_avlbl_funds"] = item["Value"]

        elif item["Key"] == "ReceiverPartyPublicName":
            transaction_values["receiver_public_name"] = item["Value"]

        elif item["Key"] == "TransactionCompletedDateTime":
            transaction_datetime = datetime.datetime.strptime(
                item["Value"], "%d.%m.%Y %H:%M:%S"
            ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            transaction_values["transaction_completed_datetime"] = transaction_datetime

        elif item["Key"] == "B2CUtilityAccountAvailableFunds":
            transaction_values["utility_acct_avlbl_funds"] = item["Value"]

        elif item["Key"] == "B2CWorkingAccountAvailableFunds":
            transaction_values["working_acct_avlbl_funds"] = item["Value"]

    return transaction_values


def send_payload(payload: str, access_token: str, url: str) -> tuple[str, int]:
    """Sends request to payment processing url with payload"""
    try:
        response = requests.post(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

        response.raise_for_status()  # Raise HTTPError if status code >= 400

    except requests.HTTPError:
        app_logger.exception("Exception Encountered when sending payment request")
        raise

    except requests.exceptions.ConnectionError:
        app_logger.exception("Exception Encountered when sending payment request")
        raise

    except Exception:
        app_logger.exception("Exception Encountered")
        raise

    frappe.msgprint("Payment Request Successful", title="Successful", indicator="green")
    return response.text, response.status_code


def make_payment(
    bearer_token: str,
    b2c_settings: Document,
    partial_payload: dict[str, str | int],
    payment_document: Document,
) -> None:
    """
    Handles making the Payment request.
    This function sends the final response to the client after initiating the payment request.
    """
    initiator_password = get_decrypted_password(
        MPESA_B2C_SETTINGS_DOCTYPE, MPESA_B2C_SETTINGS_DOCTYPE, "initiator_password"
    )
    payment_url = b2c_settings.get("payment_url")
    certificate_relative_path = b2c_settings.get("certificate_file")

    certificate = get_certificate_file(certificate_relative_path)

    if isinstance(certificate, str):
        security_credentials = openssl_encrypt_encode(
            initiator_password.encode(), certificate
        )[8:].decode()

        payload = generate_payload(b2c_settings, partial_payload, security_credentials)

        response, status_code = send_payload(payload, bearer_token, payment_url)

        update_doctype_single_values(
            MPESA_B2C_PAYMENT_DOCTYPE, payment_document, "status", "Pending"
        )

        app_logger.info(
            "Successful payment initiation for B2C Payment record: %s with status code: %s",
            payment_document.name,
            status_code,
        )
        frappe.response["message"] = "successful"
        frappe.response["info"] = {"response": response, "status_code": status_code}

        # This return is important since without it, execution will continue
        # to below and overwrite the "message" key in the response causing
        # the client to enter an incorrect state
        return

    frappe.response["message"] = "No certificate file found in server"
    return


def update_doctype_single_values(
    doctype: str, document_to_update: Document, field: str, new_value: str
) -> None:
    """
    Updates the specified doctype's field with the specified values.
    Note: Only one field is updated at a time
    """
    frappe.db.set_value(
        doctype, document_to_update.name, field, new_value, update_modified=True
    )

    app_logger.info(
        "%s's %s's %s updated to %s",
        doctype,
        document_to_update.name,
        field,
        new_value,
    )


def save_transaction_to_database(
    doctype: str,
    update_values: dict[str, str | int | float],
) -> Document:
    """
    Saves the transaction details to database as an MPesa B2C Payments Transactions record
    after successful B2C Payment and returns the record
    """
    update_values.update({"doctype": doctype})

    transaction = frappe.get_doc(update_values)
    transaction.insert(ignore_permissions=True)

    app_logger.info(
        "Transaction ID: %s, originator conversation id: %s, amount: %s, transaction time: %s saved.",
        update_values["transaction_id"],
        update_values["b2c_payment_name"],
        update_values["transaction_amount"],
        update_values["transaction_completed_datetime"],
    )

    return transaction


def validate_receiver_mobile_number(receiver: str) -> bool:
    """Validates the Receiver's mobile number"""
    receiver = receiver.replace("+", "").strip()
    pattern1 = re.compile(r"^2547\d{8}$")
    pattern2 = re.compile(r"(25410|25411)\d{7}$")

    if receiver.startswith("2547"):
        return bool(pattern1.match(receiver))

    return bool(pattern2.match(receiver))


def sanitise_phone_number(phone_number: str) -> str:
    """Sanitises a given phone_number string"""
    phone_number = phone_number.replace("+", "").replace(" ", "")

    regex = re.compile(r"^0\d{9}$")
    if not regex.match(phone_number):
        return phone_number

    phone_number = "254" + phone_number[1:]
    return phone_number
