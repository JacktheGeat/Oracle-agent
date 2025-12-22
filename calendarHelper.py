import datetime
import os.path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
load_dotenv()
SCOPES = os.getenv("SCOPES").split(",")

mcp = FastMCP("calendar")

CREDS = None
SERVICE = None


def getCalendars():
  calendarList = SERVICE.calendarList().list().execute()
  for calendar in calendarList['items']:
    print(calendar["id"], calendar["summary"])


@mcp.tool()
def get_events(startDate: str="",numDays:int=14):
  """
  Args:
    startDate (str): The date to start checking for free days in MM/DD/YYYY format. Defaults to current date.
    numDays (int): The number of days it will check for. Defaults to 14 days.
    maxResults (int): The number of results to return, starting from the earliest. Defaults to 10.

  Returna:
   A list containing the name, start, and end times of the events within the specified duration on the user's calendar.
  """

  try:

    # Call the Calendar API
    dateStart = datetime.datetime.now(tz=datetime.timezone.utc) if startDate == "" else datetime.datetime.strptime(startDate, "%m/%d/%Y").astimezone(tz=datetime.timezone.utc)
    dateEnd = datetime.timedelta(weeks=3)+dateStart
    events_result = (
        SERVICE.events()
        .list(
            calendarId="primary",
            timeMin=dateStart.isoformat(),
            timeMax=dateEnd.isoformat(),
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    # if not events:
    #   print("No upcoming events found.")
    #   return 

    # # Prints the start and name of the next 10 events
    # for event in events:
    #   start = event["start"].get("dateTime", event["start"].get("date"))
    #   print(start, event["summary"])
    toReturn = [{"summary": event["summary"], "start": event["start"].get("dateTime", event["start"].get("date")), "end": event["end"].get("dateTime", event["end"].get("date"))} for event in events]
    return toReturn

  except HttpError as error:
    print(f"An error occurred: {error}")

def create_event():
  pass

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    CREDS = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not CREDS or not CREDS.valid:
    if CREDS and CREDS.expired and CREDS.refresh_token:
      CREDS.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      CREDS = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(CREDS.to_json())    
  SERVICE = build("calendar", "v3", credentials=CREDS)
    # Initialize and run the server
  if CREDS == None or SERVICE == None: print( "ERROR: No Credentials or Service!")

  main()

  # print(get_upcoming_events("12/14/2025"))