from mcp.server.fastmcp import FastMCP

import os
from googleapiclient.errors import HttpError
import base64

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import ssl
import smtplib
from email.message import EmailMessage

import re

import logging
logging.basicConfig(filename='sqlQuery.log', level=logging.INFO)

from google.oauth2 import id_token
from google.auth.transport import requests

from dotenv import load_dotenv
load_dotenv()
TOKEN_PATH=os.getenv("TOKEN_PATH")
CREDENTIALS_PATH=os.getenv("CREDENTIALS_PATH")

EMAIL_REGEX = """(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""

mcp = FastMCP("emailer")

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def quickstart():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    if not labels:
      print("No labels found.")
      return
    print("Labels:")
    for label in labels:
      print(label["name"])

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")

@mcp.tool()
def non_api_email(reciever: str, subject: str, body: str, sender: str="jacklynch706@gmail.com"):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  port = 465 
  smtp_server = "smtp.gmail.com"
  password = os.getenv("PASSWD")

  if not re.search(EMAIL_REGEX, reciever):
    return "Invalid destination address!"
  if not re.search(EMAIL_REGEX, sender):
    return "Invalid From address"

  try:

        em=EmailMessage() 
        em['From'] = sender 
        em['to'] = reciever 
        em['Subject'] = subject
        em.set_content(body) 

        context = ssl.create_default_context() 
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server: 
            server.login(sender, password) 
            server.sendmail(sender, reciever, em.as_string()) 
  except HttpError as error:
    print(f"An error occurred: {error}")

# @mcp.tool()
def gmail_send_message(reciever: str, subject: str, body: str, sender: str="jacklynch706@gmail.com"):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds, _ = google.auth.default()

  if not re.search(EMAIL_REGEX, reciever):
    return "Invalid destination address!"
  if not re.search(EMAIL_REGEX, sender):
    return "Invalid From address"

  try:

    em=EmailMessage() 
    em['From'] = sender 
    em['to'] = reciever 
    em['Subject'] = subject
    em.set_content(body) 
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content("This is automated draft mail")

    message["To"] = "gduser1@workspacesamples.dev"
    message["From"] = "gduser2@workspacesamples.dev"
    message["Subject"] = "Automated draft"

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message


def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
    # send_email(reciever="jacklynch706@gmail.com", subject="test", body="""
    #                 Testing testing
    #                 123""")
    # gmail_send_message(reciever="jacklynch706@gmail.com", subject="test", body="""
    # #                 Testing testing
    # #                 123""")
    # quickstart()

