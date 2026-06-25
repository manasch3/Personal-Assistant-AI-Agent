import os
import math
import requests
import wikipedia

from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
import os

# Configure Wikipedia User-Agent globally
user_email = os.getenv("USER_EMAIL", "bot@example.com")
wikipedia.set_user_agent(f"KiroChatbot/1.0 ({user_email})")

# Suppress BeautifulSoup warnings from the wikipedia package
import warnings
from bs4 import GuessedAtParserWarning
warnings.filterwarnings('ignore', category=GuessedAtParserWarning)

# --------------------------------------------------
# WEB SEARCH TOOL
# --------------------------------------------------
_tavily_search_raw = TavilySearch(max_results=3)

@tool("tavily_search")
def search_tool(query: str) -> str:
    """
    Search the web for current events, news, or general information.
    Input should be a search query string.
    """
    try:
        return str(_tavily_search_raw.invoke(query))
    except Exception as e:
        return f"Error performing web search: {e}"

# --------------------------------------------------
# YOUTUBE SEARCH TOOL
# --------------------------------------------------
@tool
def youtube_search(query: str, sort_by: str = "relevance") -> str:
    """
    Search for YouTube videos.
    - query: The search term (e.g. "Dream minecraft", "Python tutorial")
    - sort_by: How to sort the results. Must be one of: "relevance" (default), "date" (for latest/newest videos), or "views".
    """
    import urllib.parse
    import re
    import json

    query_encoded = urllib.parse.quote(query)
    
    # sp parameters for YouTube search sorting
    sp_map = {
        'date': 'CAI%253D',
        'views': 'CAM%253D',
        'relevance': 'CAA%253D'
    }
    
    sp_val = sp_map.get(sort_by.lower(), 'CAA%253D')
    url = f'https://www.youtube.com/results?search_query={query_encoded}&sp={sp_val}'
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        html = requests.get(url, headers=headers, timeout=10).text
        match = re.search(r'ytInitialData = ({.*?});</script>', html)
        if not match:
            return "Failed to parse YouTube results."
            
        data = json.loads(match.group(1))
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        
        results = []
        for item in contents:
            if 'videoRenderer' in item:
                video = item['videoRenderer']
                title = video['title']['runs'][0]['text']
                vid_id = video['videoId']
                published = video.get('publishedTimeText', {}).get('simpleText', 'Unknown time')
                channel = video.get('ownerText', {}).get('runs', [{}])[0].get('text', 'Unknown channel')
                
                results.append(f"- [{title} by {channel} ({published})](https://www.youtube.com/watch?v={vid_id})")
                
                if len(results) >= 5:
                    break
                    
        if not results:
            return "No videos found for this query."
            
        return f"Top YouTube results for '{query}' (sorted by {sort_by}):\n" + "\n".join(results)
        
    except Exception as e:
        return f"Error searching YouTube: {e}"

# --------------------------------------------------
# WIKIPEDIA TOOL
# --------------------------------------------------
_wiki_tool_raw = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(
        top_k_results=1,
        doc_content_chars_max=3000
    )
)

@tool("wikipedia")
def wiki_tool(query: str) -> str:
    """
    Search Wikipedia for info on people, places, things, history, or concepts.
    Input should be a query string, e.g., "Virat Kohli".
    """
    try:
        # Re-verify user agent is set
        user_email = os.getenv("USER_EMAIL", "bot@example.com")
        wikipedia.set_user_agent(f"KiroChatbot/1.0 ({user_email})")
        return _wiki_tool_raw.run(query)
    except Exception as e:
        return f"Error searching Wikipedia: {e}"

# --------------------------------------------------
# CALCULATOR TOOL
# --------------------------------------------------
@tool
def calculator(expression: str) -> str:
    """
    Perform mathematical calculations.
    Supports basic and advanced math.
    Example: "sqrt(16) + 5 * (2 ** 3)"
    """
    from simpleeval import simple_eval
    
    try:
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        result = simple_eval(expression, functions=allowed_names)
        return str(result)
    except Exception:
        return "Invalid mathematical expression."

# --------------------------------------------------
# WEATHER TOOL
# --------------------------------------------------
@tool
def get_weather(city: str) -> str:
    """
    Get current weather for a city.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather service is not configured."

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    try:
        res = requests.get(url, timeout=10).json()
        if res.get("cod") != 200:
            return f"Could not fetch weather for {city}."

        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        return f"The weather in {city.title()} is {desc} with a temperature of {temp}°C."
    except Exception as e:
        return f"Failed to get weather details: {e}"

# --------------------------------------------------
# SYSTEM STATUS TOOL (5)
# --------------------------------------------------
@tool
def get_system_status() -> str:
    """
    Get the current system status including local date/time, battery level, 
    and available disk space on macOS.
    """
    import subprocess
    import shutil
    from datetime import datetime
    
    # 1. Date and Time
    now = datetime.now()
    time_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
    
    # 2. Disk Space
    total, used, free = shutil.disk_usage("/")
    free_gb = free / (2**30)
    total_gb = total / (2**30)
    disk_str = f"{free_gb:.1f} GB free of {total_gb:.1f} GB"
    
    # 3. Battery
    battery_str = "Unknown"
    try:
        res = subprocess.check_output(["pmset", "-g", "batt"]).decode("utf-8")
        import re
        pct_match = re.search(r"(\d+)%", res)
        state_match = re.search(r"(discharging|charging|charged|finishing charge)", res)
        if pct_match:
            pct = pct_match.group(1)
            state = state_match.group(1) if state_match else "unknown state"
            battery_str = f"{pct}% ({state})"
    except Exception:
        pass
        
    return (
        f"Current System Status:\n"
        f"- Time: {time_str}\n"
        f"- Battery: {battery_str}\n"
        f"- Disk Space: {disk_str}"
    )

# --------------------------------------------------
# OPEN APP OR WEBSITE TOOL (6)
# --------------------------------------------------
@tool
def open_app_or_website(target: str, is_url: bool = False) -> str:
    """
    Open a macOS application by name, or open a website URL in the default browser.
    - target: The name of the application (e.g. 'Spotify', 'Slack', 'Notes') OR a URL (e.g. 'https://google.com')
    - is_url: True if target is a web URL, False if target is an application name.
    """
    import subprocess
    import webbrowser
    
    try:
        if is_url:
            url = target.strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            webbrowser.open(url)
            return f"Opened website: {url}"
        else:
            app_name = target.strip()
            subprocess.run(["open", "-a", app_name], check=True)
            return f"Successfully launched application: {app_name}"
    except subprocess.CalledProcessError:
        return f"Failed to open application '{target}'. Make sure the app name is correct and installed."
    except Exception as e:
        return f"Error opening target: {e}"

# --------------------------------------------------
# FILE FINDER TOOL (4)
# --------------------------------------------------
@tool
def find_local_files(name_query: str, search_dir: str = "~/Documents") -> str:
    """
    Search for files matching name_query in a directory on your computer (e.g., ~/Documents, ~/Downloads, ~/Desktop).
    - name_query: The search term or glob pattern to search for (e.g., '*tax*', 'screenshot*', '*.pdf').
    - search_dir: The directory path to search in. Defaults to '~/Documents'.
    """
    import glob
    import os
    
    expanded_dir = os.path.abspath(os.path.expanduser(search_dir))
    home_dir = os.path.abspath(os.path.expanduser("~"))
    
    # Safety Check: only allow searching within user home folder
    if not expanded_dir.startswith(home_dir):
        return f"Access Denied: Searching is restricted to directories within your home folder ({home_dir})."
        
    if not os.path.exists(expanded_dir):
        return f"Directory does not exist: {search_dir}"
        
    if not os.path.isdir(expanded_dir):
        return f"Path is not a directory: {search_dir}"
        
    try:
        query = name_query.strip()
        if "*" not in query and "?" not in query:
            pattern = f"**/*{query}*"
        else:
            pattern = f"**/{query}"
            
        search_pattern = os.path.join(expanded_dir, pattern)
        matches = glob.glob(search_pattern, recursive=True)
        files = [m for m in matches if os.path.isfile(m)]
        
        if not files:
            return f"No files found matching '{name_query}' in '{search_dir}'."
            
        result_lines = []
        max_results = 20
        for f in files[:max_results]:
            rel_path = os.path.relpath(f, home_dir)
            size_mb = os.path.getsize(f) / (1024 * 1024)
            result_lines.append(f"- ~/{rel_path} ({size_mb:.2f} MB)")
            
        count = len(files)
        summary = f"Found {count} matching file(s) in '{search_dir}':\n" + "\n".join(result_lines)
        if count > max_results:
            summary += f"\n... and {count - max_results} more files."
            
        return summary
    except Exception as e:
        return f"Error searching for files: {e}"

# --------------------------------------------------
# MACOS REMINDERS APP TOOL (1)
# --------------------------------------------------
@tool
def create_reminder(task_name: str, due_time: str = "") -> str:
    """
    Create a new reminder in the native macOS Reminders app, optionally at a future date/time.
    - task_name: The text/title of the reminder (e.g. "Buy milk", "Meeting with team")
    - due_time: Optional natural language date/time string for when the reminder is due.
      Examples: "in 30 seconds", "in 10 minutes", "tomorrow at 9am", "Sunday 10 AM",
                "2026-06-07 15:00", "next Monday 8pm". Leave empty for an immediate reminder.
    """
    import subprocess
    import sys
    from datetime import datetime
    from dateutil import parser as dateutil_parser
    from dateutil.relativedelta import relativedelta

    safe_name = task_name.replace('"', '\\"')
    due_dt = None

    # --- Parse the natural language due_time ---
    if due_time.strip():
        now = datetime.now()
        text = due_time.strip().lower()

        # Handle relative "in X seconds/minutes/hours/days"
        import re
        rel_match = re.match(
            r"in\s+(\d+)\s*(second|minute|hour|day|week)s?", text
        )
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2)
            delta_map = {
                "second": relativedelta(seconds=amount),
                "minute": relativedelta(minutes=amount),
                "hour":   relativedelta(hours=amount),
                "day":    relativedelta(days=amount),
                "week":   relativedelta(weeks=amount),
            }
            due_dt = now + delta_map[unit]
        else:
            # Try dateutil for absolute / natural dates like "Sunday 10 AM"
            try:
                due_dt = dateutil_parser.parse(due_time, default=now, fuzzy=True)
                # If parsed time is in the past (e.g. "Sunday" already passed today),
                # bump it to next week
                if due_dt <= now:
                    due_dt += relativedelta(weeks=1)
            except Exception:
                return f"Could not understand the time '{due_time}'. Try something like 'in 30 seconds', 'tomorrow at 9am', or 'Sunday 10 AM'."

    # --- Build AppleScript ---
    if due_dt:
        # Format for AppleScript: "June 8, 2026 at 10:00:00 AM"
        as_date = due_dt.strftime("%-d %B %Y at %I:%M:%S %p")
        script = (
            f'tell application "Reminders" to make new reminder '
            f'with properties {{name:"{safe_name}", due date:date "{as_date}"}}'
        )
    else:
        script = (
            f'tell application "Reminders" to make new reminder '
            f'with properties {{name:"{safe_name}"}}'
        )

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    except Exception as e:
        return f"Failed to create reminder in Reminders app: {e}"

    if due_dt:
        friendly = due_dt.strftime("%A, %B %-d at %-I:%M %p")
        return f"Reminder created: '{task_name}' — due {friendly}."
    else:
        return f"Reminder created: '{task_name}'."


# --------------------------------------------------
# GMAIL TOOLS (Custom wrapper to avoid startup crash)
# --------------------------------------------------
@tool
def search_emails(query: str, max_results: int = 5) -> str:
    """
    Search your Gmail inbox for emails matching a query.
    - query: e.g. "from:boss@example.com", "subject:Meeting", "last week"
    """
    from google_service import search_gmail_messages
    return search_gmail_messages(query, max_results)

@tool
def read_email(message_id: str) -> str:
    """
    Read the full body of a specific email by ID.
    - message_id: The ID of the email (obtain this from search_emails).
    """
    from google_service import read_gmail_message
    return read_gmail_message(message_id)

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email to a recipient.
    - to: Email address of the recipient.
    - subject: Subject of the email.
    - body: The full body of the email.
    """
    print(f"\n──────────────────────────────────────────")
    print(f"⚠️  Kiro wants to send an email:")
    print(f"To:      {to}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print(f"──────────────────────────────────────────")
    
    ans = input("Approve sending? (y/n): ").strip().lower()
    if ans != 'y':
        print("Cancelled.")
        return "User rejected the email. Do not attempt to send it again."
        
    from google_service import send_gmail_message
    return send_gmail_message(to, subject, body)

# --------------------------------------------------
# YOUTUBE PERSONAL TOOLS (API)
# --------------------------------------------------
@tool
def get_youtube_subscriptions(max_results: int = 10) -> str:
    """Fetch the latest channels the user has subscribed to."""
    from google_service import get_youtube_subscriptions
    return get_youtube_subscriptions(max_results)

@tool
def create_youtube_playlist(title: str, description: str = "", privacy_status: str = "private") -> str:
    """
    Create a new playlist on the user's YouTube account.
    - privacy_status: "private", "public", or "unlisted".
    """
    from google_service import create_youtube_playlist
    return create_youtube_playlist(title, description, privacy_status)

@tool
def add_to_youtube_playlist(playlist_id: str, video_id: str) -> str:
    """
    Add a video to an existing playlist by ID.
    - video_id: The 11-character video ID (e.g. 'dQw4w9WgXcQ' from 'watch?v=dQw4w9WgXcQ')
    """
    from google_service import add_to_youtube_playlist
    return add_to_youtube_playlist(playlist_id, video_id)

# --------------------------------------------------
# MACOS CALENDAR APP TOOLS
# --------------------------------------------------
@tool
def read_calendar_events(date_query: str = "") -> str:
    """
    Read your native macOS Calendar events for a specific date or time frame.
    - date_query: Optional natural language date/time (e.g., "today", "tomorrow", "June 26", "2026-06-25"). If empty, defaults to today.
    """
    import subprocess
    from datetime import datetime
    from dateutil import parser as dateutil_parser
    from dateutil.relativedelta import relativedelta

    now = datetime.now()
    target_dt = now

    if date_query.strip():
        try:
            target_dt = dateutil_parser.parse(date_query, default=now, fuzzy=True)
        except Exception:
            return f"Could not understand the date '{date_query}'. Try 'today', 'tomorrow', or 'YYYY-MM-DD'."

    start_of_day = target_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + relativedelta(days=1)

    as_start = start_of_day.strftime("%-d %B %Y at %I:%M:%S %p")
    as_end = end_of_day.strftime("%-d %B %Y at %I:%M:%S %p")

    script = f'''
    tell application "Calendar"
        set startBoundary to date "{as_start}"
        set endBoundary to date "{as_end}"
        set eventList to ""
        repeat with c in (every calendar)
            try
                set theEvents to (every event of c whose start date >= startBoundary and start date < endBoundary)
                repeat with theEvent in theEvents
                    set sName to summary of theEvent
                    set sStart to start date of theEvent
                    set sEnd to end date of theEvent
                    set eventList to eventList & "- " & sName & " (" & sStart & " to " & sEnd & ")" & linefeed
                end repeat
            end try
        end repeat
        if eventList is "" then
            return "No events found."
        else
            return eventList
        end if
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        out = res.stdout.strip()
        if out == "No events found.":
            return f"No events found on {start_of_day.strftime('%A, %B %-d')}."
        return f"Events on {start_of_day.strftime('%A, %B %-d')}:\n" + out
    except Exception as e:
        return f"Failed to read calendar: {e}"

@tool
def create_calendar_event(summary: str, start_time: str, end_time: str) -> str:
    """
    Create a new event in the macOS Calendar.
    - summary: The name or title of the event.
    - start_time: Natural language start time (e.g., "tomorrow at 2pm", "2026-06-25 14:00").
    - end_time: Natural language end time (e.g., "tomorrow at 3pm").
    """
    import subprocess
    from datetime import datetime
    from dateutil import parser as dateutil_parser

    now = datetime.now()
    
    try:
        start_dt = dateutil_parser.parse(start_time, default=now, fuzzy=True)
        end_dt = dateutil_parser.parse(end_time, default=now, fuzzy=True)
    except Exception:
        return "Could not understand start or end time. Try format like 'tomorrow at 2pm'."

    as_start = start_dt.strftime("%-d %B %Y at %I:%M:%S %p")
    as_end = end_dt.strftime("%-d %B %Y at %I:%M:%S %p")
    safe_summary = summary.replace('"', '\\"')

    script = f'''
    tell application "Calendar"
        try
            set theCal to first calendar whose writable is true
            tell theCal
                make new event with properties {{summary:"{safe_summary}", start date:date "{as_start}", end date:date "{as_end}"}}
            end tell
            return "SUCCESS"
        on error errMsg
            return errMsg
        end try
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        out = res.stdout.strip()
        if out == "SUCCESS":
            return f"Created event '{summary}' from {start_dt.strftime('%b %d, %I:%M %p')} to {end_dt.strftime('%I:%M %p')}."
        else:
            return f"AppleScript error: {out}"
    except Exception as e:
        return f"Failed to create calendar event: {e}"

@tool
def delete_calendar_event(summary: str, date_query: str = "") -> str:
    """
    Delete an event from the macOS Calendar by matching its summary/title.
    - summary: The exact or partial name of the event to delete.
    - date_query: Optional date string to narrow down the search (e.g., "today", "tomorrow"). Highly recommended to avoid deleting the wrong event.
    """
    import subprocess
    from datetime import datetime
    from dateutil import parser as dateutil_parser
    from dateutil.relativedelta import relativedelta

    now = datetime.now()
    target_dt = now

    date_filter = ""
    if date_query.strip():
        try:
            target_dt = dateutil_parser.parse(date_query, default=now, fuzzy=True)
            start_of_day = target_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + relativedelta(days=1)
            
            as_start = start_of_day.strftime("%-d %B %Y at %I:%M:%S %p")
            as_end = end_of_day.strftime("%-d %B %Y at %I:%M:%S %p")
            date_filter = f' and start date >= date "{as_start}" and start date < date "{as_end}"'
        except Exception:
            return f"Could not understand the date '{date_query}'. Try 'today', 'tomorrow'."

    safe_summary = summary.replace('"', '\\"')

    script = f'''
    tell application "Calendar"
        set foundCount to 0
        repeat with c in (every calendar whose writable is true)
            try
                set matchingEvents to (every event of c whose summary contains "{safe_summary}"{date_filter})
                repeat with theEvent in matchingEvents
                    delete theEvent
                    set foundCount to foundCount + 1
                end repeat
            end try
        end repeat
        return foundCount
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        count = int(res.stdout.strip())
        if count == 0:
            return f"No events found matching '{summary}'" + (f" on {target_dt.strftime('%A, %B %-d')}." if date_query.strip() else ".")
        return f"Successfully deleted {count} event(s) matching '{summary}'."
    except Exception as e:
        return f"Failed to delete calendar event: {e}"

# --------------------------------------------------
# MACOS APPLE NOTES APP TOOLS
# --------------------------------------------------
@tool
def read_apple_notes(query: str = "", limit: int = 3) -> str:
    """
    Search your native macOS Apple Notes.
    - query: The text to search for in the note's title or body. If empty, fetches the most recent notes.
    - limit: Maximum number of notes to return (default 3).
    """
    import subprocess
    
    safe_query = query.replace('"', '\\"')
    
    script = f'''
    tell application "Notes"
        set results to ""
        set resultCount to 0
        if "{safe_query}" is "" then
            set theNotes to notes
        else
            set theNotes to (every note whose name contains "{safe_query}" or body contains "{safe_query}")
        end if
        
        repeat with n in theNotes
            if resultCount >= {limit} then exit repeat
            set nName to name of n
            set nBody to plaintext of n
            set results to results & "Title: " & nName & linefeed & "Body: " & nBody & linefeed & "---" & linefeed
            set resultCount to resultCount + 1
        end repeat
        
        if results is "" then
            return "No notes found."
        else
            return results
        end if
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        out = res.stdout.strip()
        return out
    except Exception as e:
        return f"Failed to read Apple Notes: {e}"

@tool
def create_apple_note(name: str, body: str) -> str:
    """
    Create a new note in macOS Apple Notes.
    - name: The title of the note.
    - body: The text body of the note.
    """
    import subprocess
    
    safe_name = name.replace('"', '\\"')
    safe_body = body.replace('"', '\\"').replace('\\n', '<br>')
    
    script = f'''
    tell application "Notes"
        try
            make new note with properties {{name:"{safe_name}", body:"{safe_body}"}}
            return "SUCCESS"
        on error errMsg
            return errMsg
        end try
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        out = res.stdout.strip()
        if out == "SUCCESS":
            return f"Created note '{name}' successfully."
        else:
            return f"AppleScript error: {out}"
    except Exception as e:
        return f"Failed to create Apple Note: {e}"

@tool
def append_apple_note(name: str, text: str) -> str:
    """
    Append text to an existing macOS Apple Note.
    - name: The exact or partial title of the note to modify.
    - text: The text to add to the end of the note.
    """
    import subprocess
    
    safe_name = name.replace('"', '\\"')
    safe_text = text.replace('"', '\\"').replace('\\n', '<br>')
    
    script = f'''
    tell application "Notes"
        try
            set theNotes to (every note whose name contains "{safe_name}")
            if length of theNotes is 0 then
                return "No note found matching '{safe_name}'"
            end if
            
            set targetNote to item 1 of theNotes
            set oldBody to body of targetNote
            set body of targetNote to oldBody & "<br><br>{safe_text}"
            return "SUCCESS"
        on error errMsg
            return errMsg
        end try
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        out = res.stdout.strip()
        if out == "SUCCESS":
            return f"Appended text to note '{name}' successfully."
        else:
            return f"AppleScript error: {out}"
    except Exception as e:
        return f"Failed to append to Apple Note: {e}"

# --------------------------------------------------
# YOUTUBE MUSIC DIRECT PLAY TOOL
# --------------------------------------------------
@tool
def play_youtube_music(query: str) -> str:
    """
    Play a specific song or artist directly on YouTube Music.
    - query: The name of the song or artist.
    """
    import urllib.parse
    import re
    import requests
    import webbrowser
    
    query_encoded = urllib.parse.quote(query)
    url = f'https://www.youtube.com/results?search_query={query_encoded}'
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        html = requests.get(url, headers=headers, timeout=10).text
        match = re.search(r'ytInitialData = ({.*?});</script>', html)
        if not match:
            return "Failed to parse YouTube results for music."
            
        import json
        data = json.loads(match.group(1))
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        
        vid_id = None
        for item in contents:
            if 'videoRenderer' in item:
                vid_id = item['videoRenderer']['videoId']
                title = item['videoRenderer']['title']['runs'][0]['text']
                break
                
        if not vid_id:
            return "No music found for this query."
            
        ytm_url = f"https://music.youtube.com/watch?v={vid_id}&autoplay=1"
        webbrowser.open(ytm_url)
        
        return f"Opened '{title}' on YouTube Music."
        
    except Exception as e:
        return f"Error playing YouTube Music: {e}"

# --------------------------------------------------
# TOOL LIST (EXPORT)
# --------------------------------------------------
tools = [
    youtube_search,
    search_tool,
    wiki_tool,
    calculator,
    get_weather,
    get_system_status,
    open_app_or_website,
    find_local_files,
    create_reminder,
    search_emails,
    read_email,
    send_email,
    get_youtube_subscriptions,
    create_youtube_playlist,
    add_to_youtube_playlist,
    read_calendar_events,
    create_calendar_event,
    delete_calendar_event,
    read_apple_notes,
    create_apple_note,
    append_apple_note,
    play_youtube_music
]