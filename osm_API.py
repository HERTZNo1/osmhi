import http.server
import webbrowser
import requests
import json
from dotenv import load_dotenv
import os
import time
from urllib.parse import urlparse, parse_qs


# OAuth 2.0 Endpoints
AUTHORIZATION_URL = "https://www.openstreetmap.org/oauth2/authorize"
ACCESS_TOKEN_URL = "https://www.openstreetmap.org/oauth2/token"


redirect_uri = "http://127.0.0.1:8080/callback"  
scope = "consume_messages send_messages read_prefs"

API_ENDPOINTS = {
    "user_details": "https://api.openstreetmap.org/api/0.6/user/details",
    "inbox_messages": "https://api.openstreetmap.org/api/0.6/user/messages/inbox.json",
    "message_content": "https://api.openstreetmap.org/api/0.6/user/messages/{message_id}.json",
    "send_message": "https://api.openstreetmap.org/api/0.6/user/messages.json",
}

# Token storage file
TOKEN_FILE = "osm_tokens.json"


def load_env_variables():
    """Load environment variables from the .env file."""
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID or CLIENT_SECRET is not set in the .env file.")
    return client_id, client_secret

def save_tokens(tokens):
    """Save access and refresh tokens to a file."""
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)
    print("Tokens saved.")

def load_tokens():
    """Load tokens from a file."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

def get_new_tokens():
    """Perform OAuth 2.0 authorization flow and retrieve new tokens."""
    client_id, client_secret = load_env_variables()
    # Step 1: Build the authorization URL
    authorization_url = (
        f"{AUTHORIZATION_URL}?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope.replace(' ', '%20')}"
    )

    try:
        print(f"Opening browser for authorization: \n{authorization_url}\n If it is not oppened, please open it manually.\n")
        webbrowser.open(authorization_url)        # Opens the authorization URL
    except Exception as e:
        print(f"An error occurred while opening the browser: {e}")
 

    # Step 2: Start a local HTTP server to capture the authorization code
    class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            if "code" in query:
                self.server.auth_code = query["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authorization successful! You can close this window.")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed. Please try again.")

    httpd = http.server.HTTPServer(("127.0.0.1", 8080), OAuthCallbackHandler)
    httpd.handle_request()

    auth_code = getattr(httpd, "auth_code", None)
    if not auth_code:
        print("Authorization failed. No authorization code received.")
        exit(1)

    # Step 3: Exchange authorization code for tokens
    token_response = requests.post(
        ACCESS_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    if token_response.status_code == 200:
        tokens = token_response.json()
        save_tokens(tokens)
        return tokens
    else:
        print("Failed to retrieve tokens:", token_response.text)
        exit(1)

def refresh_tokens(refresh_token):
    """Refresh the access token using the refresh token."""

    client_id, client_secret = load_env_variables()
    token_response = requests.post(
        ACCESS_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    if token_response.status_code == 200:
        tokens = token_response.json()
        save_tokens(tokens)
        return tokens
    else:
        print("Failed to refresh tokens:", token_response.text)
        exit(1)

def get_access_token():
    """Retrieve a valid access token, refreshing if necessary."""
    tokens = load_tokens()
    if not tokens:
        tokens = get_new_tokens()

    if "access_token" in tokens and "expires_in" in tokens:
        # Check if the token needs to be refreshed
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        if "expires_at" not in tokens or tokens["expires_at"] < time.time():
            tokens = refresh_tokens(refresh_token)
        return tokens["access_token"]
    else:
        return tokens["access_token"]

# Use the access token in API calls
def make_api_call():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Example API call: Fetch user details
    response = requests.get(API_ENDPOINTS["user_details"], headers=headers)

    if response.status_code == 200:
        user_data = response.text  # OpenStreetMap APIs typically return XML
        print("User Data:", user_data)
    else:
        print(f"API call failed. Status code: {response.status_code}")
        print("Response:", response.text)

def fetch_inbox_messages():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(API_ENDPOINTS["inbox_messages"], headers=headers)

    if response.status_code == 200:
        messages = response.json().get("messages", [])
        for message in messages:
            print(f"ID: {message['id']}, From: {message['from_display_name']}, Title: {message['title']}")
        return messages
    else:
        print(f"Failed to fetch inbox messages. Status code: {response.status_code}")
        print("Response:", response.text)
        return None

def fetch_message_content(message_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Format the endpoint with the specific message ID
    url = API_ENDPOINTS["message_content"].format(message_id=message_id)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        message = response.json().get("message", {})
        print(f"Title: {message['title']}")
        print(f"From: {message['from_display_name']}")
        print(f"To: {message['to_display_name']}")
        print(f"Sent on: {message['sent_on']}")
        print(f"Body:\n{message['body']}")
        return message
    else:
        print(f"Failed to fetch message content. Status code: {response.status_code}")
        print("Response:", response.text)
        return None


def send_message_to_user(recipient, title, body, body_format="markdown"):
    """
    Send a message to a specific OpenStreetMap user.

    Args:
        recipient (str): The display name of the recipient (e.g., 'simulator1').
        title (str): The title (subject) of the message.
        body (str): The body of the message.
        body_format (str): Format of the message body ('text', 'markdown', or 'html'). Defaults to 'markdown'.

    Returns:
        dict: Response from the API if successful, None otherwise.
    """
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Payload for the POST request
    payload = {
        "recipient": recipient,
        "title": title,
        "body": body,
        "body_format": body_format
    }

    response = requests.post(API_ENDPOINTS["send_message"], headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Message sent successfully to: {recipient}")
        return response.json()
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print("Response:", response.text)
        return None

# Main execution
if __name__ == "__main__":
    try:
        messages = fetch_inbox_messages()
        if messages:
            # Example: Fetch the content of the first message
            first_message_id = messages[0]['id']
            fetch_message_content(first_message_id)
    except Exception as e:
        print(f"An error occurred: {e}")

    #recipient = "simulator1"
    #title = "Test Message"
    #body = "Hello, this is a test message from the OpenStreetMap API."

    #send_message_to_user(recipient, title, body)

