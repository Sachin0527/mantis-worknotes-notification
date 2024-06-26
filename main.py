import time
import os

from datetime import datetime
import pytz

from mantis_client import MantisBTApiClient
from msmq_client import MSMQSender
from update_checker import check_for_updates, fetch_issue_details
from timezone_helper import to_timezone_aware
from attachment import fetch_attachments  # Import fetch_attachments from attachment.py

# Dictionary to keep track of the last note date for each issue
last_note_dates = {}

# MSMQ configuration
queue_path = ".\\Private$\\myqueue"

# Timezone configuration
IST = pytz.timezone('Asia/Kolkata')

# Function to delete temporary file if exists
def delete_temp_file():
    temp_notes_filename = "temp_notes.txt"
    if os.path.exists(temp_notes_filename):
        os.remove(temp_notes_filename)


# Function to check for updates and write notes to text files
def process_updates(initial_run, script_start_time, mantis_client, msmq_client):
    issues = check_for_updates(mantis_client)
    if issues:
        current_time = datetime.now(pytz.UTC).astimezone(IST)  # Ensure current time is timezone-aware in IST
        for issue in issues:
            last_updated = issue['updated_at']
            last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            last_updated = to_timezone_aware(last_updated, IST)  # Ensure last_updated is timezone-aware in IST

            print(f"Ticket #{issue['id']} last modified: {last_updated}")
            print(f"Current time: {current_time}")
            print(f"Description: {issue['description']}")

            detailed_issue = fetch_issue_details(mantis_client, issue['id'])
            if detailed_issue:
                process_notes(issue, detailed_issue, initial_run, script_start_time, msmq_client)


def process_notes(issue, detailed_issue, initial_run, script_start_time, msmq_client):
    notes_filename = f"ticket_{issue['id']}_notes.txt"
    temp_notes_filename = "temp_notes.txt"
    new_notes = []
    last_saved_date = last_note_dates.get(issue['id'], script_start_time)  # Use script start time on the initial run
    for note in detailed_issue['notes']:
        note_date_submitted = note['created_at']
        note_date_submitted = datetime.fromisoformat(note_date_submitted.replace('Z', '+00:00'))
        note_date_submitted = to_timezone_aware(note_date_submitted, IST)

        if note_date_submitted > last_saved_date:
            reporter_email = note['reporter'].get('email', 'N/A')

            new_notes.append({
                'text': note['text'],
                'reporter': note['reporter']['name'],
                'reporter_email': reporter_email,
                'date_submitted': note_date_submitted,
                'attachments': note.get('attachments', [])
            })
            last_note_dates[issue['id']] = note_date_submitted

    if new_notes:
        # Read existing content of the file
        existing_content = ""
        if os.path.exists(notes_filename):
            with open(notes_filename, 'r', encoding='utf-8') as notes_file:
                existing_content = notes_file.read()

        # Prepend new notes to existing content
        with open(notes_filename, 'w', encoding='utf-8') as notes_file:  # Open file in write mode
            for note in reversed(new_notes):  # Reverse to maintain order from top to bottom
                note_text = (
                    f"- {note['reporter']} ({note['reporter_email']}) ({note['date_submitted']}): {note['text']}\n"
                )
                print(note_text.strip())
                notes_file.write(note_text)

                # Process attachments if they exist
                if note['attachments']:
                    for attachment_id in note['attachments']:
                        results = fetch_attachments(attachment_id['id'], issue['id'], note.get('bugnote_id'))
                        if isinstance(results, list):
                            for result in results:
                                print(result.strip())
                        else:
                            print(results.strip())

            notes_file.write(existing_content)

        if not initial_run:
            # Send new notes to MSMQ only after the initial run
            for note in new_notes:
                note_date_submitted = to_timezone_aware(note['date_submitted'], IST)

                # Fetch assigned user details if available
                assignee_email = 'Unassigned'
                if 'handler' in detailed_issue and detailed_issue['handler']:
                    assignee_email = detailed_issue['handler'].get('email', 'N/A')

                # Create MSMQ message label
                project_name = detailed_issue['project']['name']
                label = f"{project_name} - Issue #{issue['id']} - {issue['summary']} - Priority: {issue['priority']['name']} - Severity: {issue['severity']['name']} - Resolution: {issue['resolution']['name']}"

                # Create MSMQ message body
                body = (
                    f"A new work note added in the ticket #{issue['id']} at {note_date_submitted}\n\n"
                    f"Work note (new): {note['text']}\n"
                    f"Work note added by: {note['reporter']} ({note['reporter_email']})\n"
                    f"Issue assigned to: {assignee_email}\n"
                )

                msmq_client.send_message(label, body)


# Main script execution starts here
if __name__ == "__main__":
    mantis_client = MantisBTApiClient()
    msmq_client = MSMQSender(queue_path)

    initial_run = True
    script_start_time = datetime.now(pytz.UTC).astimezone(IST)

    while True:
        delete_temp_file()
        process_updates(initial_run, script_start_time, mantis_client, msmq_client)
        initial_run = False  # Set to False after the first run

        # Wait for some time before checking again (e.g., every minute)
        time.sleep(60)