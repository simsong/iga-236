import requests
import msal
import json

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
# "Microsoft Graph Command Line Tools" Client ID
# This is a standard Microsoft ID usually allowed for scripting.
CLIENT_ID = '14d82eec-204b-4c2f-b7e8-296a70dab67e' 
TENANT_ID = 'harvard.edu'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'

# We need "Mail.Send" permission on the Graph API
SCOPES = ['Mail.Send']

USERNAME = 'sgarfinkel@fas.harvard.edu'
# ----------------------------------------------------------------------

def get_token():
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    
    # Check cache
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # Device Code Flow (if no cache)
    if not result:
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
    
    # Graph API expects a JSON payload, not an SMTP message
    email_msg = {
        "message": {
            "subject": "Final Test via Graph API",
            "body": {
                "contentType": "Text",
                "content": "Hello class, this is sent via the Microsoft Graph API."
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": USERNAME # Send to yourself first!
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
        print("Success! Email accepted by Microsoft Exchange.")
    else:
        print(f"Error sending email: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    token = get_token()
    if token:
        send_mail(token)
