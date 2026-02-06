import requests
import msal
import json
import keyring
import sys

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
CLIENT_ID = '14d82eec-204b-4c2f-b7e8-296a70dab67e' # Microsoft Graph Command Line Tools
TENANT_ID = 'harvard.edu'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ['Mail.Send']
USERNAME = 'sgarfinkel@fas.harvard.edu'

# Keychain Identifiers
KEYCHAIN_SERVICE = "harvard_mailer_script"
KEYCHAIN_ACCOUNT = "msal_token_cache"
# ----------------------------------------------------------------------

def create_cache():
    """
    Creates a persistent token cache that saves to the macOS Keychain.
    """
    cache = msal.SerializableTokenCache()

    # 1. Hook: Load from Keychain before accessing the cache
    def _before_access(context):
        print("Checking keyring...")
        saved_cache = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
        if saved_cache:
            context.deserialize(saved_cache)

    # 2. Hook: Save to Keychain after the cache changes
    def _after_access(context):
        print("Checking to save")
        if context.has_state_changed:
            print("Saving")
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, context.serialize())

    # Attach hooks
    cache.on_before_access = _before_access
    cache.on_after_access = _after_access
    return cache

def get_token():
    # Initialize the app with our custom keychain-backed cache
    token_cache = create_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=token_cache
    )

    # 1. Try to get token from Keychain first (Silent)
    accounts = app.get_accounts()
    result = None
    if accounts:
        # We pick the first account found in the cache
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # 2. If no token in Keychain, trigger Device Code Flow
    if not result:
        print("No valid token in Keychain. Initiating login...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        if 'user_code' not in flow:
            print(f"Auth Error: {flow.get('error_description')}")
            return None

        print("\n" + "#" * 60)
        print(flow['message'])
        print("#" * 60 + "\n")

        result = app.acquire_token_by_device_flow(flow)

    if 'access_token' in result:
        return result['access_token']
    else:
        print(f"Could not acquire token: {result.get('error_description')}")
        return None

def send_mail(token):
    endpoint = f'https://graph.microsoft.com/v1.0/users/{USERNAME}/sendMail'

    email_msg = {
        "message": {
            "subject": "Final Test: Graph API + MacOS Keychain",
            "body": {
                "contentType": "Text",
                "content": "This email was sent using a token cached securely in the macOS Keychain."
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": USERNAME # Send to yourself
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }

    print("Sending via Graph API...")
    response = requests.post(
        endpoint,
        headers={
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        },
        data=json.dumps(email_msg)
    )

    if response.status_code == 202:
        print("Success! Email accepted.")
    else:
        print(f"Error sending email: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    token = get_token()
    if token:
        send_mail(token)
