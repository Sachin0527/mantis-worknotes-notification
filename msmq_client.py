import win32com.client
from abc import ABC, abstractmethod

class MSMQClient(ABC):
    @abstractmethod
    def send_message(self, label, body):
        pass


class MSMQSender(MSMQClient):
    def __init__(self, queue_path):
        self.queue_path = queue_path

    def send_message(self, label, body):
        try:
            msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
            msmq_info.FormatName = f"DIRECT=OS:{self.queue_path}"
            queue = msmq_info.Open(2, 0)  # Open the queue with send access
            msg = win32com.client.Dispatch("MSMQ.MSMQMessage")
            msg.Body = body
            msg.Label = label
            msg.Send(queue)
            queue.Close()
        except Exception as e:
            print(f"Error sending message to MSMQ: {e}")