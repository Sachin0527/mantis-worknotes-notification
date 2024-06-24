from datetime import datetime
import pytz

from mantis_client import MantisBTApiClient

# Timezone configuration
IST = pytz.timezone('Asia/Kolkata')

def check_for_updates(mantis_client):
    issues = mantis_client.fetch_ticket_updates()
    if issues:
        return issues
    return None


def fetch_issue_details(mantis_client, issue_id):
    detailed_issue = mantis_client.fetch_issue_details(issue_id)
    return detailed_issue if detailed_issue and 'notes' in detailed_issue else None