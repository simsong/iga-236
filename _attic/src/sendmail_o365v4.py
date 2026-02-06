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

# Unique identifier for the keychain item
KEYCHAIN_SERVICE = "harvard_mailer_script"
KEYCHAIN_ACCOUNT = "msal_token_cache"
# ----------------------------------------------------------------------

class KeychainCache(msal.SerializableTokenCache):
    """
    A custom MSAL token cache that persists data to the macOS Keychain.
    """
    def __init__(self):
        super().__init__()
        # This tells MSAL to call these methods when the cache is accessed
        self.on_before_access = self._load_from_keychain
        self.on_after_access = self._save_to_keychain

    def _load_from_keychain(self, context):
        """Called by MSAL before it tries to read the cache."""
        print("[DEBUG] Attempting to load token from Keychain...", end=" ")
        saved_cache = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)

        if saved_cache:
            print("Found!")
            self.deserialize(saved_cache)
        else:
            print("Empty (First run or expired).")

    def _save_to_keychain(self, context):
        """Called by MSAL after the cache has been modified."""
        if self.has_state_changed:
            print("[DEBUG] Token state changed. Saving to Keychain...", end=" ")
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, self.serialize())
            self.has_state_changed = False
            print("Saved.")

def get_token():
    # 1. Initialize our custom cache
    token_cache = KeychainCache()

    # 2. Build the app using that cache
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=token_cache
    )

    # 3. Check for existing accounts in the loaded cache
    #    (This triggers _load_from_keychain automatically)
    accounts = app.get_accounts()

    result = None
    if accounts:
        print(f"[DEBUG] Account found in cache: {accounts[0]['username']}")
        print("[DEBUG] Attempting silent token acquisition...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # 4. If silent auth failed, do interactive login
    if not result:
        print("\n[!] No valid token in cache. Starting interactive login...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        if 'user_code' not in flow:
            print(f"Auth Error: {flow.get('error_description')}")
            return None

        print("\n" + "#" * 60)
        print(flow['message'])
        print("#" * 60 + "\n")

        result = app.acquire_token_by_device_flow(flow)
        keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, app.token_cache.serialize())

    if 'access_token' in result:
        return result['access_token']
    else:
        print(f"Could not acquire token: {result.get('error_description')}")
        return None

def send_mail(token):
    endpoint = f'https://graph.microsoft.com/v1.0/users/{USERNAME}/sendMail'

    email_msg = {
        "message": {
            "subject": "Final Test: Graph API + Keychain Cache",
            "body": {
                "contentType": "Text",
                "content": "This email confirms the token was retrieved properly."
            },
            "toRecipients": [{"emailAddress": {"address": USERNAME}}]
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
    # Sanity check: verify keyring module works on this machine
    try:
        keyring.get_password("test_service", "test_account")
    except Exception as e:
        print(f"CRITICAL ERROR: The 'keyring' library cannot access your OS keychain.")
        print(f"Error detail: {e}")
        sys.exit(1)

    token = get_token()
    if token:
        send_mail(token)
