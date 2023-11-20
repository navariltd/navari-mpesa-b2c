# Copyright (c) 2023, Navari Limited and contributors
# For license information, please see license.txt

import datetime
import frappe
from frappe.model.document import Document

from .. import api_logger
from ..custom_exceptions import (
    InformationMismatchError,
    UnExistentB2CPaymentRecordError,
)


class MPesaB2CPaymentsTransactions(Document):
    """B2C Payments Transactions"""

    def validate(self) -> None:
        """B2C Payments Transactions validations"""

        if self.b2c_payment_name:
            self.fetched_b2c_payment = frappe.db.get_value(
                "MPesa B2C Payment",
                {"name": self.b2c_payment_name},
                [
                    "name",
                    "status",
                    "amount",
                    "account_paid_from",
                    "account_paid_to",
                    "party_type",
                    "party",
                ],
                as_dict=True,
            )

            if not self.fetched_b2c_payment:
                api_logger.error(
                    "The B2C payment record: %s does not exist",
                    self.b2c_payment_name,
                )
                raise UnExistentB2CPaymentRecordError(
                    f"The B2C payment record: {self.b2c_payment_name} does not exist",
                )

            if (
                self.fetched_b2c_payment.status == "Errored"
                or self.fetched_b2c_payment.status == "Not Initiated"
                or self.fetched_b2c_payment.status == "Timed-Out"
                or self.fetched_b2c_payment.status == "Pending"
            ):
                api_logger.error(
                    "Incorrect B2C Payment Status: %s for B2C Payment: %s",
                    self.fetched_b2c_payment.status,
                    self.b2c_payment_name,
                )
                raise InformationMismatchError(
                    f"Incorrect B2C Payment Status: {self.fetched_b2c_payment.status} for B2C Payment: {self.b2c_payment_name}"
                )

            if self.transaction_amount != self.fetched_b2c_payment.amount:
                api_logger.error(
                    "Incorrect Transaction and B2C Payment Amount for B2C payment: %s",
                    self.b2c_payment_name,
                )
                raise InformationMismatchError(
                    f"Incorrect Transaction and B2C Payment Amount for B2C payment: {self.b2c_payment_name}"
                )

    def on_update(self) -> None:
        """Create journal entry after saving successful transaction to the database"""
        if self.fetched_b2c_payment:
            journal_entry = frappe.new_doc("Journal Entry")
            journal_entry.voucher_type = "Journal Entry"
            journal_entry.posting_date = datetime.datetime.now()
            journal_entry.append(
                "accounts",
                {
                    "account": self.account_paid_from,
                    "debit_in_account_currency": self.transaction_amount,
                },
            )
            journal_entry.append(
                "accounts",
                {
                    "account": self.account_paid_to,
                    "credit_in_account_currency": self.transaction_amount,
                    "party_type": self.fetched_b2c_payment.party_type,
                    "party": self.fetched_b2c_payment.party,
                },
            )

            journal_entry.insert(ignore_permissions=True)
            api_logger.info(
                "Journal Entry %s created successfully from B2C Payment: %s and B2C Payments Transaction: %s",
                journal_entry.name,
                self.fetched_b2c_payment.name,
                self.name,
            )
