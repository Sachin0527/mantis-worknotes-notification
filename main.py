# Configure logging
import json
from mantis_client import MantisClient
from msmq_client import MSMQClient


def get_data_from_mantis_api(config_file):
    mantis_client = MantisClient(config_file)
    return mantis_client.fetch_recently_updated_issues()


def send_msg_to_queue(label, body):
    msmq_client = MSMQClient('config.yaml')
    msmq_client.send_message(label, body)


# Main script execution starts here
if __name__ == "__main__":
    config_file = 'config.yaml'
    issues, notes = get_data_from_mantis_api(config_file)
    for issue in issues:
        label = "Issue Id - " + str(issue['Issue Id']) + " :: " + issue['Issue Description']
        body = json.dumps(issue, indent=4)
        send_msg_to_queue(label, body)

    for note in notes:
        label = "Issue Id - " + str(note['Issue Id']) + " :: " + note['Issue Description'] + " :: " + note[
            'Work Note Text']
        body = json.dumps(note, indent=4)
        send_msg_to_queue(label, body)
