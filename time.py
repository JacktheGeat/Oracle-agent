from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import requests
from typing import List
import json
from datetime import datetime
from tzlocal import get_localzone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


mcp = FastMCP("time")

@mcp.tool()
def get_current_time_in_time_zone(timezones: List[str]) -> List[str]:
    """
    Retrieves the current date and time for a list of time zones.

    Args:
        time_zone list(str): A list of timezones e.g., ['None', 'America/Chicago','Europe/Paris'].  If None is passed then the system time zone is used.

    Returns:
        A list of JSON strings with information about each time zone, current time and current date,
             or an error message if the city is invalid or time zone cannot be determined.
    """
    result = []
    try:
        for tz_name in timezones:
            try:
                if tz_name.lower() == 'none':
                    tz = get_localzone()
                else:
                    tz = ZoneInfo(tz_name)
                print(tz)
                current_time = datetime.now(tz)
                result.append(json.dumps({'time zone':tz_name, 'current date':current_time.strftime('%B %d, %Y'), 'current time': current_time.strftime('%I:%M %p') }))
            except ZoneInfoNotFoundError:
                result.append(json.dumps({
                        'time zone': tz_name,
                        'err_message': f"{tz_name} is unkown"
                            }))
                continue
    except Exception as e:
        result.append(json.dumps({
            'time zone': 'error',
            'err_message': f"Error fetching data: {e}"
        }))
    return result

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()