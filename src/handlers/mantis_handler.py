import pytz, requests
from datetime import datetime, timedelta, timezone

from src.config.config import MantisConfig
from src.handlers.attachment_handler import AttachmentHandler


def get_timestamp_from(time_zone, minutes):
    current_utc_time = datetime.now(timezone.utc)
    target_timezone = pytz.timezone(time_zone)
    local_datetime = current_utc_time.astimezone(target_timezone)
    timestamp_from = local_datetime - timedelta(minutes=minutes)
    timestamp_from = datetime.strftime(timestamp_from, "%Y-%m-%d %H:%M:%S")
    return timestamp_from


def is_recently_updated(issue, timestamp_from):
    try:
        # Parse issue's last updated timestamp
        last_updated = issue["updated_at"]
        last_updated = datetime.fromisoformat(last_updated)
        last_updated = datetime.strftime(last_updated, "%Y-%m-%d %H:%M:%S")
        # Check if the issue was updated after timestamp_from
        return last_updated > timestamp_from
    except Exception as e:
        msg = f"Failed to parse issue last updated time: {e}"
        raise Exception(msg)


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


class MantisClient:
    def __init__(self, config):
        self.__mantis_config = MantisConfig(config['mantis'])
        self.__mysql_config = config['mysql']
        self.__attachment_base_dir = config['attachment_base_dir']

    def __setup_header(self):
        # Headers for REST API requests
        headers = {
            'Authorization': f'{self.__mantis_config.api_token}',
            'Content-Type': 'application/json'
        }
        return headers

    def __get_attachment_details(self, bug_id, bug_note_id=None):
        try:
            attachment_handler = AttachmentHandler(self.__mysql_config, self.__attachment_base_dir)
            return attachment_handler.fetch_attachments(bug_id, bug_note_id)
        except Exception as e:
            msg = f"Failed to download the attachments for the ticket/worknotes: {e}"
            raise Exception(msg)

    def __fetch_all_issues(self):
        try:
            all_issues = []
            page = 1
            while True:
                issues_on_current_page = self.__api_call(page)
                if not issues_on_current_page:
                    break
                all_issues.extend(issues_on_current_page)
                page += 1
            return all_issues
        except requests.RequestException as e:
            msg = f"Failed in Mantis API Call: {e}"
            raise Exception(msg)

    def __api_call(self, page):
        url = f"{self.__mantis_config.base_url}/api/rest/issues"
        params = {
            "project_id": self.__mantis_config.project_id,
            "page_size": 50,
            "page": page,
            "filter_id": self.__mantis_config.filter_id
        }
        response = requests.get(url, headers=self.__setup_header(), params=params)
        response.raise_for_status()
        return response.json()['issues']

    def __fetch_updated_since_timestamp_from(self, issues, timestamp_from):
        updated_issues = []
        updated_notes = []
        for issue in issues:
            if is_recently_updated(issue, timestamp_from):
                issue_data = extract_fields(issue, self.__mantis_config.issue_fields, "Issue ")
                temp_attachments = self.__get_attachment_details(issue['id'])
                if temp_attachments:
                    issue_data['Issue Attachments Path'] = temp_attachments
                updated_issues.append(issue_data)
                # Also fetch and process notes for this issue
                notes = issue.get('notes', [])
                for note in notes:
                    if is_recently_updated(note, timestamp_from):
                        note_data = extract_fields(note, self.__mantis_config.work_notes_fields, "Work Note ")
                        note_data.update(issue_data)
                        temp_attachments = self.__get_attachment_details(issue['id'], note['id'])
                        if temp_attachments:
                            note_data['Work Note Attachments Path'] = temp_attachments
                        updated_notes.append(note_data)
        return updated_issues, updated_notes

    def fetch_recently_updated_issues(self, minutes=1):
        try:
            # Fetch all issues
            all_issues = self.__fetch_all_issues()
            timestamp_from = get_timestamp_from(self.__mantis_config.time_zone, minutes)
            # Filter issues updated within the last specified minutes time window
            return self.__fetch_updated_since_timestamp_from(all_issues, timestamp_from)
        except Exception as e:
            msg = f"Failed to fetch recently updated issues: {e}"
            raise Exception(msg)
