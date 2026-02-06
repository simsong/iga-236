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

DEBUG = False


def get_token():
    # 1. EXPLICIT LOAD: Read string directly from Keychain
    print("[*] Checking Keychain for cached credentials...", end=" ")
    try:
        saved_token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
    except Exception as e:
        print(f"\n[!] Keychain Access Error: {e}")
        saved_token = None

    # 2. HYDRATE CACHE: Inject data into MSAL cache object
    token_cache = msal.SerializableTokenCache()
    if saved_token:
        print("Found.")
        token_cache.deserialize(saved_token)
    else:
        print("Empty.")

    # 3. SETUP APP: Pass the pre-filled cache to the app
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=token_cache
    )

    # 4. SILENT ATTEMPT: Try to use the data we just loaded
    accounts = app.get_accounts()
    result = None
    if accounts:
        print(f"[*] Found account in cache: {accounts[0]['username']}")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # 5. INTERACTIVE FALLBACK: If silent failed, log in manually
    if not result:
        print("[!] No valid token found. Starting interactive login...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        if 'user_code' not in flow:
            print(f"Auth Error: {flow.get('error_description')}")
            return None

        print("\n" + "#" * 60)
        print(flow['message'])
        print("#" * 60 + "\n")

        result = app.acquire_token_by_device_flow(flow)

        # 6. EXPLICIT SAVE: Immediately write success back to Keychain
        if 'access_token' in result:
            print("[*] Login successful. Saving token to Keychain...", end=" ")
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, token_cache.serialize())
            print("Done.")

    if 'access_token' in result:
        return result['access_token']
    else:
        print(f"Could not acquire token: {result.get('error_description')}")
        return None

def send_mail(to,subject,body):
    token = get_token()
    endpoint = f'https://graph.microsoft.com/v1.0/users/{USERNAME}/sendMail'

    email_msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": "<html>\n<pre>\n"+body+"\n</pre>\n</html>\n"
            },
            "toRecipients": [{"emailAddress": {"address": to}}]
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
    send_mail("simsong@acm.org","test subject","test body")
