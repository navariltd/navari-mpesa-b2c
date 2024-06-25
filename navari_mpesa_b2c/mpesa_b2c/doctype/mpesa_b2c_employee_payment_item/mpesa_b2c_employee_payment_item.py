# Copyright (c) 2024, Navari Ltd and contributors
# For license information, please see license.txt

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
