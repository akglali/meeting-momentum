# google_client.py
import os.path
import re
from datetime import datetime # This is the corrected import statement

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/contacts.readonly"
]

def get_credentials():
    """Handles user authentication and returns valid credentials."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def get_briefings():
    """Fetches events and parses them into structured briefing objects."""
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary", timeMin=now, maxResults=10,
        singleEvents=True, orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])

    briefings = []
    if not events:
        return briefings

    for event in events:
        attendee_emails = [a.get('email') for a in event.get('attendees', []) if a.get('email')]
        
        description = event.get('description', '')
        gdrive_links = []
        if description:
            gdrive_links = re.findall(r'https://docs.google.com/[a-zA-Z0-9/_-]+', description)

        start_time_str = event['start'].get('dateTime', event['start'].get('date'))
        start_time_obj = datetime.fromisoformat(start_time_str)

        briefing = {
            "event_id": event['id'],
            "summary": event['summary'],
            "start_time": start_time_obj,
            "attendees": attendee_emails,
            "documents": gdrive_links
        }
        briefings.append(briefing)
        
    return briefings