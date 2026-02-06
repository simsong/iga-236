import smtplib
from email.message import EmailMessage
import msal  # pip install msal

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
# This is the official "Microsoft Azure CLI" Client ID.
# It is a "Public Client" (no secret needed) and usually pre-approved.
CLIENT_ID = '9e5f94bc-e8a4-4e73-b8be-63364c29d753' # thunderbird
TENANT_ID = 'harvard.edu'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'

# We need the "SMTP.Send" scope.
SCOPES = ['https://outlook.office365.com/SMTP.Send']

USERNAME = 'sgarfinkel@fas.harvard.edu'
# ----------------------------------------------------------------------

def send_mail():
    # 1. Authenticate interactively (Magic happens here)
    # This acts like a desktop app. It will pop up a browser window
    # for you to login with your Harvard Key.
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    # Check if we have a cached token first
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # If no cached token, login interactively
    if not result:
        print("Please log in via the browser popup...")
        result = app.acquire_token_interactive(scopes=SCOPES)

    if 'access_token' in result:
        access_token = result['access_token']
        print(f"Authentication successful! Token acquired.")

        # 2. Build the OAuth2 String (The weird format SMTP expects)
        # Format: "user={user}\x01auth=Bearer {token}\x01\x01"
        auth_string = f"user={USERNAME}\x01auth=Bearer {access_token}\x01\x01"

        # 3. Connect to Office 365 SMTP
        print("Connecting to SMTP...")
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.ehlo()

        # 4. Authenticate using the Token
        try:
            server.docmd('AUTH XOAUTH2', auth_string.encode('utf-8').decode('latin-1'))
            print("SMTP Authenticated!")
        except Exception as e:
            print(f"SMTP Auth failed: {e}")
            return

        # 5. Send the email
        msg = EmailMessage()
        msg.set_content("Hello class, this is a test from Python using Modern Auth.")
        msg['Subject'] = "Class Test Email"
        msg['From'] = USERNAME
        msg['To'] = USERNAME # Send to yourself first to test!

        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    else:
        print("Could not acquire token.")
        print(result.get('error'))
        print(result.get('error_description'))

if __name__ == "__main__":
    send_mail()
