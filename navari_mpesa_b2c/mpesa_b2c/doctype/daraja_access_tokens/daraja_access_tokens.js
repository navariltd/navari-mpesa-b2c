// Copyright (c) 2023, Navari Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daraja Access Tokens", {
  associated_settings: function (frm) {
    if (frm.doc.associated_settings) {
      frm.add_custom_button(
        __("Get Authentication Credentials"),
        function () {
          frappe.call({
            method: "trigger_authentication",
            args: {
              mpesa_setting: frm.doc.associated_settings,
            },
            callback: (response) => {
              frm.set_value("access_token", response.message.access_token);
              frm.set_value("expiry_time", response.message.expires_in);
              frm.set_value("token_fetch_time", response.message.fetched_time);
            },
            doc: frm.doc,
          });
        },
        __("MPesa Actions")
      );
    }
  },
  validate: function (frm) {
    if (frm.doc.expiry_time && frm.doc.token_fetch_time) {
      expiryTime = new Date(frm.doc.expiry_time);
      fetchTime = new Date(frm.doc.token_fetch_time);

      if (expiryTime <= fetchTime) {
        frappe.msgprint({
          message: __(
            "Token Expiry Time cannot be earlier than or the same as Token Fetch Time"
          ),
          indicator: "red",
          title: "Validation Error",
        });
        frappe.validated = false;
      }
    }
  },
});
