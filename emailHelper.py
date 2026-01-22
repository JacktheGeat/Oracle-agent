from mcp.server.fastmcp import FastMCP

import os
from googleapiclient.errors import HttpError
import base64

from datetime import datetime

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from email.message import EmailMessage

import re
from typing import List


import logging
# logging.basicConfig(filename='emailer.log', level=logging.INFO)
from logger import logger as log


from google.oauth2 import id_token
from google.auth.transport import requests

from dotenv import load_dotenv
load_dotenv()
TOKEN_PATH=os.getenv("TOKEN_PATH")
CREDENTIALS_PATH=os.getenv("CREDENTIALS_PATH")

SCOPES = os.getenv("SCOPES").split(",")

mcp = FastMCP("emailer")

log.debug("Acquiring Email API credentials")
CREDS = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists(TOKEN_PATH):
    CREDS = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not CREDS or not CREDS.valid:
    if CREDS and CREDS.expired and CREDS.refresh_token:
        CREDS.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        CREDS = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKEN_PATH, "w") as token:
        token.write(CREDS.to_json())
SERVICE = build("gmail", "v1", credentials=CREDS)

USEREMAIL = SERVICE.users().getProfile(userId="me").execute()['emailAddress']


def parse_icalendar_to_json(ical_string):
    """
    Convert an iCalendar/VCALENDAR string to a structured JSON format.
    
    Args:
        ical_string (str): Raw iCalendar format string
        
    Returns:
        Dictionary representation of the calendar event
    """
    
    def extract_value(line):
        """Extract the value from a line, handling multi-line values."""
        if ':' not in line:
            return None
        return line.split(':', 1)[1].strip()
    
    def extract_email_and_name(line):
        """Extract email and name from ORGANIZER/ATTENDEE lines."""
        email_match = re.search(r'mailto:([^\s]+)', line)
        name_match = re.search(r'CN=([^:;]+)', line)
        return {
            'email': email_match.group(1) if email_match else None,
            'name': name_match.group(1) if name_match else None
        }
    
    def parse_datetime(dt_string, timezone=None):
        """Parse iCalendar datetime format."""
        # Remove timezone prefix if present
        dt_string = dt_string.strip()
        
        # Try parsing YYYYMMDDTHHMMSS format
        try:
            dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
            return dt.isoformat()
        except ValueError:
            return dt_string
    
    def get_timezone_name(tzid):
        """Convert Windows timezone to IANA format."""
        timezone_map = {
            'Eastern Standard Time': 'America/New_York',
            'Pacific Standard Time': 'America/Los_Angeles',
            'Central Standard Time': 'America/Chicago',
            'Mountain Standard Time': 'America/Denver'
        }
        return timezone_map.get(tzid, tzid)
    
    # Normalize line breaks and continuation
    ical_string = ical_string.replace('\r\n ', '').replace('\r\n', '\n')
    lines = ical_string.split('\n')
    
    event_data = {
        'type': 'calendar_event',
        'method': None,
        'event': {}
    }
    
    current_timezone = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Extract METHOD
        if line.startswith('METHOD:'):
            event_data['method'] = extract_value(line)
        
        # Extract TZID
        elif line.startswith('TZID:'):
            current_timezone = get_timezone_name(extract_value(line))
        
        # Extract ORGANIZER
        elif line.startswith('ORGANIZER'):
            org_info = extract_email_and_name(line)
            event_data['event']['organizer'] = org_info
        
        # Extract ATTENDEE
        elif line.startswith('ATTENDEE'):
            if 'attendees' not in event_data['event']:
                event_data['event']['attendees'] = []
            
            attendee_info = extract_email_and_name(line)
            
            # Extract additional attendee properties
            if 'ROLE=REQ-PARTICIPANT' in line:
                attendee_info['role'] = 'required'
            elif 'ROLE=OPT-PARTICIPANT' in line:
                attendee_info['role'] = 'optional'
            
            if 'PARTSTAT=NEEDS-ACTION' in line:
                attendee_info['status'] = 'needs-action'
            elif 'PARTSTAT=ACCEPTED' in line:
                attendee_info['status'] = 'accepted'
            elif 'PARTSTAT=DECLINED' in line:
                attendee_info['status'] = 'declined'
            
            if 'RSVP=TRUE' in line:
                attendee_info['rsvp'] = True
            
            event_data['event']['attendees'].append(attendee_info)
        
        # Extract SUMMARY
        elif line.startswith('SUMMARY'):
            event_data['event']['summary'] = extract_value(line)
        
        # Extract DESCRIPTION
        elif line.startswith('DESCRIPTION'):
            event_data['event']['description'] = extract_value(line)
        
        # Extract LOCATION
        elif line.startswith('LOCATION'):
            event_data['event']['location'] = extract_value(line)
        
        # Extract DTSTART
        elif line.startswith('DTSTART'):
            dt_value = extract_value(line)
            event_data['event']['start'] = {
                'datetime': parse_datetime(dt_value),
                'timezone': current_timezone
            }
        
        # Extract DTEND
        elif line.startswith('DTEND'):
            dt_value = extract_value(line)
            event_data['event']['end'] = {
                'datetime': parse_datetime(dt_value),
                'timezone': current_timezone
            }
        
        # Extract STATUS
        elif line.startswith('STATUS:'):
            event_data['event']['status'] = extract_value(line).lower()
        
        # Extract busy status
        elif line.startswith('X-MICROSOFT-CDO-BUSYSTATUS:'):
            busy_status = extract_value(line).lower()
            event_data['event']['busy_status'] = busy_status
    
    return event_data

def gmail_send_message(reciever: str, subject: str, body: str):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # If there are no (valid) credentials available, let the user log in.

    try:

        message=EmailMessage() 
        message['From'] = USEREMAIL 
        message['to'] = reciever 
        message['Subject'] = subject
        message.set_content(body) 
        SERVICE = build("gmail", "v1", credentials=CREDS)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            SERVICE.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        # print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message

def get_unread_ids():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail messages.
    """
    
    try:
        # Call the Gmail API
        results = (
            SERVICE.users().messages().list(userId="me", labelIds=["UNREAD", "INBOX"]).execute()
        )
        messages = results.get("messages", [])

        if not messages:
            print("No messages found.")
            return []
        return messages

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

@mcp.tool()
def list_unread():
    """
    Returns:
      List[dict]: A list of dictionary objects containing a summary of all unread emails.
    """
    log.debug("Listing unread emails")
    toReturn = []
    unreadIDs=get_unread_ids()
    if unreadIDs ==None: toReturn = []
    for message in get_unread_ids():
        msg = (
            SERVICE.users().messages().get(userId="me", id=message["id"]).execute()
        )
        headers = msg['payload']['headers']
        sentFrom = next((h['value'] for h in headers if h['name'] == 'From'), None)
        recievedBy = next((h['value'] for h in headers if h['name'].lower() == 'to'), None)
        Date = next((h['value'] for h in headers if h['name'] == 'Date'), None)
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        snippet = msg['snippet']

        attachment = None
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == "text/calendar":
                  fileData = SERVICE.users().messages().attachments().get(
                      userId='me',
                      messageId=message['id'],
                      id=part['body']['attachmentId']
                  ).execute()
                  attachment = base64.urlsafe_b64decode(fileData['data']).decode('utf-8')

                  
        toReturn.append(
            {
                "messageId":msg['id'],
                "threadId":msg['threadId'],
                "sender":sentFrom, 
                "reciever":recievedBy, 
                "date":Date, 
                "subject":subject, 
                "snippet":snippet,
                "calendar_attachment": parse_icalendar_to_json(attachment) if attachment else None
            }
        )
    return toReturn

@mcp.tool()
def draft_reply(messageId: str, threadId: str, body:str, recieverAddr: str, subject: str = None):
    """
    Draft a reply or forwarding email.

    Args:
      messageId (str): The string ID of an email for the reference header.
      threadId (str): The string ID of the thread to attach the previous messages. 
      recieverAddr (str): a string of recipient email addresses separated by a comma e.g. "johndoe@email.com" or "test@example.org, janedoe@test.com"
      subject (str): The subject of the reply.
      body (str): The body of the reply.

    Returns:
      Dict: Containing the draftId and message.

    Raises:
      HttpError: Upon invalid email address.
    """
    log.debug("Drafting reply")
    global SERVICE
    try:
        if subject == None:
            headers = SERVICE.users().messages().get(userId="me", id=messageId).execute()['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        message=EmailMessage() 
        message['From'] = USEREMAIL 
        message['to'] = recieverAddr 
        message['Subject'] = f"RE: {subject}" 
        message['References'] = messageId
        message['In-Reply-To'] = threadId
        message.set_content(body) 
        SERVICE = build("gmail", "v1", credentials=CREDS)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message,
                          "threadId": threadId}}
        # pylint: disable=E1101
        draft = (
            SERVICE.users()
            .drafts()
            .create(userId="me", body=create_message)
            .execute()
        )

    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None

    return draft

@mcp.tool()
def draft_email(reciever: str, subject: str, body: str)-> dict:
    """
    Draft an email message

    Args:
      reciever (str): a string of recipient emails separated by a comma e.g. "johndoe@email.com" or "test@example.org, janedoe@test.com"
      subject (str): The subject of the email.
      body (str): The body of the message.

    Returns:
      Dict: Containing the draftId and message.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # If there are no (valid) credentials available, let the user log in.
    log.debug("Drafting email")
    try:
        message=EmailMessage() 
        message['From'] = USEREMAIL 
        message['to'] = reciever 
        message['Subject'] = subject
        message.set_content(body) 
        SERVICE = build("gmail", "v1", credentials=CREDS)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}
        # pylint: disable=E1101
        draft = (
            SERVICE.users()
            .drafts()
            .create(userId="me", body=create_message)
            .execute()
        )

    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None

    return draft

@mcp.tool()
def send_draft(draftId:str):
    """
    Sends an email draft.

    Args:
      draftId (str): a string id of an already created draft.

    Returns:
      Dict: Containing the draftId and message.
    """
    log.debug("Sending draft")
    try:
        # Send the draft
        message = SERVICE.users().drafts().send(
            userId='me',
            body={'id': draftId}
        ).execute()
        
        print(f"Draft sent! Message ID: {message['id']}")
        return message
        
    except Exception as error:
        print(f"An error occurred: {error}")
        return None

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    # get_unread_ids()

    main()

    # send_email(reciever="jacklynch706@gmail.com", subject="test", body="""
    #                 Testing testing
    #                 123""")
    # gmail_send_message(reciever="jacklynch706@gmail.com", subject="test", body="""
    # #                 Testing testing
    # #                 123""")
    # quickstart()
    # for i in (list_unread()):
    #     print("\n".join([f"{j}: {k}" for j,k in i.items()]))
    #     print("\n\n")

    # print("\n\n".join([str(i) for i in list_unread()]))
    # draft_reply(messageId='19b32919b8c8f6dd', threadId='19b32919b8c8f6dd', body='Test', reciever='pigmanvillagers@gmail.com')

    # print(draft_message(reciever="pigmanvillagers@gmail.com",subject="testing", body="did this work?"))

    # print(draft_email(reciever="test@example.org, janedoe@test.com", subject="test",body="make a draft"))
    # id = "r-221596423401082574"
    # send_draft(id)
