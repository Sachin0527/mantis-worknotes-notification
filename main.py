import json, logging
from msmq_client import MSMQClient
from mantis_client import MantisClient
from common import read_config

config_file = 'config.yaml'
log_file = read_config(config_file, 'log_file_path')

# Configure logging
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_data_from_mantis_api():
    try:
        mantis_client = MantisClient(config_file)
        return mantis_client.fetch_recently_updated_issues(240)
    except Exception as e:
        logging.error(f"Error fetching data from Mantis API: {e}")
        return [], []  # Return empty lists to avoid errors downstream


def send_issues_to_queue(issues_data):
    try:
        msmq_client = MSMQClient(config_file)
        for issue in issues_data:
            label = f"Issue Id - {issue['Issue Id']} :: {issue['Issue Description']}"
            body = json.dumps(issue, indent=4)
            msmq_client.send_message(label, body)
            logging.info(f"Sent issue to queue: {label}")
    except Exception as e:
        logging.error(f"Error sending issues to queue: {e}")


def send_notes_to_queue(notes_data):
    try:
        msmq_client = MSMQClient(config_file)
        for note in notes_data:
            label = f"Issue Id - {note['Issue Id']} :: {note['Issue Description']} :: {note['Work Note Text']}"
            body = json.dumps(note, indent=4)
            msmq_client.send_message(label, body)
            logging.info(f"Sent note to queue: {label}")
    except Exception as e:
        logging.error(f"Error sending notes to queue: {e}")


# Main script execution starts here
if __name__ == "__main__":
    try:
        issues, notes = get_data_from_mantis_api()
        if issues:
            send_issues_to_queue(issues)
        if notes:
            send_notes_to_queue(notes)
    except Exception as e:
        logging.error(f"Unexpected error occurred during processing : {e}")
