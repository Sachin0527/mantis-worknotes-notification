import win32com.client


class MSMQClient:
    def __init__(self, config):
        self.__queue_path = config['queue']

    def send_message(self, label, body):
        try:
            msmq_info = win32com.client.Dispatch("MSMQ.MSMQQueueInfo")
            msmq_info.FormatName = f"DIRECT=OS:{self.__queue_path}"
            queue = msmq_info.Open(2, 0)  # Open the queue with send access
            msg = win32com.client.Dispatch("MSMQ.MSMQMessage")
            msg.Body = body
            msg.Label = label
            msg.Send(queue)
            queue.Close()
            print(f"Message '{label}' sent successfully to queue.")
        except Exception as e:
            print(f"Error sending message to MSMQ: {e}")
