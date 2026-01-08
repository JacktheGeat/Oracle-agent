import cohere
import json

import weather, emailHelper, calendarHelper, time

import logging
logging.basicConfig(filename='agent.log', level=logging.DEBUG)
from logger import logger as log


import os
from dotenv import load_dotenv
load_dotenv()
 
class Agent():
    CO_API_KEY = os.getenv("CO_API_KEY")
    client = cohere.ClientV2(api_key=CO_API_KEY)

    def __init__(self, loopTimes: int = 10):
        log.debug("starting Agent")
        self.loopTimes = 10

    def create_tool_response_message(self, tool_call, result):
        tool_content = []
        # Optional: the "document" object can take an "id" field for use in citations, otherwise auto-generated
        tool_content.append(
                    {
                    "type": "document",
                    "document": {"data": json.dumps(result)},
                    }
                )
        return {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                }

    def call(self, prompt: str, model: str = "command-a-03-2025"):
    
        messages = [
            {
                "role": "system", 
                "content": """You are a helpful assistant.
                When you find a meeting or appointment in an unread email, check the calendar to see if there is a conflict.
                If there is no conflict, you should add it to the calendar. You do not need permission.
                If there is a conflict, draft an email reply explaining that the user is already busy. You do not need permission."""
            },
            {"role": "user", "content": prompt}  # Add user message to existing list
        ]
        tools = get_available_tools()

        numIterations = 0
        while numIterations <self.loopTimes:
            response = self.client.chat(
                model=model,
                messages=messages,
                tools=tools,
            )
            print(f"Finish reason: {response.finish_reason}")

            msg = response.message
    
            if msg.content:
                log.debug("Message Content found")

                for content in msg.content:
                    print(content.text)
    
            if msg.tool_calls:
                log.debug("Tool call made")

                for tool_call in msg.tool_calls:
                    # print(f"tool_name:{tool_call.function.name} tool_function:{tool_call.function.arguments}")
                    result = handle_tool_call(tool_call)

                    messages.append(msg)
                    messages.append(self.create_tool_response_message(tool_call, result))
            else:
                print ("No content retuned")
                message = input()
                if message == "": return
                messages.append({"role": "user", "content": message})

            numIterations += 1

            


 
 
# you need to implement:
# get_available_tools()  Here is an example so you need the schema of the tools.  You need to define yours
 
def get_available_tools():
    """Cohere-specific tool format"""
    return [
        {
            "type": "function",
            "function": {
                "name": "list_unread",
                "description": "List unread emails. Use this tool to retrieve all unread emails from the user's inbox.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "draft_reply",
                "description": "Drafts a reply email. Can also be used to draft forwarding messages.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "messageId": {"type": "string", "description": "ID of the message being responded to"},
                        "threadId": {"type": "string", "description":"ID of the thread being responded to"},
                        "body": {"type": "string", "description": "body of the response"},
                        "recieverAddr": {"type": "string", "description": "The email address of the draft's recipient."},
                        "subject": {"type": "string", "description":"The subject of the draft."}
                    },
                    "required": ["messageId", "threadId", "recieverAddr", "body"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_calendar",
                "description": "Checks the user's calendar for events. Use this to find conflicts before scheduling meetings. startDate MUST be in MM/DD/YYYY format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "startDate": {"type": "string", "description": "The date to start checking for events in 'MM/DD/YYYY' format. Defaults to current date."},
                        "numDays": {"type": "integer", "description":"The number of days to check. Defaults to 21 days (3 weeks) from the startDate"},
                        "maxResults": {"type": "integer", "description": "The number of results to return, starting from the earliest. Defaults to 10."},
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_calendar_event",
                "description": "Create a new calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "A short summary of event"},
                        "location": {"type": "string", "description": "The location of event, can be a physical address, or online link"},
                        "description": {"type": "string", "description": "Detailed description of event"},
                        "start": {"type": "object", "description": "The start time of the event in the format {'dateTime': <ISO formatted dateTime>, 'timeZone': <timeZone>}"},
                        "end": {"type": "object", "description": "The end time of the event in the format {'dateTime': <ISO formatted dateTime>, 'timeZone': <timeZone>}"},
                        "attendees": {"type": "array", "description": "A list of attendees, in the format [{'email':'johndoe@email.com'},{'email':'example@test.org'}]"},
                    },
                    "required": ["summary", "start", "end"]
                }
            }
        }
    ]
 
 
def handle_tool_call(tool_call):
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    print(arguments)
    tools_map = {
        "list_unread": emailHelper.list_unread,
        "draft_reply": emailHelper.draft_reply,
        "check_calendar": calendarHelper.list_events,
        "create_calendar_event": calendarHelper.create_event
    }
 
    return tools_map[function_name](**arguments)


if __name__ == "__main__":
    # my_agent("can you look through my unread emails, and if one is inviting me to a meeting, draft a reply that I will make time for it")
    email_calendar_agent = Agent(10)
    email_calendar_agent.call("Can you use a tool call to list my unread emails")