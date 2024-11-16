import string

# Configuration constants
MAX_ACCOUNTS = 5
DEFAULT_ACCOUNTS = 1
PASSWORD_LENGTH = 12
MAIL_SERVICE_URL = "https://mails.org"
EXITLAG_REGISTER_URL = "https://www.exitlag.com/register"
EXITLAG_CLIENT_AREA = "https://www.exitlag.com/clientarea.php"

# File paths
ACCOUNTS_TXT = "accounts.txt"
ACCOUNTS_JSON = "accounts.json"

# Selectors
SELECTORS = {
    'first_name': '#inputFirstName',
    'last_name': '#inputLastName',
    'email': '#inputEmail',
    'password1': '#inputNewPassword1',
    'password2': '#inputNewPassword2',
    'checkbox': '.custom-checkbox--input checkbox',
    'recaptcha_btn': '.btn btn-primary btn-block  btn-recaptcha btn-recaptcha-invisible',
    'error_payment': '.alert alert-danger error-payment'
}

# Character sets for password generation
CHARS = {
    'lowercase': string.ascii_lowercase,
    'uppercase': string.ascii_uppercase,
    'digits': string.digits,
    'special': string.punctuation
}
