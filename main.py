import suds
from suds.client import Client
import time
from datetime import datetime
import pytz
import os
import win32com.client

# Configuration
mantis_base_url = 'http://localhost:8086/mantisbt'
username = 'administrator'
password = 'root'

# Timezone configuration
IST = pytz.timezone('Asia/Kolkata')

# SOAP WSDL URL
wsdl_url = f"{mantis_base_url}/api/soap/mantisconnect.php?wsdl"

# Dictionary to keep track of the last note date for each issue
last_note_dates = {}

# MSMQ configuration
queue_path = ".\\Private$\\myqueue"

# Function to fetch ticket updates
def fetch_ticket_updates():
    try:
        client = Client(wsdl_url)
        issues = client.service.mc_project_get_issues(username, password, 0, 1, 50)  # Project ID 0 (all projects), page 1, per page 50
        return issues
    except suds.WebFault as e:
        print(f"Error: Failed to fetch ticket updates: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Function to fetch detailed issue information
def fetch_issue_details(issue_id):
    try:
        client = Client(wsdl_url)
        issue = client.service.mc_issue_get(username, password, issue_id)
        return issue
    except Exception as e:
        print(f"Error: failed to fetch issue details for issue #{issue_id}: {e}")
        return None

def to_timezone_aware(dt, tzinfo):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzinfo)
    return dt.astimezone(tzinfo)

# Function to send a message to MSMQ
def send_to_msmq(message):
    msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
    msmq_info.FormatName = f"DIRECT=OS:{queue_path}"
    queue = msmq_info.Open(2, 0)  # Open the queue with send access
    msg = win32com.client.Dispatch("MSMQ.MSMQMessage")
    msg.Body = message
    msg.Label = "New Work Note"
    msg.Send(queue)
    queue.Close()

# Function to check for updates and write notes to text files
def check_for_updates(initial_run, script_start_time):
    issues = fetch_ticket_updates()
    if issues:
        current_time = datetime.now(pytz.UTC).astimezone(IST)  # Ensure current time is timezone-aware in IST
        for issue in issues:
            last_updated = issue.last_updated
            if isinstance(last_updated, str):
                last_updated = datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S%z')  # Adjust format if necessary
            last_updated = to_timezone_aware(last_updated, IST)  # Ensure last_updated is timezone-aware in IST

            print(f"Ticket #{issue.id} last modified: {last_updated}")
            print(f"Current time: {current_time}")
            print(f"Description: {issue.description}")

            # Fetch and print text notes
            detailed_issue = fetch_issue_details(issue.id)
            if detailed_issue and hasattr(detailed_issue, 'notes'):
                notes_filename = f"ticket_{issue.id}_notes.txt"
                temp_notes_filename = "temp_notes.txt"
                new_notes = []
                last_saved_date = last_note_dates.get(issue.id, script_start_time)  # Use script start time on the initial run
                for note in detailed_issue.notes:
                    note_date_submitted = note.date_submitted
                    if isinstance(note_date_submitted, str):
                        note_date_submitted = datetime.strptime(note_date_submitted, '%Y-%m-%dT%H:%M:%S%z')  # Adjust format if necessary
                    note_date_submitted = to_timezone_aware(note_date_submitted, IST)

                    if note_date_submitted > last_saved_date:
                        reporter_email=getattr(note.reporter,'email','N/A')
                        note_text = f"- {note.reporter.name} ({reporter_email}) ({note_date_submitted}): {note.text}\n"
                        new_notes.append(note_text)
                        last_note_dates[issue.id] = note_date_submitted

                if new_notes:
                    # Read existing content of the file
                    existing_content = ""
                    if os.path.exists(notes_filename):
                        with open(notes_filename, 'r', encoding='utf-8') as notes_file:
                            existing_content = notes_file.read()

                    # Prepend new notes to existing content
                    with open(notes_filename, 'w', encoding='utf-8') as notes_file:  # Open file in write mode
                        for note_text in reversed(new_notes):  # Reverse to maintain order from top to bottom
                            print(note_text.strip())
                            notes_file.write(note_text)
                        notes_file.write(existing_content)

                    # Write new notes to the temporary file
                    with open(temp_notes_filename, 'w', encoding='utf-8') as temp_notes_file:  # Open file in write mode
                        for note_text in reversed(new_notes):  # Reverse to maintain order from top to bottom
                            temp_notes_file.write(note_text)

                    if not initial_run:
                        # Send new notes to MSMQ only after the initial run
                        for note_text in new_notes:
                            send_to_msmq(note_text)

            print()  # Blank line for readability

# Main loop
initial_run = True
script_start_time = datetime.now(pytz.UTC).astimezone(IST)  # Record script start time
while True:
    # Delete temporary file if exists
    temp_notes_filename = "temp_notes.txt"
    if os.path.exists(temp_notes_filename):
        os.remove(temp_notes_filename)

    check_for_updates(initial_run, script_start_time)
    initial_run = False  # Set to False after the first run

    # Wait for some time before checking again (e.g., every minute)
    time.sleep(180)
