import smtplib
from email.message import EmailMessage
import msal

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
CLIENT_ID = '9e5f94bc-e8a4-4e73-b8be-63364c29d753'  # Thunderbird ID
TENANT_ID = 'harvard.edu'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'

SCOPES = [
    'https://outlook.office365.com/SMTP.Send'
]

USERNAME = 'sgarfinkel@fas.harvard.edu'
# ----------------------------------------------------------------------

def send_mail():
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    # 1. Look for cache first
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # 2. If no cache, use DEVICE CODE FLOW (The "Hack")
    if not result:
        # Initiate the flow
        flow = app.initiate_device_flow(scopes=SCOPES)

        if 'user_code' not in flow:
            print(f"Error: {flow.get('error_description')}")
            return

        # Print the instructions for the user
        print("\n" + "#" * 60)
        print(flow['message']) # e.g. "To sign in, use a web browser to open..."
        print("#" * 60 + "\n")

        # Block and wait for the user to login on the web
        result = app.acquire_token_by_device_flow(flow)

    # 3. Process Result
    if 'access_token' in result:
        access_token = result['access_token']
        print("Authenticated successfully!")

        # Build the weird XOAUTH2 string
        # user=EMAIL^Aauth=Bearer TOKEN^A^A
        auth_string = f"user={USERNAME}\x01auth=Bearer {access_token}\x01\x01"

        print("Connecting to SMTP...")
        try:
            server = smtplib.SMTP("smtp.office365.com", 587)
            server.starttls()
            server.ehlo()
            server.docmd('AUTH XOAUTH2', auth_string.encode('utf-8').decode('latin-1'))
            print("SMTP Login Successful!")

            # Send the email
            msg = EmailMessage()
            msg.set_content("This is the test email via Device Code Flow.")
            msg['Subject'] = "Class Notification Test"
            msg['From'] = USERNAME
            msg['To'] = USERNAME # Test to yourself

            server.send_message(msg)
            server.quit()
            print("Email sent.")

        except Exception as e:
            print(f"SMTP Error: {e}")
    else:
        print("Authentication failed.")
        print(result.get('error'))
        print(result.get('error_description'))

if __name__ == "__main__":
    send_mail()
