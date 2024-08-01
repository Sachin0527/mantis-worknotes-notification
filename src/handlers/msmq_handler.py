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

    # Method to receive a message from the queue.
    def receive_message(self):
        try:
            msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
            msmq_info.FormatName = f"DIRECT=OS:{self.__mantis_config.queue}"
            queue = msmq_info.Open(1, 0)  # Open the queue with receive access
            msg = queue.Receive()
            label = msg.Label
            body = msg.Body
            queue.Close()
            return label, body
        except Exception as e:
            msg = f"Error receiving message from MSMQ: {e}"
            raise Exception(msg)

    # Method to delete a message from the queue based on its label.
    def delete_message(self, label):
        try:
            msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
            msmq_info.FormatName = f"DIRECT=OS:{self.__mantis_config.queue}"
            queue = msmq_info.Open(1, 0)  # Open the queue with receive access

            while True:
                # Peek at the first message in the queue
                msg = queue.Peek(0)
                if msg is None:
                    break

                # Check if this is the message to delete
                if msg.Label == label:
                    # If found, receive (and thus delete) the message
                    queue.Receive(0)
                    break

            queue.Close()
        except Exception as e:
            msg = f"Error deleting message from MSMQ: {e}"
            raise Exception(msg)