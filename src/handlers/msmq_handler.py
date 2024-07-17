import win32com.client

from ..config import MsmqConfig


class MsmqHandler:
    def __init__(self, config):
        self.__mantis_config = MsmqConfig(config)

    # Method to send messages to queue.
    def send_message(self, label, body):
        try:
            msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
            msmq_info.FormatName = f"DIRECT=OS:{self.__mantis_config.queue}"
            queue = msmq_info.Open(2, 0)  # Open the queue with send access
            msg = win32com.client.Dispatch("MSMQ.MSMQMessage")
            msg.Body = body
            msg.Label = label
            msg.Send(queue)
            queue.Close()
        except Exception as e:
            msg = f"Error sending message to MSMQ: {e}"
            raise Exception(msg)
