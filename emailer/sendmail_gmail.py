import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = 'src/credentials.json'
TOKEN_FILE = 'src/token.json'
SENDER_EMAIL = "sgarfinkel@g.harvard.edu"
# ----------------------------------------------------------------------

def get_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing Access Token...")
            creds.refresh(Request())
        else:
            print("Initiating OAuth2 Flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # This opens a local server to listen for the auth callback
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = EmailMessage()
    message.set_content(message_text)
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject

    # Gmail API requires base64url encoding
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return {
        'raw': encoded_message
    }

def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print(f"Message Id: {message['id']} - Sent successfully.")
        return message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

if __name__ == '__main__':
    # 1. Authenticate
    service = get_service()

    # 2. Construct Message
    # For testing, send to yourself
    msg = create_message(
        sender=SENDER_EMAIL,
        to=SENDER_EMAIL, 
        subject="Cybersecurity Class Notification",
        message_text="Hello class, this is an authenticated message via Gmail API."
    )

    # 3. Send
    send_message(service, "me", msg)
