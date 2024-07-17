import pytz, requests
from datetime import datetime, timedelta, timezone

from src.config.config import MantisConfig
from src.handlers.mysql_handler import MysqlHandler


# Method to return time window range for the specified time zone and minutes interval
def get_time_range(time_zone, minutes):
    current_utc_time = datetime.now(timezone.utc)
    target_timezone = pytz.timezone(time_zone)
    local_datetime = current_utc_time.astimezone(target_timezone)
    timestamp_from = local_datetime - timedelta(minutes=minutes)
    timestamp_from = datetime.strftime(timestamp_from, "%Y-%m-%d %H:%M:%S")
    timestamp_to = datetime.strftime(local_datetime, "%Y-%m-%d %H:%M:%S")
    return timestamp_from, timestamp_to


# Method to verify if a given issue or work note is updated after start timestamp value
def is_recently_updated(data, timestamp_from):
    try:
        # Parse issue's last updated timestamp
        last_updated = data["updated_at"]
        last_updated = datetime.fromisoformat(last_updated)
        last_updated = datetime.strftime(last_updated, "%Y-%m-%d %H:%M:%S")
        # Check if the issue was updated after timestamp_from
        return last_updated > timestamp_from
    except Exception as e:
        msg = f"Failed to parse issue last updated time: {e}"
        raise Exception(msg)


# Method to verify if a given issue is a new issue or not
def is_new_issue(created_at, updated_at):
    try:
        formatted_created_at = datetime.fromisoformat(created_at)
        formatted_created_at = datetime.strftime(formatted_created_at, "%Y-%m-%d %H:%M:%S")
        formatted_updated_at = datetime.fromisoformat(updated_at)
        formatted_updated_at = datetime.strftime(formatted_updated_at, "%Y-%m-%d %H:%M:%S")
        return formatted_created_at == formatted_updated_at
    except Exception as e:
        msg = f"Failed to parse create and update date timestamps: {e}"
        raise Exception(msg)


# Method to extract data fields from Mantis issue which are to be pushed to MSMQ.
# Fields to extract are supplied in yaml with comma separation
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


class MantisHandler:
    def __init__(self, config):
        self.__mantis_config = MantisConfig(config['mantis'])
        self.__mysql_handler = MysqlHandler(config['mysql'], config['attachment_base_dir'])

    # Sets up the header for Mantis API call
    def __setup_header(self):
        # Headers for REST API requests
        headers = {
            'Authorization': f'{self.__mantis_config.api_token}',
            'Content-Type': 'application/json'
        }
        return headers

    # Sets up the params to be supplied in Mantis API call
    def __setup_params(self):
        params = {
            "project_id": self.__mantis_config.project_id,
            "page_size": self.__mantis_config.page_size,
        }
        return params

    # Method to download the attachment for the given bug id or bug note id & gets the location of downloaded files
    def __get_attachment_details(self, bug_id, bug_note_id=None):
        try:
            return self.__mysql_handler.fetch_attachments(bug_id, bug_note_id)
        except Exception as e:
            msg = f"Failed to download the attachments for the ticket/worknotes: {e}"
            raise Exception(msg)

    # Method to fetch the updated issues ids from Mantis DB and
    # then fetch issues details for the retrieved issues ids using Mantis API
    def __fetch_updated_issues_between_range(self, issues_ids_list):
        try:
            all_issues = []
            page = 1
            for id in issues_ids_list:
                issues_on_current_page = self.__api_call(f"/api/rest/issues/{id}", page)
                if not issues_on_current_page:
                    break
                all_issues.extend(issues_on_current_page)
                page += 1
            return all_issues
        except requests.RequestException as e:
            msg = f"Failed in Mantis API Call: {e}"
            raise Exception(msg)

    # Mantis API call method
    def __api_call(self, url_suffix, page):
        url = f"{self.__mantis_config.base_url}{url_suffix}"
        headers = self.__setup_header()
        params = self.__setup_params()
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()['issues']

    # Method to filter out only recently updated issues and work notes from the issues based on timestamp from value
    def __fetch_updated_issues_and_worknotes_since_timestamp(self, issues, timestamp_from):
        updated_issues = []
        updated_notes = []
        for issue in issues:
            if is_recently_updated(issue, timestamp_from):
                issue_data = extract_fields(issue, self.__mantis_config.issue_fields, "Issue ")
                if is_new_issue(issue['created_at'], issue['updated_at']) :
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

    # Main Method of the class
    def fetch_recently_updated_issues(self, minutes=1):
        try:
            start_time, end_time = get_time_range(self.__mantis_config.time_zone, minutes)
            updated_issues_ids_list = self.__mysql_handler.get_updated_issues_ids_list(start_time, end_time)
            updated_issues_data = self.__fetch_updated_issues_between_range(updated_issues_ids_list)
            return self.__fetch_updated_issues_and_worknotes_since_timestamp(updated_issues_data, start_time)
        except Exception as e:
            msg = f"Failed to fetch recently updated issues: {e}"
            raise Exception(msg)
