import datetime
import os.path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# logging.basicConfig(filename='calendar.log', level=logging.INFO)
from logger import logger as log


# If modifying these scopes, delete the file token.json.
load_dotenv()
SCOPES = os.getenv("SCOPES").split(",")

mcp = FastMCP("calendar")

log.debug("Acquiring Calendar API credentials")
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



def getCalendars():
  log.debug("Listing calendars the user has access to.")
  calendarList = SERVICE.calendarList().list().execute()
  for calendar in calendarList['items']:
    print(calendar["id"], calendar["summary"])

@mcp.tool()
def get_event(eventId: str, calendarId: str='primary'):
  log.debug(f"Retrieving full event information. (eventId={eventId})")
  event = SERVICE.events().get(calendarId=calendarId, eventId=eventId).execute()
  return event

@mcp.tool()
def list_events(startDate: str="",numDays:int=14, maxResults: int = 10):
  """
  Args:
    startDate (str): The date to start checking for free days in MM/DD/YYYY format. Defaults to current date.
    numDays (int): The number of days it will check for. Defaults to 3 weeks from the startDate.
    maxResults (int): The number of results to return, starting from the earliest. Defaults to 10. Use `None` for no limit.

  Returns:
    List[dict]: A list containing the name, start, and end times of the events within the specified duration on the user's calendar.
  """
  log.debug(f"Listing all events. (startDate={startDate}, numDays={numDays})")
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
            maxResults=maxResults,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    print("\n\n".join([f"{i}" for i in events]))
    # if not events:
    #   print("No upcoming events found.")
    #   return 

    # # Prints the start and name of the next 10 events
    # for event in events:
    #   start = event["start"].get("dateTime", event["start"].get("date"))
    #   print(start, event["summary"])
    toReturn = [
      {
        "eventId": event['id'],
        "status": event['status'],
        "summary": event["summary"], 
        "description": None if 'description' not in event else event['description'],
        "creator": event["creator"],
        "organizer": event['organizer'],
        "start": event["start"], 
        "end": event["end"],
        "attendees": None if 'attendees' not in event else event['attendees']
      }
      for event in events
    ]
    return toReturn

  except HttpError as error:
    log.critical(f"An error has occurred: {error}")
    print(f"An error occurred: {error}")

@mcp.tool()
# def create_event(eventObj):
#   """
#   Create a new event
  
#   :type event: dict
#   :param event: The event data in dictionary format
#   examples: 
#     * {"end": {"date": "2026-01-02"},"start": {"date": "2026-01-01"},"summary": "John Doe's birthday"}
#     * {'summary': 'Google I/O 2015','location': '800 Howard St., San Francisco, CA 94103','description': 'A chance to hear more about Google\'s developer products.','start': {'dateTime': '2015-05-28T09:00:00-07:00','timeZone': 'America/Los_Angeles',},'end': {'dateTime': '2015-05-28T17:00:00-07:00','timeZone': 'America/Los_Angeles',},'recurrence': ['RRULE:FREQ=DAILY;COUNT=2'],'attendees': [{'email': 'lpage@example.com'},{'email': 'sbrin@example.com'},],'reminders': {'useDefault': False,'overrides': [{'method': 'email', 'minutes': 24 * 60},{'method': 'popup', 'minutes': 10}]}}
#   """
#   return SERVICE.events().insert(calendarId='primary', body=eventObj).execute()

def create_event(summary: str, start: dict, end: dict, location: str = None, description: str = None, attendees: List[dict] = None):
  """
  Docstring for create_event
  
  :param summary: A short summary of event
  :type summary: str
  :param location: The location of event, can be a physical address, or online link
  :type location: str
  :param description: Detailed description of event
  :type description: str
  :param start: The start time of the event in the format {'dateTime': <ISO formatted dateTime>, 'timeZone': <timeZone>}
  :type start: dict
  :param end: The end time of the event in the format {'dateTime': <ISO formatted dateTime>, 'timeZone': <timeZone>}
  :type end: dict
  :param attendees: A list of attendees, in the format [{'email':'johndoe@email.com'},{'email':'example@test.org'}]
  :type attendees: List[dict]
  """

  event = {
    'summary': summary,
    'location': location,
    'description': description,
    'start': start,
    'end': end,
    'attendees': attendees,
  }
  log.debug(f"Creating an event. (event={event})")
  event = SERVICE.events().insert(calendarId='primary', body=event).execute()
  return event


def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  

  main()

  # print(list_events("12/14/2025"))
  # print(get_event("dbrctm0r9j0ksl2i1om39j2220"))
  # list_events("12/14/2025")