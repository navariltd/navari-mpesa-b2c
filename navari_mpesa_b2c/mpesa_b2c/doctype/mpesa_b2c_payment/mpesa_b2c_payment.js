// Copyright (c) 2023, Navari Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("MPesa B2C Payment", {
  refresh: function (frm) {
    if (
      frm.doc.docstatus === 1 &&
      (frm.doc.status === "Not Initiated" || frm.doc.status === "Timed-Out")
    ) {
      // Only render the Initiate Payment button if document is saved, and
      // payment status is "Not Initiated" or "Timed-Out"
      frm.add_custom_button(
        "Initiate Payment",
        async function () {
          frappe.call({
            method:
              "navari_mpesa_b2c.mpesa_b2c.doctype.mpesa_b2c_payment.mpesa_b2c_payment.initiate_payment",
            args: {
              // Create request with a partial payload
              partial_payload: {
                name: frm.doc.name,
                OriginatorConversationID: frm.doc.originatorconversationid,
                CommandID: frm.doc.commandid,
                Amount: frm.doc.amount,
                PartyB: frm.doc.partyb,
                Remarks: frm.doc.remarks,
                Occassion: frm.doc.occassion,
              },
            },
            callback: function (response) {
              // Redirect upon response. Response received is success since error responses
              // raise an HTTPError on the server-side
              if (response.message === "No certificate file found in server") {
                frappe.msgprint({
                  title: __("Authentication Error"),
                  indicator: "red",
                  message: __(response.message),
                });
              } else if (response.message === "successful") {
                location.reload();
              } else {
                // TODO: Add proper cases
                frappe.msgprint(`${response}`);
              }
            },
          });
        },
        __("MPesa Actions")
      );
    }

    if (!frm.doc.originatorconversationid) {
      // Set uuidv4 compliant string
      frm.set_value("originatorconversationid", generateUUIDv4());
    }

    // Set filters for party type field
    frm.set_query("party_type", function () {
      return {
        filters: [["DocType", "name", "in", ["Employee", "Supplier"]]],
      };
    });
  },
  commandid: function (frm) {
    frm.set_value("party_type", "");

    // Set appropriate party type according to commandid value
    if (frm.doc.commandid === "SalaryPayment") {
      frm.set_value("party_type", "Employee");
    } else if (frm.doc.commandid === "BusinessPayment") {
      frm.set_value("party_type", "Supplier");
    }
  },
  party_type: function (frm) {
    // Set filters to doctype to pay against field according to party type chosen
    frm.set_query("doctype_to_pay_against", function () {
      const doctypeFieldsList =
        frm.doc.party_type === "Employee"
          ? ["Salary Slip", "Expense Claim", "Employee Advance"]
          : ["Purchase Invoice", "Payment Entry"];

      return {
        filters: [["DocType", "name", "in", doctypeFieldsList]],
      };
    });
  },
  doctype_to_pay_against: function (frm) {
    frm.set_value("items", []);
    const doctype = frm.doc.doctype_to_pay_against;

    console.log(frm.doc.start_date, frm.doc.end_date);

    // Fetch relevant records and set relevant fields in items table
    frappe.db
      .get_list(doctype, {
        fields: ["*"],
        filters: {
          // TODO: Fix problem with date filters not working properly
          creation: [">", frm.doc.start_date],
          creation: ["<=", frm.doc.end_date],
        },
      })
      .then((response) => {
        if (!response.length) {
          throw new Error("No Data Fetched");
        } else {
          response.forEach(async (data) => {
            let recordData = {
              reference_doctype: doctype,
              record: data.name,
              receiver_name: data.employee ?? data.supplier,
              partyb: null,
              record_amount: data.base_rounded_total,
            };

            // Apply fetching contact strategy according to document
            if (doctype === "Salary Slip") {
              const contact = await frappe.db.get_value(
                "Employee",
                { name: data.employee ?? null },
                ["cell_number"]
              );

              if (contact) {
                recordData = {
                  ...recordData,
                  partyb: contact.message?.cell_number,
                };
              }
            } else if (doctype === "Purchase Invoice") {
              const contact = await frappe.db.get_value(
                "Contact",
                { name: ["like", `%${data.supplier}%`] },
                ["*"]
              );

              if (contact) {
                recordData = {
                  ...recordData,
                  partyb: contact.message?.phone ?? contact.message?.mobile_no,
                };
              }
            }

            // Update fields of child table with filtered data
            const row = frm.add_child("items");
            frappe.model.set_value(row.doctype, row.name, recordData);
            cur_frm.refresh_fields("items");
          });
        }
      })
      .catch((error) => {
        if (error.message === "No Data Fetched")
          frappe.msgprint({
            message: __(
              `No records fetched for doctype <b>${doctype}</b> with the <b>date filters specified</b>`
            ),
            indicator: "red",
            title: "Error",
          });
      });
  },
});

function generateUUIDv4() {
  // Generates a uuid4 string conforming to RFC standards
  let uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
    /[xy]/g,
    function (c) {
      let r = (Math.random() * 16) | 0,
        v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    }
  );
  return uuid;
}

function validatePhoneNumber(phoneNumber) {
  // Validates the receiver phone numbers
  if (phoneNumber.startsWith("2547")) {
    const pattern = /^2547\d{8}$/;
    return pattern.test(phoneNumber);
  } else {
    const pattern = /^(25410|25411)\d{7}$/;
    return pattern.test(phoneNumber);
  }
}

function sanitisePhoneNumber(phoneNumber) {
  phoneNumber = phoneNumber.replace("+", "").replace(/\s/g, "");

  const regex = /^0\d{9}$/;
  if (!regex.test(phoneNumber)) {
    return phoneNumber;
  }

  phoneNumber = "254" + phoneNumber.substring(1);
  return phoneNumber;
}
