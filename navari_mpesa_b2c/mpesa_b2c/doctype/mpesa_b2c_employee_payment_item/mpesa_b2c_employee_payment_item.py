# Copyright (c) 2024, Navari Ltd and contributors
# For license information, please see license.txt
import re
from uuid import uuid4

import frappe
from frappe.model.document import Document


class MPesaB2CEmployeePaymentItem(Document):
    def validate(self) -> None:
        """Validation Hook"""
        if not self.originator_conversation_id:
            self.originator_conversation_id = str(uuid4())

        if self.amount and self.record_amount:
            if self.amount > self.record_amount:
                frappe.throw(
                    "Payment Amount cannot be greater than Record Amount",
                    frappe.ValidationError,
                    title="Validation Error",
                )

        if self.partyb:
            mobile_no = sanitise_phone_number(self.partyb)

            if not validate_receiver_mobile_number(mobile_no):
                frappe.throw(
                    f"Incorrect Receiver's Mobile Number: {self.partyb}",
                    frappe.ValidationError,
                    title="Incorrect Contact",
                )

            self.partyb = mobile_no


def sanitise_phone_number(phone_number: str) -> str:
    """Sanitises a given phone_number string"""
    phone_number = phone_number.replace("+", "").replace(" ", "")

    regex = re.compile(r"^0\d{9}$")
    if not regex.match(phone_number):
        return phone_number

    phone_number = "254" + phone_number[1:]
    return phone_number


def validate_receiver_mobile_number(receiver: str) -> bool:
    """Validates the Receiver's mobile number"""
    receiver = receiver.replace("+", "").strip()
    pattern1 = re.compile(r"^2547\d{8}$")
    pattern2 = re.compile(r"(25410|25411)\d{7}$")

    if receiver.startswith("2547"):
        return bool(pattern1.match(receiver))

    return bool(pattern2.match(receiver))
