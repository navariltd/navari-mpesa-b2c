"""Custom Exceptions and Errors raised by modules in the MPesa B2C application"""


class InvalidReceiverMobileNumberError(Exception):
    """Raised when receiver's mobile number fails validation"""


class InsufficientPaymentAmountError(Exception):
    """Raised when the payment amount is less than the required KShs. 10"""


class IncorrectStatusError(Exception):
    """Raised when status is Errored but no errod description or error code has been supplied"""


class InvalidTokenExpiryTimeError(Exception):
    """
    Raised when the access token's expiry time is earlier
    or the same as the access token's fetch time.
    It should always be 1 hour after the fetch time.
    """


class InvalidURLError(Exception):
    """Raised when URLs fail validation"""


class InvalidAuthenticationCertificateFileError(Exception):
    """Raised when an invalid certificate file, i.e. not a .cer or .pem, is uploaded"""


class UnExistentB2CPaymentRecordError(Exception):
    """Raised when referencing a B2C Payment that does not exist"""


class InformationMismatchError(Exception):
    """
    Raised when there's a mismatch in any of the B2C Payment's records
    and the corresponding B2C Payments Transaction's records
    """
