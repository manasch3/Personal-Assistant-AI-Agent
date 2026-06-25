import os

def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = [
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/youtube'
    ]
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise Exception("credentials.json is missing! Tell the user to download it from Google Cloud Console and put it in the project directory.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

_gmail_service = None
_youtube_service = None

def _get_gmail_service():
    """Lazily authenticates and returns the Gmail API service."""
    global _gmail_service
    if _gmail_service is None:
        from googleapiclient.discovery import build
        _gmail_service = build('gmail', 'v1', credentials=_get_credentials())
    return _gmail_service

def _get_youtube_service():
    """Lazily authenticates and returns the YouTube API service."""
    global _youtube_service
    if _youtube_service is None:
        from googleapiclient.discovery import build
        _youtube_service = build('youtube', 'v3', credentials=_get_credentials())
    return _youtube_service


def search_gmail_messages(query: str, max_results: int = 5):
    """Search for emails matching a query."""
    service = _get_gmail_service()
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    if not messages:
        return "No emails found matching your query."
        
    summary = []
    for msg in messages:
        txt = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From', 'Date']).execute()
        headers = {h['name']: h['value'] for h in txt['payload']['headers']}
        summary.append(f"ID: {msg['id']} | From: {headers.get('From')} | Date: {headers.get('Date')} | Subject: {headers.get('Subject')}")
        
    return "\n".join(summary)


def read_gmail_message(message_id: str):
    """Read the full body of a specific email by ID."""
    service = _get_gmail_service()
    try:
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        subject = headers.get('Subject', 'No Subject')
        sender = headers.get('From', 'Unknown Sender')
        date = headers.get('Date', 'Unknown Date')

        import base64
        body = ""
        
        # Parse payload
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            data = msg['payload']['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        return f"From: {sender}\nDate: {date}\nSubject: {subject}\n\n{body}"
    except Exception as e:
        return f"Error reading email {message_id}: {e}"


def send_gmail_message(to: str, subject: str, body: str):
    """Send an email to a recipient. REQUIRES USER APPROVAL."""
    service = _get_gmail_service()
    
    import base64
    from email.message import EmailMessage

    message = EmailMessage()
    message.set_content(body)
    message['To'] = to
    message['From'] = 'me'
    message['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'raw': encoded_message}

    try:
        sent_message = service.users().messages().send(userId="me", body=create_message).execute()
        return f"Successfully sent email to {to}. Message Id: {sent_message['id']}"
    except Exception as e:
        return f"Failed to send email: {e}"

def get_youtube_subscriptions(max_results: int = 10):
    """Get the latest channels the user has subscribed to."""
    service = _get_youtube_service()
    try:
        request = service.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=max_results,
            order="unread"
        )
        response = request.execute()
        
        subs = []
        for item in response.get('items', []):
            title = item['snippet']['title']
            channel_id = item['snippet']['resourceId']['channelId']
            subs.append(f"- {title} (Channel ID: {channel_id})")
            
        if not subs:
            return "You don't have any YouTube subscriptions."
        return "Your YouTube Subscriptions:\n" + "\n".join(subs)
    except Exception as e:
        return f"Failed to fetch subscriptions: {e}"

def create_youtube_playlist(title: str, description: str = "", privacy_status: str = "private"):
    """Create a new playlist on the user's YouTube account."""
    service = _get_youtube_service()
    try:
        request = service.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
        )
        response = request.execute()
        playlist_id = response['id']
        return f"Successfully created playlist '{title}'! Playlist ID: {playlist_id}\nURL: https://www.youtube.com/playlist?list={playlist_id}"
    except Exception as e:
        return f"Failed to create playlist: {e}"

def add_to_youtube_playlist(playlist_id: str, video_id: str):
    """Add a video to an existing playlist by ID."""
    service = _get_youtube_service()
    try:
        request = service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        response = request.execute()
        return f"Successfully added video to playlist. Item ID: {response['id']}"
    except Exception as e:
        return f"Failed to add video to playlist: {e}"
