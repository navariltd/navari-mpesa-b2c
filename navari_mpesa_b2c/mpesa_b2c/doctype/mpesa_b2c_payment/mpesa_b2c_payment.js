// Copyright (c) 2023, Navari Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("MPesa B2C Payment", {
  validate: function (frm) {
    if (frm.doc.partyb) {
      if (!validatePhoneNumber(frm.doc.partyb)) {
        // Validate if the receiver's mobile number is valid
        frappe.msgprint({
          title: __("Validation Error"),
          indicator: "red",
          message: __("The Receiver (mobile number) entered is incorrect."),
        });
        frappe.validated = false;
      }
    }

    if (frm.doc.amount < 10) {
      // Validate amount to be greater then KShs. 10
      frappe.msgprint({
        title: __("Validation Error"),
        indicator: "red",
        message: __(
          "Amount entered is less than the least acceptable amount of Kshs. 10"
        ),
      });
      frappe.validated = false;
    }
  },
  refresh: function (frm) {
    if (
      !frm.doc.__islocal &&
      (frm.doc.status === "Not Initiated" || frm.doc.status === "Timed-Out")
    ) {
      // Only render the Initiate Payment button if document is saved, and
      // payment status is "Not Initiated" or "Timed-Out"
      frm.add_custom_button("Initiate Payment", async function () {
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
      });
    }

    if (!frm.doc.originatorconversationid) {
      // Set uuidv4 compliant string
      frm.set_value("originatorconversationid", generateUUIDv4());
    }

    frm.set_query("party_type", function () {
      return {
        filters: [["DocType", "name", "in", ["Employee", "Supplier"]]],
      };
    });
  },
  party: async function (frm) {
    frm.set_value("party_name", "");
    frm.set_value("partyb", "");

    await fetchAndSetContactDetails(frm);
  },
  party_type: function (frm) {
    frm.set_value("party", "");

    if (frm.doc.party_type === "Supplier") {
      frm.set_value("commandid", "BusinessPayment");
    } else if (frm.doc.party_type === "Employee") {
      frm.set_value("commandid", "SalaryPayment");
    } else {
      frm.set_value("commandid", "");
    }
  },
});

async function fetchAndSetContactDetails(frm) {
  if (frm.doc.party_type === "Supplier") {
    const contactDetails = await frappe.db.get_value(
      "Contact",
      { name: frm.doc.party },
      ["mobile_no", "full_name"]
    );

    frm.set_value("party_name", contactDetails.message?.full_name);
    frm.set_value(
      "partyb",
      sanitisePhoneNumber(contactDetails.message?.mobile_no)
    );
  } else if (frm.doc.party_type === "Employee") {
    const contactDetails = await frappe.db.get_value(
      "Employee",
      { name: frm.doc.party },
      ["cell_number", "employee_name"]
    );
    frm.set_value("party_name", contactDetails.message?.employee_name);
    frm.set_value(
      "partyb",
      sanitisePhoneNumber(contactDetails.message?.cell_number)
    );
  }
}

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
