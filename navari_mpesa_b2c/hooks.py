app_name = "navari_mpesa_b2c"
app_title = "Navari Mpesa Disbursements Integration"
app_publisher = "Navari Ltd"
app_description = "Mpesa Business to Customer (B2C) Disbursements Integration with ERPNext by Navari Ltd"
app_email = "solutions@navari.co.ke"
app_license = "GNU Affero General Public License v3.0"
required_apps = ["frappe/erpnext/hrms/payments"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/navari_mpesa_b2c/css/navari_mpesa_b2c.css"
# app_include_js = "/assets/navari_mpesa_b2c/js/navari_mpesa_b2c.js"

# include js, css files in header of web template
# web_include_css = "/assets/navari_mpesa_b2c/css/navari_mpesa_b2c.css"
# web_include_js = "/assets/navari_mpesa_b2c/js/navari_mpesa_b2c.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "navari_mpesa_b2c/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "navari_mpesa_b2c/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "navari_mpesa_b2c.utils.jinja_methods",
#	"filters": "navari_mpesa_b2c.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "navari_mpesa_b2c.install.before_install"
# after_install = "navari_mpesa_b2c.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "navari_mpesa_b2c.uninstall.before_uninstall"
# after_uninstall = "navari_mpesa_b2c.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "navari_mpesa_b2c.utils.before_app_install"
# after_app_install = "navari_mpesa_b2c.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "navari_mpesa_b2c.utils.before_app_uninstall"
# after_app_uninstall = "navari_mpesa_b2c.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "navari_mpesa_b2c.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"navari_mpesa_b2c.tasks.all"
#	],
#	"daily": [
#		"navari_mpesa_b2c.tasks.daily"
#	],
#	"hourly": [
#		"navari_mpesa_b2c.tasks.hourly"
#	],
#	"weekly": [
#		"navari_mpesa_b2c.tasks.weekly"
#	],
#	"monthly": [
#		"navari_mpesa_b2c.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "navari_mpesa_b2c.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "navari_mpesa_b2c.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "navari_mpesa_b2c.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["navari_mpesa_b2c.utils.before_request"]
# after_request = ["navari_mpesa_b2c.utils.after_request"]

# Job Events
# ----------
# before_job = ["navari_mpesa_b2c.utils.before_job"]
# after_job = ["navari_mpesa_b2c.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"navari_mpesa_b2c.auth.validate"
# ]
