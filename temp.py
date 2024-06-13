import suds
from suds.client import Client
import time
from datetime import datetime
import pytz
import os

# Configuration
mantis_base_url = 'http://localhost:8086/mantisbt'
username = 'administrator'
password = 'root'

#Timezone configuration
IST=pytz.timezone('Asia/Kolkata')

# SOAP WSDL URL
wsdl_url = f"{mantis_base_url}/api/soap/mantisconnect.php?wsdl"

#Dictionary to keep track of the last note date for each issue
last_note_dates={}

# Function to fetch ticket updates
def fetch_ticket_updates():
    try:
        client = Client(wsdl_url)
        issues = client.service.mc_project_get_issues(username, password, 0, 1, 50)  # Project ID 0 (all projects), page 1, per page 50
        #print(issues)
        return issues
    except suds.WebFault as e:
        print(f"Error: Failed to fetch ticket updates: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None



#fuction to cfetch details issue information
def fetch_issue_details(issue_id):
    try:
        client = Client(wsdl_url)
        issue = client.service.mc_issue_get(username, password,issue_id)
        return issue
    except Exception as e:
        print(f"Error: failed to fetch issue details for issue #{issue_id}: {e}")
        return None


def to_timezone_aware(dt,tzinfo):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzinfo)
    return dt.astimezone(tzinfo)

def extract_work_notes(issue_details):
    work_notes = []
    # Assuming issue_details is a dictionary containing issue details including work notes
    if 'work_notes' in issue_details:
        for note in issue_details['work_notes']:
            work_note = {
                'timestamp': note['timestamp'],  # Assuming timestamp is a key in the work note dictionary
                'author': note['author'],        # Assuming author is a key in the work note dictionary
                'text': note['text']             # Assuming text is a key in the work note dictionary
            }
            work_notes.append(work_note)
    return work_notes


def check_for_new_work_notes(last_check_timestamp):
    issues = fetch_ticket_updates()

    for issue in issues:
        work_notes = extract_work_notes(issue)
        for note in work_notes:
            note_timestamp = note['timestamp']  # Assuming you have a timestamp for each work note
            if note_timestamp > last_check_timestamp:
                # Process the new work note
                print("New work note found:", note)

    # Update the last check timestamp to the current time
    return time.time()


# Sample usage
last_check_timestamp = time.time()  # Initialize with current time
while True:
    last_check_timestamp = check_for_new_work_notes(last_check_timestamp)
    time.sleep(60)  # Wait for 60 seconds before checking again
