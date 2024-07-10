import pytz
import requests
from datetime import datetime, timedelta, timezone
from common import read_config
from attachment_handler import AttachmentHandler


def is_recently_updated(issue, timestamp_from):
    try:
        # Parse issue's last updated timestamp
        last_updated = issue["updated_at"]
        last_updated = datetime.fromisoformat(last_updated)
        last_updated = datetime.strftime(last_updated, "%Y-%m-%d %H:%M:%S")
        # Check if the issue was updated after timestamp_from
        return last_updated > timestamp_from

    except Exception as e:
        print(f"Failed to parse issue last updated time: {e}")
        return False


def extract_fields(data, fields_to_extract, prefix):
    issue_data = {}
    for field in fields_to_extract:
        if '.' in field:
            field_name = field.split('.')[0]
            nested_field = field.split('.')[1]
            value = data.get(field_name, {}).get(nested_field)
            # Replace 'handler' with 'assignee'
            if 'handler' in field:
                field = field.replace('handler', 'assignee')
                issue_data[prefix + field.capitalize()] = value
            elif 'reporter' in field:
                issue_data[prefix + field.capitalize()] = value
            else:
                issue_data[prefix + field_name.capitalize()] = value
        else:
            value = data.get(field)
            issue_data[prefix + field.capitalize()] = value
    return issue_data


class MantisClient():
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = read_config(config_file, 'mantis')
        self.base_url = self.config['base_url']
        self.api_token = self.config['api_token']
        self.project_id = self.config['project_id']
        self.time_zone = self.config['time_zone']
        self.issue_fields = [field.strip() for field in self.config['issue_fields'].split(',')]
        self.work_notes_fields = [field.strip() for field in self.config['work_notes_fields'].split(',')]

    def setup_header(self):
        # Headers for REST API requests
        headers = {
            'Authorization': f'{self.api_token}',
            'Content-Type': 'application/json'
        }
        return headers

    def get_attachment_details(self, bug_id, bug_note_id=None):
        attachment_handler = AttachmentHandler(self.config_file)
        return attachment_handler.fetch_attachments(bug_id, bug_note_id)

    def fetch_all_issues(self):
        try:
            all_issues = []
            page = 1
            while True:
                issues_on_current_page = self.api_call(page)
                if not issues_on_current_page:
                    break
                all_issues.extend(issues_on_current_page)
                page += 1
            return all_issues
        except requests.RequestException as e:
            print(e)

    def api_call(self, page):
        try:
            url = f"{self.base_url}/api/rest/issues"
            params = {
                "project_id": self.project_id,
                "page_size": 50,
                "page": page
            }
            headers = self.setup_header()
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()['issues']
        except requests.exceptions.RequestException as e:
            print(e)

    def fetch_recently_updated_issues(self, minutes=240):
        try:
            # Fetch all issues
            all_issues = self.fetch_all_issues()
            current_utc_time = datetime.now(timezone.utc)
            target_timezone = pytz.timezone(self.time_zone)
            local_datetime = current_utc_time.astimezone(target_timezone)
            timestamp_from = local_datetime - timedelta(minutes=minutes)
            timestamp_from = datetime.strftime(timestamp_from, "%Y-%m-%d %H:%M:%S")
            # Filter issues updated within the last 1 minute
            updated_issues = []
            updated_notes = []
            for issue in all_issues:
                if is_recently_updated(issue, timestamp_from):
                    issue_data = extract_fields(issue, self.issue_fields, "Issue ")
                    temp_attachments = self.get_attachment_details(issue['id'])
                    if temp_attachments:
                        issue_data['Issue Attachments Path'] = temp_attachments
                    updated_issues.append(issue_data)
                    # Also fetch and process notes for this issue
                    notes = issue.get('notes', [])
                    for note in notes:
                        if is_recently_updated(note, timestamp_from):
                            note_data = extract_fields(note, self.work_notes_fields, "Work Note ")
                            note_data.update(issue_data)
                            del note_data['Issue Attachments Path']
                            temp_attachments = self.get_attachment_details(issue['id'],note['id'])
                            if temp_attachments:
                                note_data['Work Note Attachments Path'] = temp_attachments
                            updated_notes.append(note_data)
            return updated_issues, updated_notes
        except Exception as e:
            print(e.with_traceback())
            print(f"Failed to fetch recently updated issues: {e}")
            return []

    def extract_updated_entities(self, updated_issues, one_minute_ago):
        try:
            updated_work_notes = []
            updated_issues_list = []

            for issue in updated_issues:
                if 'updated_at' in issue or 'created_at' in issue:
                    updated_issues_list.append(issue)

                if 'notes' in issue:
                    for note in issue['notes']:
                        last_updated = note.get('updated_at', note.get('created_at'))
                        if last_updated and is_recently_updated({"updated_at": last_updated}, one_minute_ago):
                            updated_work_notes.append(note)

            return updated_issues_list, updated_work_notes
        except Exception as e:
            print(f"Failed to extract updated entities: {e}")
            return [], []
