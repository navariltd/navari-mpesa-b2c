# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt


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

        if self.items:
            # Perform validations for child table records
            for item in self.items:
                item.validate()

    def on_submit(self) -> None:
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
                        OriginatorConversationID=item.originator_conversation_id,
                        InitiatorName=setting.initiator_name,
                        SecurityCredential=setting.security_credential,
                        CommandID=self.commandid,
                        Amount=item.amount,
                        PartyA=setting.business_shortcode,  # TODO: Consider this
                        PartyB=item.partyb,
                        Remarks=self.remarks,
                        Occassion=self.occassion,
                    )
                )
