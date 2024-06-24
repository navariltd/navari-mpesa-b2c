from datetime import datetime

import frappe

from .doctype_names import DARAJA_ACCESS_TOKENS_DOCTYPE


def save_access_token(
    token: str,
    expiry_time: str | datetime,
    fetch_time: str | datetime,
    associated_setting: str,
    doctype: str = DARAJA_ACCESS_TOKENS_DOCTYPE,
) -> bool:
    doc = frappe.new_doc(doctype)

    doc.associated_settings = associated_setting

    doc.access_token = token
    doc.expiry_time = expiry_time
    doc.token_fetch_time = fetch_time

    try:
        doc.save(ignore_permissions=True)
        doc.submit()

        return True

    except Exception:
        # TODO: Not sure what exception is thrown here. Confirm
        frappe.throw("Error Encountered")
        return False
