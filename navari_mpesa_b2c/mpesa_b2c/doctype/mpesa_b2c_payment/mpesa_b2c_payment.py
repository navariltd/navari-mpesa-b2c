# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt

import re
from uuid import uuid4

import frappe
from frappe.model.document import Document

from ...scripts.server.mpesa_connector import MpesaB2CConnector
from ...utils.definitions import B2CRequestDefinition
from .. import app_logger
from ..custom_exceptions import InformationMismatchError


class MPesaB2CPayment(Document):
    """MPesa B2C Payment Class"""

    def validate(self) -> None:
        """Validations"""
        self.error = ""

        if not self.originatorconversationid:
            # Generate random UUID4
            self.originatorconversationid = str(uuid4())

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

    def on_submit(self) -> bool:
        setting: Document = frappe.get_doc(
            "Mpesa Settings",
            {"payment_gateway_name": self.mpesa_setting, "api_type": "Disbursement"},
            [
                "name",
                "initiator_name",
                "security_credential",
                "business_shortcode",
                "consumer_key",
                "consumer_secret",
            ],
            as_dict=True,
        )

        if setting:
            connector = MpesaB2CConnector()

            for item in self.items:
                connector.make_b2c_payment_request(
                    B2CRequestDefinition(
                        Setting=setting.name,
                        ConsumerKey=setting.consumer_key,
                        ConsumerSecret=setting.get_password("consumer_secret"),
                        OriginatorConversationID=self.originatorconversationid,  # Refactor this out of this doctype
                        InitiatorName=setting.initiator_name,
                        SecurityCredential=setting.security_credential,
                        CommandID=self.commandid,
                        Amount=item.amount,
                        PartyA=setting.business_shortcode,  # Consider this
                        PartyB=item.partyb,
                        Remarks=self.remarks,
                        Occassion=self.occassion,
                    )
                )


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
