import requests
import json
from abc import ABC, abstractmethod

# Read the JSON file
with open('config.json', 'r') as file:
    config = json.load(file)

# Configuration
mantis_base_url = ['mantis_base_url']
api_token = config['api_token']# Replace with your API token

# Headers for REST API requests
headers = {
    'Authorization': f'{api_token}',
    'Content-Type': 'application/json'
}



class MantisBTClient(ABC):
    @abstractmethod
    def fetch_ticket_updates(self):
        pass

    @abstractmethod
    def fetch_issue_details(self, issue_id):
        pass


class MantisBTApiClient(MantisBTClient):
    def fetch_ticket_updates(self):
        try:
            response = requests.get(f"{mantis_base_url}/api/rest/issues?project_id=0&page_size=50&page=1", headers=headers)
            response.raise_for_status()
            return response.json()['issues']
        except requests.RequestException as e:
            print(f"Error: Failed to fetch ticket updates: {e}")
            print(f"Response status code: {e.response.status_code if e.response else 'No response'}")
            print(f"Response content: {e.response.content if e.response else 'No content'}")
            return None

    def fetch_issue_details(self, issue_id):
        try:
            response = requests.get(f"{mantis_base_url}/api/rest/issues/{issue_id}", headers=headers)
            response.raise_for_status()
            return response.json()['issues'][0]
        except requests.RequestException as e:
            print(f"Error: failed to fetch issue details for issue #{issue_id}: {e}")
            print(f"Response status code: {e.response.status_code if e.response else 'No response'}")
            print(f"Response content: {e.response.content if e.response else 'No content'}")
            return None
