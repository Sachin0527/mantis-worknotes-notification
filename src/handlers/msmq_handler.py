import win32com.client
from ..config import MsmqConfig


class MsmqHandler:
    def __init__(self, config):
        self.__mantis_config = MsmqConfig(config)
        self.__msmq_info = self.__setup_msmq_info()

    def __setup_msmq_info(self):
        msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
        msmq_info.FormatName = f"DIRECT=OS:{self.__mantis_config.queue}"
        return msmq_info

    # Method to send messages to queue.
    def send_message(self, label, body):
        try:
            queue = self.__msmq_info.Open(2, 0)  # Open the queue with send access
            msg = win32com.client.Dispatch("MSMQ.MSMQMessage")
            msg.Body = body
            msg.Label = label
            msg.Send(queue)
            queue.Close()
        except Exception as e:
            msg = f"Error sending message to MSMQ: {e}"
            raise Exception(msg)

    # Method to receive a message from the queue.
    def receive_message(self):
        try:
            queue = self.__msmq_info.Open(1, 0)  # Open the queue with receive access
            msg = queue.PeekCurrent(1, False,1000)
            if msg:
                msg = queue.Receive()
                label = msg.Label
                body = msg.Body
                return label, body
            else:
                queue.Close()
                return None
        except Exception as e:
            if "Timeout" in str(e):
                return None, None  # No messages in the queue
            else:
                msg = f"Error receiving message from MSMQ: {e}"
                raise Exception(msg)
