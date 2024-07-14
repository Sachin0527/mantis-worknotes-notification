import os, json
from src.config.config import read_config
from src.utils.logger import CustomLogger
from src.handlers.msmq_handler import MSMQClient
from src.handlers.mantis_handler import MantisClient

_config_file = os.path.abspath('src/config/config.yaml')


class MantisWorkNotesNotification:
    def __init__(self):
        self.__msmq_client = None
        self.__msmq_config = None
        self.__config_file = _config_file
        self.__custom_logger = CustomLogger(self.__config_file).get_logger()

    def mantis_worknotes_notification(self):
        try:
            self.__custom_logger.info("Mantis work-notes notification process started")
            issues, notes = self.__get_data_from_mantis_api()
            msg = self.__send_data_to_queue(issues, notes)
            self.__custom_logger.info("Mantis work-notes notification process ended")
            return msg
        except Exception as e:
            msg = f"Mantis work-notes notification process failed : {e}"
            self.__custom_logger.error(msg)
            raise Exception(e)

    def __get_data_from_mantis_api(self):
        try:
            self.__custom_logger.info("Fetching data from Mantis started")
            config = read_config(self.__config_file)
            mantis_client = MantisClient(config)
            issues, notes = mantis_client.fetch_recently_updated_issues(120)
            self.__custom_logger.info("Fetching data from Mantis completed")
            return issues, notes
        except Exception as e:
            msg = f"Error fetching data from Mantis API: {e}"
            self.__custom_logger.error(msg)
            raise Exception(e)

    def __send_data_to_queue(self, issues, notes):
        try:
            self.__custom_logger.info("Sending data to MSMQ started")
            self.__msmq_config = read_config(self.__config_file, 'msmq')
            self.__msmq_client = MSMQClient(self.__msmq_config)
            if issues or notes:
                if issues:
                    self.__send_issues_to_queue(issues)
                if notes:
                    self.__send_notes_to_queue(notes)
                self.__custom_logger.info("Sending data to MSMQ ended")
                return "Data Successfully sent to queue"
            else:
                msg = "No Data available to be sent to queue"
                self.__custom_logger.info("Sending data to MSMQ ended - No Data available to be sent to queue")
                return msg
        except Exception as e:
            msg = f"Error sending data from MSMQ: {e}"
            self.__custom_logger.error(msg)
            raise Exception(e)

    def __send_issues_to_queue(self, issues_data):
        for issue in issues_data:
            label = f"Issue Id - {issue['Issue Id']} :: {issue['Issue Description']}"
            body = json.dumps(issue, indent=4)
            self.__msmq_client.send_message(label, body)
            self.__custom_logger.info(f"Sent issue to queue: {label}")

    def __send_notes_to_queue(self, notes_data):
        for note in notes_data:
            label = f"Issue Id - {note['Issue Id']} :: {note['Issue Description']} :: {note['Work Note Text']}"
            body = json.dumps(note, indent=4)
            self.__msmq_client.send_message(label, body)
            self.__custom_logger.info(f"Sent issue to queue: {label}")
