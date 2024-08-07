import os, json
from src.config.config import read_config
from src.utils.logger import CustomLogger
from src.handlers.msmq_handler import MsmqHandler
from src.handlers.mantis_handler import MantisHandler
from src.handlers.smtp_handler import SmtpHandler


_config_file = os.path.abspath('src/config/config.yaml')


class MantisWorkNotesNotification:
    def __init__(self, time_window=60):
        self.__time_window = time_window
        self.__msmq_client = None
        self.__config_file = _config_file
        self.__config = read_config(self.__config_file)
        self.__custom_logger = CustomLogger(self.__config_file).get_logger()

    # Main method of class to start the process.
    def mantis_worknotes_notification(self):
        try:
            msg=''
            self.__custom_logger.info("Mantis work-notes notification process started")
            issues, notes = self.__get_data_from_mantis_api()
            if issues or notes:
                msg = self.__send_data_to_queue(issues, notes)
                self.__send_email()
            self.__custom_logger.info("Mantis work-notes notification process ended")
            return msg
        except Exception as e:
            msg = f"Mantis work-notes notification process failed : {e}"
            self.__custom_logger.error(msg)
            raise Exception(msg)

    # Method to load mantis config and
    # invoke Mantis API call using Mantis handler to fetch updated issues in given time window
    def __get_data_from_mantis_api(self):
        try:
            self.__custom_logger.info("Fetching data from Mantis started")
            mantis_client = MantisHandler(self.__config)
            issues, notes = mantis_client.fetch_recently_updated_issues(self.__time_window)
            self.__custom_logger.info("Fetching data from Mantis completed")
            return issues, notes
        except Exception as e:
            msg = f"Error fetching data from Mantis API: {e}"
            self.__custom_logger.error(msg)
            raise Exception(msg)

    # Method to load MSMQ config and send data to MSMQ using MSMQ handler
    def __send_data_to_queue(self, issues, notes):
        try:
            self.__custom_logger.info("Sending data to MSMQ started")
            self.__msmq_client = MsmqHandler(self.__config['msmq'])
            if issues or notes:
                if issues:
                    self.__send_issues_to_queue(issues)
                if notes:
                    self.__send_notes_to_queue(notes)
                self.__custom_logger.info("Sending data to MSMQ ended - Data Successfully sent to queue")
                return "Data Successfully sent to queue"
            else:
                msg = "No Data available to be sent to queue"
                self.__custom_logger.info("Sending data to MSMQ ended - No Data available to be sent to queue")
                return msg
        except Exception as e:
            msg = f"Error sending data to MSMQ: {e}"
            self.__custom_logger.error(msg)
            raise Exception(msg)

    # Method to send updated issue to the queue
    def __send_issues_to_queue(self, issues_data):
        for issue in issues_data:
            label = self.__config['issue_label_formatter'].format(**issue)
            body = json.dumps(issue, indent=4)
            self.__msmq_client.send_message(label, body)
            self.__custom_logger.info(f"Sent issue to queue: {label}")

    # Method to send updated work notes to the queue
    def __send_notes_to_queue(self, notes_data):
        for note in notes_data:
            label = self.__config['note_label_formatter'].format(**note)
            body = json.dumps(note, indent=4)
            self.__msmq_client.send_message(label, body)
            self.__custom_logger.info(f"Sent work note to queue: {label}")

    def __send_email(self):
        try:
            self.__custom_logger.info("MSMQ messages email trigger process started")
            while True:
                # Try to receive a message from the queue
                message = self.__msmq_client.receive_message()
                if message is not None:
                    subject, body = message
                    # Send email to the default recipient
                    smtp_client = SmtpHandler(self.__config['smtp'])
                    smtp_client.send_email(subject,body)
                else:
                    break
                # Delete the message from the queue after it's sent
                # msmq_handler.delete_message(subject)
            self.__custom_logger.info("MSMQ messages email trigger process ended")
        except Exception as e:
            msg = f"MSMQ messages email trigger process failed: {e}"
            self.__custom_logger.error(msg)
            raise Exception(msg)
